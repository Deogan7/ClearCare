# Member 1 — Part 1 & Part 2 Completion Report

Documentation of what was done, why it was done, how it works, and how to use it for Part 1 (Alembic Async Configuration) and Part 2 (Seed Script).

---

## Part 1: Alembic Async Configuration

### What Was Done

Four deliverables were completed:

1. **Created `backend/alembic/versions/` directory** — the folder Alembic uses to store migration files.
2. **Created `backend/alembic/script.py.mako`** — a Mako template that Alembic uses to generate new migration files when you run `alembic revision`.
3. **Wrote `backend/alembic/env.py`** — the async-compatible migration environment that connects Alembic to the PostgreSQL database through SQLAlchemy's async engine.
4. **Generated the initial migration `backend/alembic/versions/1ba812ca8048_create_patients_and_referrals_tables.py`** — the first migration file that creates the `patients` and `referrals` tables.

### Why It Was Done

The project uses an **async** PostgreSQL driver (`asyncpg`) throughout the FastAPI application. Alembic's default configuration assumes a synchronous database connection, so it cannot run migrations against the async engine out of the box. The environment file had to be written from scratch to bridge Alembic's synchronous migration runner with the async database driver.

Without this configuration:
- There is no way to version-control database schema changes.
- Team members would have to manually create tables, leading to inconsistencies.
- There is no rollback mechanism if a schema change breaks something.

### How It Works

#### File-by-file breakdown

**`backend/alembic.ini`** (pre-existing, modified)
- The entry point for the `alembic` CLI. It tells Alembic where to find migration scripts (`script_location = alembic`) and provides a fallback `sqlalchemy.url`. However, `env.py` overrides this URL at runtime with the value from `settings.DATABASE_URL`, so the `.env` file remains the single source of truth for the connection string.

**`backend/alembic/script.py.mako`**
- A Mako template file. Every time you run `alembic revision`, Alembic reads this template and fills in the placeholders (`${message}`, `${up_revision}`, etc.) to generate a new Python migration file. This is why migration files all share the same boilerplate structure.

**`backend/alembic/env.py`**
- This is the core configuration file. Here is what each section does:

  1. **Model imports** (lines 13-14): Imports `Patient` and `Referral` model classes. This is required because Alembic's `--autogenerate` feature works by comparing the tables defined in `Base.metadata` against what actually exists in the database. If models are not imported, `Base.metadata` is empty and Alembic sees nothing to generate.

  2. **URL override** (line 17): `config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)` overrides whatever is in `alembic.ini` with the value from the application's `Settings` class (which reads from `.env`). This avoids having the database URL duplicated in two places.

  3. **`run_migrations_offline()`** (lines 26-35): Generates raw SQL without connecting to the database. Useful for producing migration scripts that can be handed to a DBA.

  4. **`do_run_migrations(connection)`** (lines 38-41): A synchronous helper that Alembic calls to actually execute migration operations against a live database connection.

  5. **`run_migrations_online()`** (lines 44-49): Creates an async engine, opens an async connection, and then uses `connection.run_sync(do_run_migrations)` to bridge the async connection into the synchronous migration runner. This is the key pattern that makes Alembic work with `asyncpg`.

  6. **Entry point** (lines 52-55): Checks if Alembic is running in offline or online mode and calls the appropriate function. `asyncio.run()` is used to execute the async online migration function.

**`backend/alembic/versions/1ba812ca8048_create_patients_and_referrals_tables.py`**
- This is the auto-generated migration file. It was created by running `alembic revision --autogenerate -m "create patients and referrals tables"`, which compared the models in `Base.metadata` against the (empty) database and produced the `CREATE TABLE` statements.

  - **`upgrade()`**: Creates the `patients` table first (since `referrals` has a foreign key to it), then creates the `referrals` table with a `referralstatus` enum, and finally adds a unique index on `ticket_id`.
  - **`downgrade()`**: Reverses everything in the correct order — drops the index, drops `referrals`, drops `patients`, and drops the `referralstatus` enum type.

  The filename `1ba812ca8048_create_patients_and_referrals_tables.py` follows Alembic's convention: `<revision_hash>_<slugified_message>.py`. The hash is a randomly generated identifier stored both in the file and in the `alembic_version` database table to track which migration the database is currently at.

#### Database tables created

**`patients` table:**

| Column         | Type          | Constraints                |
|----------------|---------------|----------------------------|
| `id`           | UUID          | Primary key                |
| `first_name`   | String(100)   | NOT NULL                   |
| `last_name`    | String(100)   | NOT NULL                   |
| `phone`        | String(20)    | NOT NULL                   |
| `date_of_birth`| DateTime      | Nullable                   |
| `is_high_risk` | Boolean       | NOT NULL                   |
| `address`      | String(255)   | Nullable                   |
| `notes`        | String        | Nullable                   |
| `created_at`   | DateTime      | NOT NULL, default `now()`  |
| `updated_at`   | DateTime      | NOT NULL, default `now()`  |

**`referrals` table:**

| Column          | Type              | Constraints                          |
|-----------------|-------------------|--------------------------------------|
| `id`            | UUID              | Primary key                          |
| `ticket_id`     | String(20)        | NOT NULL, unique index               |
| `patient_id`    | UUID              | NOT NULL, foreign key -> patients.id |
| `status`        | Enum(referralstatus) | NOT NULL                          |
| `description`   | String            | Nullable                             |
| `referred_to`   | String(255)       | NOT NULL                             |
| `action_date`   | DateTime          | NOT NULL                             |
| `scheduled_date`| DateTime          | Nullable                             |
| `notes`         | String            | Nullable                             |
| `created_by`    | String(100)       | NOT NULL                             |
| `created_at`    | DateTime          | NOT NULL, default `now()`            |
| `updated_at`    | DateTime          | NOT NULL, default `now()`            |

The `referralstatus` enum has five values: `PENDING_CONFIRMATION`, `SCHEDULED`, `ATTENDED`, `RESOLVED`, `MISSED`.

### How to Use It

**Prerequisites:**
- PostgreSQL must be running locally.
- The `ridgecare` database must exist (`createdb ridgecare` if it does not).
- A `.env` file in `backend/` with a valid `DATABASE_URL` (e.g., `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ridgecare`).

**Apply all migrations (create the tables):**
```bash
cd backend
alembic upgrade head
```

**Verify the tables exist:**
```bash
psql ridgecare -c "\dt"
```
Expected output should list `patients`, `referrals`, and `alembic_version`.

**Roll back all migrations (destroy the tables):**
```bash
cd backend
alembic downgrade base
```

**Generate a new migration after model changes:**
```bash
cd backend
alembic revision --autogenerate -m "describe what changed"
```
Then review the generated file in `backend/alembic/versions/` before applying it.

**Re-apply from scratch (clean slate):**
```bash
cd backend
alembic downgrade base
alembic upgrade head
```

---

## Part 2: Seed Script

### What Was Done

Two files were created:

1. **`backend/scripts/__init__.py`** — an empty file that makes `scripts` a Python package, required for running the seed script as a module.
2. **`backend/scripts/seed.py`** — an async script that inserts 4 test patients and 4 test referrals into the database.

### Why It Was Done

The team needs consistent test data to develop and test against. Without seed data:
- Frontend developers cannot build the dashboard because there are no referrals to display.
- API developers cannot verify that endpoints return correct data.
- Every team member would have to manually insert rows, leading to inconsistent test environments.

The seed script gives everyone the same baseline dataset with a single command.

### How It Works

The script imports `async_session` from the application's database session module, which provides an async SQLAlchemy session connected to the same database the application uses (configured via `DATABASE_URL` in `.env`).

#### Seed data overview

**4 Patients:**

| Name               | Phone          | High Risk | Notes                                            |
|--------------------|----------------|-----------|--------------------------------------------------|
| Margaret Blackwood | +14035551001   | Yes       | Hypertension, limited mobility. Lives alone.     |
| James Whitehorse   | +14035551002   | Yes       | Diabetes type 2, requires cardiology follow-up.  |
| Sarah Morin        | +14035551003   | No        | (none)                                           |
| David Cardinal     | +14035551004   | Yes       | Post-stroke rehab. Needs accessible transport.   |

**4 Referrals:**

| Ticket ID  | Patient            | Status                 | Referred To                     | Scenario                           |
|------------|--------------------|------------------------|---------------------------------|------------------------------------|
| RC-SEED01  | Margaret Blackwood | PENDING_CONFIRMATION   | Calgary Foothills Cardiology    | New referral, awaiting confirmation|
| RC-SEED02  | James Whitehorse   | SCHEDULED              | Red Deer Regional Hospital      | Confirmed, transport arranged      |
| RC-SEED03  | Sarah Morin        | ATTENDED               | Calgary Ortho Clinic            | Patient attended, awaiting summary |
| RC-SEED04  | David Cardinal     | MISSED                 | Calgary Stroke Centre           | Missed due to highway storm closure|

These four referrals deliberately cover four different statuses so that every state in the referral lifecycle can be tested. The dates are relative to the time the script is run — future dates for pending/scheduled referrals, past dates for attended/missed ones.

#### Execution flow

1. Opens an async database session via `async_session()`.
2. Creates 4 `Patient` objects with `uuid.uuid4()` IDs and adds them to the session.
3. Calls `await db.flush()` — this sends the `INSERT` statements to the database and populates each patient's `id` field, but does not yet commit the transaction. The flush is necessary because the referral objects reference `patient_id`, which must be a real UUID that exists (at least within the transaction).
4. Creates 4 `Referral` objects, each linking to a patient via `patient_id=p<n>.id`.
5. Calls `await db.commit()` — commits the entire transaction (all 8 rows) atomically. If anything fails, nothing is inserted.
6. Prints a confirmation message.

### How to Use It

**Prerequisites:**
- Migrations must have been applied first (`alembic upgrade head`) so the tables exist.
- The `.env` file must have a valid `DATABASE_URL`.

**Run the seed script:**
```bash
cd backend
python -m scripts.seed
```

Expected output:
```
Seeded 4 patients and 4 referrals.
```

**Verify the data:**
```bash
psql ridgecare -c "SELECT first_name, last_name, is_high_risk FROM patients;"
psql ridgecare -c "SELECT ticket_id, status, referred_to FROM referrals;"
```

**Re-seeding:**
The script does not check for existing data. Running it twice will fail because `ticket_id` has a unique constraint (e.g., `RC-SEED01` already exists). To re-seed, clear the tables first:

```bash
psql ridgecare -c "DELETE FROM referrals; DELETE FROM patients;"
cd backend
python -m scripts.seed
```

Or reset the entire database:
```bash
cd backend
alembic downgrade base
alembic upgrade head
python -m scripts.seed
```

---

## Files Summary

| File | Status | Purpose |
|------|--------|---------|
| `backend/alembic.ini` | Pre-existing | Alembic CLI configuration |
| `backend/alembic/env.py` | Written | Async migration environment |
| `backend/alembic/script.py.mako` | Created | Template for new migration files |
| `backend/alembic/versions/` | Created | Directory for migration files |
| `backend/alembic/versions/1ba812ca8048_...py` | Generated | Initial migration (patients + referrals) |
| `backend/scripts/__init__.py` | Created | Makes scripts a Python package |
| `backend/scripts/seed.py` | Created | Seeds test data into the database |
