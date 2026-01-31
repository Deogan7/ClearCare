"""Seed the database with test patients and referrals for development."""

import asyncio
import uuid
from datetime import datetime, timedelta

from app.db.session import async_session
from app.models.patient import Patient
from app.models.referral import Referral
from app.models.referral import ReferralStatus
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

        db.add_all([p1, p2, p3, p4])
        await db.flush()

        # -- Referrals --
        now = datetime.utcnow()

        r1 = Referral(
            ticket_id="RC-SEED01",
            patient_id=p1.id,
            status=ReferralStatus.PENDING_CONFIRMATION,
            description="Cardiology follow-up for irregular heartbeat",
            referred_to="Calgary Foothills Cardiology",
            action_date=now + timedelta(days=7),
            scheduled_date=None,
            notes="Awaiting hospital confirmation.",
            created_by="Nurse Adams",
        )
        r2 = Referral(
            ticket_id="RC-SEED02",
            patient_id=p2.id,
            status=ReferralStatus.SCHEDULED,
            description="Endocrinology consult for diabetes management",
            referred_to="Red Deer Regional Hospital",
            action_date=now + timedelta(days=3),
            scheduled_date=now + timedelta(days=5),
            notes="Transport arranged via community van.",
            created_by="Nurse Adams",
        )
        r3 = Referral(
            ticket_id="RC-SEED03",
            patient_id=p3.id,
            status=ReferralStatus.ATTENDED,
            description="Routine ortho follow-up for knee replacement",
            referred_to="Calgary Ortho Clinic",
            action_date=now - timedelta(days=10),
            scheduled_date=now - timedelta(days=7),
            notes="Patient attended. Awaiting discharge summary.",
            created_by="Nurse Chen",
        )
        r4 = Referral(
            ticket_id="RC-SEED04",
            patient_id=p4.id,
            status=ReferralStatus.MISSED,
            description="Neurology follow-up post-stroke",
            referred_to="Calgary Stroke Centre",
            action_date=now - timedelta(days=5),
            scheduled_date=now - timedelta(days=2),
            notes="Highway closed due to storm. Needs rescheduling.",
            created_by="Nurse Adams",
        )

        db.add_all([r1, r2, r3, r4])

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

    print("Seeded 4 patients, 4 referrals, and 2 users.")


if __name__ == "__main__":
    asyncio.run(seed())
