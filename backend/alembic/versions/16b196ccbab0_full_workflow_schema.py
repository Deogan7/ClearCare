"""full_workflow_schema

Revision ID: 16b196ccbab0
Revises: 94005dcabf3f
Create Date: 2026-01-31 17:07:22.724524
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '16b196ccbab0'
down_revision: Union[str, None] = '94005dcabf3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Old and new enum values
OLD_STATUSES = [
    'pending_confirmation', 'scheduled', 'attended', 'resolved', 'missed'
]
NEW_STATUSES = [
    'sent_to_specialist', 'resent_to_specialist', 'referral_received',
    'appointment_scheduling', 'appointment_scheduled', 'patient_notified',
    'completed', 'missed', 'reschedule_requested', 'closed'
]

# Map old status values to new ones for existing data
STATUS_MAP = {
    'pending_confirmation': 'sent_to_specialist',
    'scheduled': 'appointment_scheduled',
    'attended': 'completed',
    'resolved': 'closed',
    'missed': 'missed',
}


def upgrade() -> None:
    # --- 1. Update the ReferralStatus enum ---
    # Rename old enum
    op.execute("ALTER TYPE referralstatus RENAME TO referralstatus_old")

    # Create new enum with all workflow statuses
    new_enum = postgresql.ENUM(*NEW_STATUSES, name='referralstatus', create_type=True)
    new_enum.create(op.get_bind(), checkfirst=True)

    # Change column type using the mapping
    op.execute(
        "ALTER TABLE referrals ALTER COLUMN status TYPE referralstatus "
        "USING CASE "
        + " ".join(
            f"WHEN status::text = '{old}' THEN '{new}'::referralstatus"
            for old, new in STATUS_MAP.items()
        )
        + " ELSE 'sent_to_specialist'::referralstatus END"
    )

    # Drop old enum
    op.execute("DROP TYPE referralstatus_old")

    # --- 2. Add new columns to referrals ---
    op.add_column('referrals', sa.Column('specialist_phone', sa.String(length=20), nullable=True))

    # Create appointment_type enum
    appointment_enum = postgresql.ENUM('IN_PERSON', 'VIRTUAL', 'UNKNOWN', name='appointmenttype', create_type=True)
    appointment_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('referrals', sa.Column('appointment_type', sa.Enum('IN_PERSON', 'VIRTUAL', 'UNKNOWN', name='appointmenttype'), nullable=True))

    op.add_column('referrals', sa.Column('ride_needed', sa.Boolean(), nullable=True))
    op.add_column('referrals', sa.Column('ride_scheduled_time', sa.DateTime(), nullable=True))
    op.add_column('referrals', sa.Column('specialist_call_attempts', sa.Integer(), server_default='0', nullable=False))
    op.add_column('referrals', sa.Column('last_call_at', sa.DateTime(), nullable=True))
    op.add_column('referrals', sa.Column('next_follow_up_at', sa.DateTime(), nullable=True))

    # --- 3. Create facilities table (IF NOT EXISTS for idempotency) ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS facilities (
            id UUID NOT NULL PRIMARY KEY,
            "index" INTEGER,
            facility_name VARCHAR(500) NOT NULL,
            source_facility_type VARCHAR(255),
            odhf_facility_type VARCHAR(255),
            provider VARCHAR(500),
            unit VARCHAR(100),
            street_no VARCHAR(50),
            street_name VARCHAR(255),
            postal_code VARCHAR(10),
            city VARCHAR(255),
            province VARCHAR(10),
            source_format_address VARCHAR(500),
            csd_name VARCHAR(255),
            csd_uid VARCHAR(20),
            pr_uid VARCHAR(10),
            latitude FLOAT,
            longitude FLOAT
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_facilities_facility_name ON facilities (facility_name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_facilities_city ON facilities (city)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_facilities_province ON facilities (province)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_facilities_postal_code ON facilities (postal_code)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_facilities_odhf_facility_type ON facilities (odhf_facility_type)")


def downgrade() -> None:
    # Drop facilities
    op.drop_index('ix_facilities_odhf_facility_type')
    op.drop_index('ix_facilities_postal_code')
    op.drop_index('ix_facilities_province')
    op.drop_index('ix_facilities_city')
    op.drop_index('ix_facilities_facility_name')
    op.drop_table('facilities')

    # Remove new columns
    op.drop_column('referrals', 'next_follow_up_at')
    op.drop_column('referrals', 'last_call_at')
    op.drop_column('referrals', 'specialist_call_attempts')
    op.drop_column('referrals', 'ride_scheduled_time')
    op.drop_column('referrals', 'ride_needed')
    op.drop_column('referrals', 'appointment_type')
    op.drop_column('referrals', 'specialist_phone')

    # Drop appointment_type enum
    op.execute("DROP TYPE IF EXISTS appointmenttype")

    # Revert status enum
    op.execute("ALTER TYPE referralstatus RENAME TO referralstatus_new")
    old_enum = postgresql.ENUM(*OLD_STATUSES, name='referralstatus', create_type=True)
    old_enum.create(op.get_bind(), checkfirst=True)
    op.execute(
        "ALTER TABLE referrals ALTER COLUMN status TYPE referralstatus "
        "USING CASE "
        "WHEN status::text = 'sent_to_specialist' THEN 'pending_confirmation'::referralstatus "
        "WHEN status::text = 'appointment_scheduled' THEN 'scheduled'::referralstatus "
        "WHEN status::text = 'completed' THEN 'attended'::referralstatus "
        "WHEN status::text = 'closed' THEN 'resolved'::referralstatus "
        "WHEN status::text = 'missed' THEN 'missed'::referralstatus "
        "ELSE 'pending_confirmation'::referralstatus END"
    )
    op.execute("DROP TYPE referralstatus_new")
