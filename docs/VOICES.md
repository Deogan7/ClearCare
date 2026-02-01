# Voice System — RidgeCare Link

## Overview

RidgeCare Link uses **AI-powered phone calls** to automate the closed-loop referral workflow. Instead of nurses manually calling specialist offices and patients, the system places outbound calls using a conversational AI agent named **Sarah**.

Sarah sounds like a real person — friendly, patient, and natural. She handles the full referral lifecycle through phone calls: confirming specialists received documents, checking on appointments, notifying patients, following up after visits, and rescheduling when needed.

### Tech Stack

| Component       | Service       | Purpose                                          |
|-----------------|---------------|--------------------------------------------------|
| Voice AI        | **Vapi AI**   | Conversational AI engine — handles the phone call dialogue |
| Language Model  | **GPT-4o**    | Powers Sarah's natural conversation ability       |
| Voice Synthesis | **ElevenLabs**| "Rachel" voice — warm, natural-sounding female voice |
| Telephony       | **Twilio**    | Routes the actual phone calls (imported into Vapi)|
| Webhooks        | **ngrok**     | Exposes local server for Vapi callback events     |

---

## Architecture

```
┌─────────────┐     POST /call      ┌──────────┐     Twilio SIP     ┌──────────────┐
│  FastAPI     │ ──────────────────► │  Vapi AI │ ────────────────►  │  Phone Call   │
│  Backend     │                     │  Engine  │                    │  (Recipient)  │
└─────────────┘                     └──────────┘                    └──────────────┘
       ▲                                  │
       │         POST /webhook            │
       └──────────────────────────────────┘
              (end-of-call-report)
```

1. **Backend triggers a call** — sends a POST to `https://api.vapi.ai/call` with an inline assistant config (system prompt, voice, first message, metadata).
2. **Vapi places the call** — uses the Twilio phone number imported into Vapi to dial the recipient.
3. **AI conversation happens** — GPT-4o drives the dialogue using the system prompt. ElevenLabs generates the voice audio in real time.
4. **Call ends** — Vapi sends an `end-of-call-report` webhook back to the backend with the full transcript and metadata.
5. **Backend processes the result** — keyword-based NLP analyzes the transcript and transitions the referral to the appropriate next status.

---

## The 6 Call Types

Each call type maps to a step in the referral workflow. Sarah has a different personality and goal for each one.

### 1. Specialist Verification (`specialist_verify_receipt`)

**Who gets called:** Specialist office
**Goal:** Confirm they received the referral documents.
**Trigger status:** `SENT_TO_SPECIALIST` or `RESENT_TO_SPECIALIST`

Sarah calls the specialist office and asks if they received the referral for the patient. She references the ticket number and patient name — nothing clinical.

| Outcome    | Next Status              | Follow-up                    |
|------------|--------------------------|------------------------------|
| Yes        | `REFERRAL_RECEIVED`      | Check appointment in 48 hrs  |
| No         | `RESENT_TO_SPECIALIST`   | Retry in 5 business days     |
| Unclear    | *(no change)*            | Retry in 24 hrs              |

### 2. Appointment Check (`specialist_appointment_check`)

**Who gets called:** Specialist office
**Goal:** Find out if they've scheduled an appointment for the patient.
**Trigger status:** `REFERRAL_RECEIVED` or `APPOINTMENT_SCHEDULING`

Sarah asks if an appointment has been booked. If yes, she asks for the date and whether it's in-person or virtual.

| Outcome         | Next Status              | Details                         |
|-----------------|--------------------------|----------------------------------|
| Scheduled       | `APPOINTMENT_SCHEDULED`  | Records in-person vs. virtual    |
| Not yet         | `APPOINTMENT_SCHEDULING` | Follow up in 2 business days     |

### 3. Patient Notification (`patient_appointment_notify`)

**Who gets called:** Patient
**Goal:** Let the patient know their appointment is scheduled.
**Trigger status:** `APPOINTMENT_SCHEDULED`

Sarah calls with good news. She shares the specialist name and date, then:
- **In-person:** Asks if they need a ride or transportation help.
- **Virtual:** Lets them know they'll receive connection details.

| Outcome           | Next Status        | Details                     |
|-------------------|--------------------|-----------------------------|
| Call completed    | `PATIENT_NOTIFIED` | Records ride preference      |

### 4. Post-Appointment Follow-Up (`patient_post_appointment`)

**Who gets called:** Patient
**Goal:** Check if they attended the specialist appointment.
**Trigger status:** `PATIENT_NOTIFIED`

Sarah checks in after the appointment date. She's warm and non-judgmental either way.

| Outcome    | Next Status              | Details                     |
|------------|--------------------------|------------------------------|
| Attended   | `COMPLETED` → `CLOSED`  | Referral loop closed         |
| Missed     | `MISSED`                 | Triggers reschedule call     |
| Unclear    | *(no change)*            | Logged for manual review     |

### 5. Missed Appointment Reschedule (`patient_missed_reschedule`)

**Who gets called:** Patient
**Goal:** Ask if they'd like to reschedule.
**Trigger status:** `MISSED`

Sarah is empathetic and zero-pressure. She understands life happens.

| Outcome         | Next Status               | Details                          |
|-----------------|---------------------------|-----------------------------------|
| Yes, reschedule | `RESCHEDULE_REQUESTED` → `SENT_TO_SPECIALIST` | Restarts the workflow  |
| No              | `CLOSED`                  | Suggests local doctor follow-up   |

### 6. Storm Reschedule (`storm_reschedule`)

**Who gets called:** Patient
**Goal:** Suggest switching an in-person appointment to virtual due to severe weather.
**Trigger:** Weather poller detects severe conditions (15cm+ snow or -35C+)

Sarah expresses genuine concern for their safety and offers the virtual option.

| Outcome    | Result                    | Details                     |
|------------|---------------------------|------------------------------|
| Accepts    | Appointment → `VIRTUAL`   | Details sent via SMS         |
| Declines   | *(no change)*             | Respects their choice        |

---

## Sarah — The AI Voice Agent

Sarah is not a script reader. She's designed to sound like a real person making a work call.

### Personality Traits
- **Friendly and professional** — like a real referral coordinator
- **Patient** — never rushes, especially with elderly callers
- **Natural** — uses filler words ("um", "so"), laughs when appropriate
- **Honest about being AI** — if asked, she says: *"I am actually an AI assistant, but I'm calling on behalf of the referral coordination team at Clearwater Ridge."*
- **Empathetic** — especially for missed appointments and health concerns

### Conversation Abilities
- Handles being put on hold: *"Sure, take your time."*
- Repeats information when asked (rephrases naturally, doesn't just repeat verbatim)
- Responds to small talk gracefully
- Uses natural transitions: *"So the reason I'm calling is..."*
- Never discusses clinical/medical details beyond what's needed

### Technical Config

```python
{
    "model": {
        "provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.7,        # Varied, natural responses
    },
    "voice": {
        "provider": "11labs",
        "voiceId": "21m00Tcm4TlvDq8ikWAM",  # Rachel — warm, natural
    },
    "silenceTimeoutSeconds": 30,    # Won't hang up during pauses
    "responseDelaySeconds": 0.5,    # Natural pause before responding
    "backchannelingEnabled": True,  # Says "mm-hmm", "right" while listening
    "backgroundDenoisingEnabled": True,  # Cleaner audio
}
```

---

## Webhook Processing

When a call ends, Vapi sends an `end-of-call-report` to `POST /api/voice/webhook`. The backend:

1. **Extracts metadata** — `ticket_id` and `call_type` from the call payload.
2. **Analyzes the transcript** — keyword-based NLP scans for expected responses.
3. **Transitions the referral** — updates the status in the database based on the analysis.
4. **Appends a timestamped note** — logs what happened to the referral's notes field.

### Keyword Analysis

Each call type has its own analyzer function that scans the transcript for keyword sets:

| Keyword Set         | Example Keywords                                        |
|---------------------|---------------------------------------------------------|
| Yes (receipt)       | "received", "confirmed", "yes we have", "got it"       |
| No (receipt)        | "haven't received", "don't have", "not yet"            |
| Scheduled           | "scheduled", "booked", "appointment is set"             |
| In-person           | "in person", "come in", "at the office"                |
| Virtual             | "virtual", "telehealth", "video call"                  |
| Attended            | "i went", "i was there", "yes i did"                   |
| Missed              | "missed", "couldn't make it", "didn't attend"          |
| Wants reschedule    | "reschedule", "new appointment", "yes please reschedule"|
| Needs ride          | "need a ride", "transportation", "yes please"          |

---

## API Endpoints

All endpoints are under `/api/voice/` and require JWT authentication (except the webhook).

### Demo Endpoint

```
POST /api/voice/demo/{ticket_id}
```

For live demonstrations. Both calls go to your phone so you can play both roles (specialist and patient).

**Body:**
```json
{
    "phone": "+16043411001",
    "step": 1
}
```

| Step | You play the role of | Sarah asks                             | On success               |
|------|---------------------|----------------------------------------|--------------------------|
| 1    | Specialist office   | "Did you receive the referral?"        | Status → REFERRAL_RECEIVED |
| 2    | Patient             | "Did you attend the appointment?"      | Status → COMPLETED → CLOSED |

### Production Endpoints

```
POST /api/voice/verify-referral/{ticket_id}
```
Manually trigger a specialist verification call. Requires `admin_phone` in the body.

```
POST /api/voice/trigger-workflow-call/{ticket_id}
```
Automatically triggers the **next appropriate call** based on the referral's current status. The backend figures out which call type to use.

```
POST /api/voice/patient-checkin/{patient_id}
```
Trigger a follow-up call to a patient about their most urgent active referral.

### Webhook

```
POST /api/voice/webhook
```
Receives `end-of-call-report` events from Vapi. No authentication — Vapi calls this directly.

---

## Referral Status Flow

The voice system drives referrals through these 10 states:

```
SENT_TO_SPECIALIST
        │
        ├── specialist confirms receipt
        ▼
REFERRAL_RECEIVED ──► APPOINTMENT_SCHEDULING
        │                     │
        │    specialist books appointment
        ▼                     │
APPOINTMENT_SCHEDULED ◄───────┘
        │
        ├── patient notified
        ▼
PATIENT_NOTIFIED
        │
        ├── after appointment date
        ▼
   ┌─────────┐
   │ Attended │──► COMPLETED ──► CLOSED
   └─────────┘
   ┌─────────┐
   │ Missed  │──► MISSED
   └─────────┘        │
                      ├── wants reschedule
                      ▼
              RESCHEDULE_REQUESTED ──► SENT_TO_SPECIALIST (restart)
                      │
                      ├── declines
                      ▼
                    CLOSED

Special: RESENT_TO_SPECIALIST (if specialist didn't receive documents)
Special: Storm Mode can convert IN_PERSON → VIRTUAL at any point
```

---

## SMS Integration

The voice system works alongside SMS (Twilio) for supplementary communication:

- **Storm check-in SMS** — sent to high-risk patients during severe weather
- **Appointment reminders** — text reminders before scheduled appointments
- **Virtual care links** — sent when an appointment is converted to virtual

---

## Running the Demo

### Prerequisites
1. Docker running (`docker compose up --build -d`)
2. ngrok tunneling to port 8000 (`ngrok http 8000`)
3. `.env` has `VAPI_SERVER_URL` set to your ngrok URL + `/api/voice/webhook`

### Step 1 — Specialist Verification
```bash
curl -s -X POST http://localhost:8000/api/voice/demo/RC-SEED01 \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+16043411001", "step": 1}'
```

You'll get a call. Sarah will ask if you (the "specialist") received the referral. Say **"Yes, we received it."** The webhook will transition the referral to `REFERRAL_RECEIVED`.

### Step 2 — Patient Follow-Up
```bash
curl -s -X POST http://localhost:8000/api/voice/demo/RC-SEED01 \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+16043411001", "step": 2}'
```

You'll get another call. Sarah will ask if you (the "patient") attended the appointment. Say **"Yes, I went and it went well."** The webhook will transition the referral to `COMPLETED` then `CLOSED`.

---

## File Map

| File | Purpose |
|------|---------|
| `backend/app/services/voice_service.py` | Vapi API integration, all 6 system prompts, outbound call functions |
| `backend/app/api/routes/voice.py` | API endpoints, webhook handler, transcript NLP analysis |
| `backend/app/schemas/voice.py` | Request/response Pydantic models |
| `backend/app/services/sms_service.py` | Twilio SMS for storm alerts, reminders, virtual care links |
| `backend/app/services/weather_service.py` | OpenWeatherMap polling for storm mode triggers |
| `backend/app/services/referral_service.py` | State machine, status transitions, follow-up scheduling |
| `backend/app/models/referral.py` | Referral model with 10-state workflow |
| `backend/app/core/config.py` | Vapi/Twilio/Weather API keys and settings |
