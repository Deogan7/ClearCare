"""Import facilities from the ODHF CSV into the database."""

import asyncio
import csv
import sys
import uuid

from app.db.session import async_session
from app.models.facility import Facility


async def import_csv(csv_path: str) -> None:
    async with async_session() as db:
        count = 0
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                facility = Facility(
                    id=uuid.uuid4(),
                    index=int(row.get("index", 0)) if row.get("index") else None,
                    facility_name=row.get("facility_name", "").strip(),
                    source_facility_type=row.get("source_facility_type", "").strip() or None,
                    odhf_facility_type=row.get("odhf_facility_type", "").strip() or None,
                    provider=row.get("provider", "").strip() or None,
                    unit=row.get("unit", "").strip() or None,
                    street_no=row.get("street_no", "").strip() or None,
                    street_name=row.get("street_name", "").strip() or None,
                    postal_code=row.get("postal_code", "").strip() or None,
                    city=row.get("city", "").strip() or None,
                    province=row.get("province", "").strip() or None,
                    source_format_address=row.get("source_format_address", "").strip() or None,
                    csd_name=row.get("CSDname", "").strip() or None,
                    csd_uid=row.get("CSDuid", "").strip() or None,
                    pr_uid=row.get("Pruid", "").strip() or None,
                    latitude=float(row["latitude"]) if row.get("latitude") else None,
                    longitude=float(row["longitude"]) if row.get("longitude") else None,
                )
                batch.append(facility)
                count += 1

                # Commit in batches of 500
                if len(batch) >= 500:
                    db.add_all(batch)
                    await db.flush()
                    batch = []
                    print(f"  Imported {count} facilities...")

            if batch:
                db.add_all(batch)

            await db.commit()

    print(f"Done. Imported {count} facilities total.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: PYTHONPATH=. python -m scripts.import_facilities <path_to_csv>")
        sys.exit(1)
    asyncio.run(import_csv(sys.argv[1]))
