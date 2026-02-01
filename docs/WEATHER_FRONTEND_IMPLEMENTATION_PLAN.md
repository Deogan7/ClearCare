# Weather Frontend Integration Plan

Goal: Replace the Weather page mock UI with live data from `/api/weather/current` and `/api/weather/storm-status`, add loading/error states, and make the UI resilient to WeatherAPI alert payloads.

## 1) Scope and endpoints

Note: Backend already runs a weather poller every 30 minutes in `backend/app/tasks/__init__.py`. We will keep that cadence.

### Backend endpoints (already available)
- `GET /api/weather/current`
  - `{ temperature_c, snow_cm, description, is_severe, thresholds: { snow_cm, temp_c }, location: { lat, lon } }`
- `GET /api/weather/storm-status`
  - `{ is_severe, temperature_c, snow_cm, description, thresholds: { snow_cm, temp_c }, alerts: [] }`

### Frontend files in scope
- `frontend/src/services/weatherService.ts`
- `frontend/src/pages/WeatherPage.tsx`
- `frontend/src/components/weather/*` (new components)
- `frontend/src/types/weather.ts` (new types)

## 2) Data contracts (frontend types)

Create `frontend/src/types/weather.ts`:
- `WeatherThresholds { snow_cm: number; temp_c: number }`
- `WeatherLocation { lat: number; lon: number }`
- `CurrentWeatherResponse { temperature_c; snow_cm; description; is_severe; thresholds; location }`
- `StormStatusResponse { is_severe; temperature_c; snow_cm; description; thresholds; alerts }`
- `WeatherAlert` should reflect the WeatherAPI alert shape as `Record<string, unknown>` at minimum, then refine the fields used in UI (ex: `headline`, `event`, `severity`, `desc`, `effective`, `expires`).

## 3) Service layer updates

Update `frontend/src/services/weatherService.ts`:
- Add return types and `data` unwrapping for Axios responses.
- Export typed methods:
  - `getCurrentWeather(): Promise<CurrentWeatherResponse>`
  - `getStormStatus(): Promise<StormStatusResponse>`

## 4) UI components (new)

Create `frontend/src/components/weather/`:
- `CurrentWeatherCard.tsx`
  - Displays temperature, snow cm, description, and severity badge.
- `StormStatusCard.tsx`
  - Displays status (severe/clear) and thresholds.
- `WeatherAlertsList.tsx`
  - Renders alert rows (headline, severity, effective/expires); shows empty state when no alerts.
- `WeatherMetaRow.tsx` (optional)
  - Shared compact row for thresholds or location.

## 5) Page wiring and state

Update `frontend/src/pages/WeatherPage.tsx`:
- Fetch both endpoints in parallel (Promise.all) on load.
- Add `loading`, `error`, and `data` state.
- Trigger refetch via the existing "Refresh" button.
- Show:
  - skeletons while loading,
  - `ErrorState` on failures,
  - cards + alerts list when data exists.

## 6) UX details

- If `is_severe` is true, show a strong status badge and an optional warning banner.
- If alerts are missing or empty, show `TableEmptyState` or a small empty card.
- Add a `Last updated` timestamp (local time) next to the refresh button or in the page header.

## 7) Implementation steps

1. Add types in `frontend/src/types/weather.ts`.
2. Update `frontend/src/services/weatherService.ts` to return typed `data`.
3. Build `CurrentWeatherCard`, `StormStatusCard`, `WeatherAlertsList`.
4. Wire `WeatherPage.tsx` with data fetching + refresh.
5. Add loading/error/empty states.

## 8) Acceptance checklist

- Weather page shows real data from both endpoints.
- Refresh button triggers a refetch and updates `Last updated`.
- Severe status is visually distinct.
- Alerts list renders at least headline + severity or empty state.
- Errors show a clear message without breaking layout.

## 9) Risks and notes

- WeatherAPI alert fields are not normalized; guard against missing fields.
- Auth is required for endpoints; make sure token is present or show redirect behavior from `api.ts`.

---

## Storm Mode (Cold Weather Resilience) — Plan Addendum

Scope for now: **Storm Mode only converts upcoming non-urgent physical appointments into Virtual Care**. No SMS check-ins in this phase.

### Behavior
- Manual activation via a "Storm Mode" button (Dashboard + Weather page).
- Automatic activation **auto-converts** when `/api/weather/storm-status` reports severe conditions.
- Conversion window defaults to next 48–72 hours (configurable later).

### Conversion rules
- Appointment type is **in-person**.
- Appointment is **non-urgent**.
- Appointment occurs within the active Storm Mode window.

### UI changes (planned)
- Add a **Storm Mode** button with confirm modal:
  - Shows count of appointments to convert.
  - Displays conversion window (e.g., next 48–72h).
  - Requires confirmation before applying.
- Add a small status indicator showing:
  - Active/Inactive
  - Trigger source (Manual vs Auto)
  - Last activation time

### API additions (planned)
- `POST /api/storm-mode/activate`
  - Body: `{ mode: "manual" | "auto", window_hours: number }`
  - Returns: `{ status, converted_count, window_hours }`
- `POST /api/storm-mode/deactivate`
  - Returns: `{ status }`
- `GET /api/storm-mode/status`
  - Returns: `{ status, mode, activated_at, window_hours }`

### Auto-convert (planned)
- On each severe weather poll (30-minute cadence), trigger auto-convert once per active window.
- Use idempotent checks to avoid re-converting the same appointment.

### Threshold guidance (fallback)
- Use alerts-first for activation when available.
- If no alert is present, a reasonable fallback for Clearwater Ridge is **snow ≥ 15 cm in 24 hours**.
- Treat this as a configurable org setting, not a hard-coded global.

### Data and auditing (planned)
- Log each conversion in an audit table (appointment_id, previous_type, new_type, triggered_by, timestamp).
- Keep a Storm Mode action batch ID for traceability.
