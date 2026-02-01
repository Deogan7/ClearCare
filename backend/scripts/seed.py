"""Seed the database with test patients and referrals for development."""

import asyncio
import uuid
from datetime import datetime, timedelta

from app.db.session import async_session
from app.models.patient import Patient
from app.models.referral import Referral, ReferralStatus, AppointmentType
from app.models.user import User
from app.core.security import hash_password


async def seed():
    async with async_session() as db:
        # -- Patients --
        p1 = Patient(
            id=uuid.uuid4(),
            first_name="Margaret",
            last_name="Blackwood",
            phone="+14035551001",
            date_of_birth=datetime(1948, 3, 15),
            is_high_risk=True,
            address="12 Pine Crescent, Clearwater Ridge",
            notes="Hypertension, limited mobility. Lives alone.",
        )
        p2 = Patient(
            id=uuid.uuid4(),
            first_name="James",
            last_name="Whitehorse",
            phone="+14035551002",
            date_of_birth=datetime(1955, 11, 2),
            is_high_risk=True,
            address="45 River Road, Clearwater Ridge",
            notes="Diabetes type 2, requires regular cardiology follow-up.",
        )
        p3 = Patient(
            id=uuid.uuid4(),
            first_name="Sarah",
            last_name="Morin",
            phone="+14035551003",
            date_of_birth=datetime(1972, 7, 20),
            is_high_risk=False,
            address="8 Elk Avenue, Clearwater Ridge",
            notes="",
        )
        p4 = Patient(
            id=uuid.uuid4(),
            first_name="David",
            last_name="Cardinal",
            phone="+14035551004",
            date_of_birth=datetime(1940, 1, 8),
            is_high_risk=True,
            address="22 Spruce Lane, Clearwater Ridge",
            notes="Post-stroke rehabilitation. Needs accessible transport.",
        )

        # Extra patients to support 10 referrals
        p5 = Patient(
            id=uuid.uuid4(),
            first_name="Helen",
            last_name="Twofeathers",
            phone="+14035551005",
            date_of_birth=datetime(1962, 5, 12),
            is_high_risk=False,
            address="3 Birch Road, Clearwater Ridge",
            notes="Annual ophthalmology review.",
        )
        p6 = Patient(
            id=uuid.uuid4(),
            first_name="Robert",
            last_name="Clearsky",
            phone="+14035551006",
            date_of_birth=datetime(1978, 9, 30),
            is_high_risk=False,
            address="17 Cedar Lane, Clearwater Ridge",
            notes="",
        )

        db.add_all([p1, p2, p3, p4, p5, p6])
        await db.flush()

        # -- Referrals (one per status for testing) --
        now = datetime.utcnow()

        # 1. SENT_TO_SPECIALIST
        r1 = Referral(
            ticket_id="RC-SEED01",
            patient_id=p1.id,
            status=ReferralStatus.SENT_TO_SPECIALIST,
            description="Cardiology follow-up for irregular heartbeat",
            referred_to="Calgary Foothills Cardiology",
            specialist_phone="+14035559001",
            action_date=now + timedelta(days=7),
            notes="Referral sent. Awaiting specialist confirmation.",
            created_by="Nurse Adams",
            specialist_call_attempts=0,
            next_follow_up_at=now + timedelta(hours=48),
        )

        # 2. RESENT_TO_SPECIALIST
        r2 = Referral(
            ticket_id="RC-SEED02",
            patient_id=p1.id,
            status=ReferralStatus.RESENT_TO_SPECIALIST,
            description="Cardiology referral resent — specialist didn't receive first fax",
            referred_to="Calgary Foothills Cardiology",
            specialist_phone="+14035559001",
            action_date=now + timedelta(days=6),
            notes="Resent after first attempt was not received.",
            created_by="Nurse Adams",
            specialist_call_attempts=1,
            last_call_at=now - timedelta(days=1),
            next_follow_up_at=now + timedelta(hours=24),
        )

        # 3. REFERRAL_RECEIVED
        r3 = Referral(
            ticket_id="RC-SEED03",
            patient_id=p2.id,
            status=ReferralStatus.REFERRAL_RECEIVED,
            description="Endocrinology consult for diabetes management",
            referred_to="Red Deer Regional Hospital",
            specialist_phone="+14035559002",
            action_date=now + timedelta(days=5),
            notes="Specialist confirmed receipt of referral documents.",
            created_by="Nurse Adams",
            specialist_call_attempts=1,
            last_call_at=now - timedelta(days=1),
        )

        # 4. APPOINTMENT_SCHEDULING
        r4 = Referral(
            ticket_id="RC-SEED04",
            patient_id=p2.id,
            status=ReferralStatus.APPOINTMENT_SCHEDULING,
            description="Dermatology consult for chronic eczema",
            referred_to="Red Deer Dermatology Clinic",
            specialist_phone="+14035559005",
            action_date=now + timedelta(days=10),
            notes="Specialist is reviewing available slots.",
            created_by="Nurse Adams",
            specialist_call_attempts=1,
            last_call_at=now - timedelta(hours=12),
        )

        # 5. APPOINTMENT_SCHEDULED
        r5 = Referral(
            ticket_id="RC-SEED05",
            patient_id=p3.id,
            status=ReferralStatus.APPOINTMENT_SCHEDULED,
            description="Ophthalmology screening",
            referred_to="Rocky Mountain Eye Centre",
            specialist_phone="+14035559006",
            action_date=now + timedelta(days=4),
            scheduled_date=now + timedelta(days=8),
            appointment_type=AppointmentType.IN_PERSON,
            ride_needed=False,
            notes="Appointment confirmed for next week.",
            created_by="Nurse Chen",
            specialist_call_attempts=1,
            last_call_at=now - timedelta(days=2),
        )

        # 6. PATIENT_NOTIFIED
        r6 = Referral(
            ticket_id="RC-SEED06",
            patient_id=p4.id,
            status=ReferralStatus.PATIENT_NOTIFIED,
            description="Neurology follow-up post-stroke",
            referred_to="Calgary Stroke Centre",
            specialist_phone="+14035559004",
            action_date=now + timedelta(days=3),
            scheduled_date=now + timedelta(days=5),
            appointment_type=AppointmentType.IN_PERSON,
            ride_needed=True,
            ride_scheduled_time=now + timedelta(days=5, hours=-2),
            notes="Patient notified. Ride arranged.",
            created_by="Nurse Adams",
            specialist_call_attempts=1,
            last_call_at=now - timedelta(days=2),
            next_follow_up_at=now + timedelta(days=6),
        )

        # 7. COMPLETED
        r7 = Referral(
            ticket_id="RC-SEED07",
            patient_id=p5.id,
            status=ReferralStatus.COMPLETED,
            description="Annual ophthalmology review",
            referred_to="Rocky Mountain Eye Centre",
            specialist_phone="+14035559006",
            action_date=now - timedelta(days=8),
            scheduled_date=now - timedelta(days=5),
            appointment_type=AppointmentType.IN_PERSON,
            ride_needed=False,
            notes="Patient attended. Prescription updated.",
            created_by="Nurse Chen",
            specialist_call_attempts=1,
            last_call_at=now - timedelta(days=7),
        )

        # 8. MISSED
        r8 = Referral(
            ticket_id="RC-SEED08",
            patient_id=p4.id,
            status=ReferralStatus.MISSED,
            description="Physiotherapy assessment post-stroke",
            referred_to="Clearwater Ridge Physio",
            specialist_phone="+14035559007",
            action_date=now - timedelta(days=5),
            scheduled_date=now - timedelta(days=2),
            appointment_type=AppointmentType.IN_PERSON,
            ride_needed=True,
            notes="Highway closed due to storm. Patient missed appointment.",
            created_by="Nurse Adams",
            specialist_call_attempts=2,
            last_call_at=now - timedelta(days=1),
        )

        # 9. RESCHEDULE_REQUESTED
        r9 = Referral(
            ticket_id="RC-SEED09",
            patient_id=p6.id,
            status=ReferralStatus.RESCHEDULE_REQUESTED,
            description="Mental health counselling — follow-up",
            referred_to="Alberta Mental Health Services",
            specialist_phone="+14035559008",
            action_date=now - timedelta(days=3),
            scheduled_date=now - timedelta(days=1),
            appointment_type=AppointmentType.VIRTUAL,
            ride_needed=False,
            notes="Patient requested reschedule due to connectivity issues.",
            created_by="Nurse Adams",
            specialist_call_attempts=1,
            last_call_at=now - timedelta(hours=6),
        )

        # 10. CLOSED
        r10 = Referral(
            ticket_id="RC-SEED10",
            patient_id=p3.id,
            status=ReferralStatus.CLOSED,
            description="Routine ortho follow-up for knee replacement",
            referred_to="Calgary Ortho Clinic",
            specialist_phone="+14035559003",
            action_date=now - timedelta(days=14),
            scheduled_date=now - timedelta(days=10),
            appointment_type=AppointmentType.IN_PERSON,
            ride_needed=False,
            notes="Patient attended. Ticket closed.",
            created_by="Nurse Chen",
            specialist_call_attempts=1,
            last_call_at=now - timedelta(days=13),
        )

        db.add_all([r1, r2, r3, r4, r5, r6, r7, r8, r9, r10])

        # -- Users --
        admin = User(
            username="admin",
            hashed_password=hash_password("changeme123"),
            full_name="System Administrator",
            role="admin",
        )
        nurse = User(
            username="nurse.adams",
            hashed_password=hash_password("changeme123"),
            full_name="Nurse Adams",
            role="nurse",
        )
        db.add_all([admin, nurse])

        await db.commit()

    print("Seeded 6 patients, 10 referrals, and 2 users.")


if __name__ == "__main__":
    asyncio.run(seed())
