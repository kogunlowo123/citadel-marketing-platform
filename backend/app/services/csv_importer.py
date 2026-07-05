import json
import uuid
from datetime import datetime, timezone

import pandas as pd
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.models.import_job import ImportJob
from app.utils.email_validator import validate_email_format

logger = structlog.get_logger()

COLUMN_ALIASES = {
    "email": ["email", "email_address", "e-mail", "emailaddress", "mail"],
    "first_name": ["first_name", "firstname", "first name", "fname", "given_name"],
    "last_name": ["last_name", "lastname", "last name", "lname", "surname", "family_name"],
    "phone": ["phone", "phone_number", "telephone", "tel", "mobile"],
    "company": ["company", "organization", "org", "company_name", "organisation"],
}


class CSVImporter:
    async def import_file(
        self,
        file_path: str,
        job_id: str,
        column_mapping: dict | None,
        tags: list[str] | None,
        db: AsyncSession,
    ) -> dict:
        """Import contacts from a CSV file."""
        result = await db.execute(select(ImportJob).where(ImportJob.id == str(job_id)))
        job = result.scalar_one_or_none()
        if job is None:
            raise ValueError(f"ImportJob {job_id} not found")

        job.status = "processing"
        await db.flush()
        await db.commit()

        try:
            df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
        except Exception as e:
            job.status = "failed"
            job.errors = {"read_error": str(e)}
            await db.flush()
            await db.commit()
            return {"error": str(e)}

        job.total_rows = len(df)
        await db.flush()
        await db.commit()

        mapping = column_mapping or self._detect_columns(df)
        df = self._clean_data(df, mapping)

        imported = 0
        skipped = 0
        duplicates = 0
        errors = []

        # Get existing emails for dedup
        existing_result = await db.execute(select(Contact.email))
        existing_emails = {row[0].lower() for row in existing_result.all()}

        for idx, row in df.iterrows():
            email_col = mapping.get("email")
            if not email_col or email_col not in row:
                skipped += 1
                continue

            email = str(row[email_col]).strip().lower()
            if not email or not validate_email_format(email):
                errors.append({"row": idx + 1, "email": email, "reason": "Invalid email format"})
                skipped += 1
                continue

            if email in existing_emails:
                duplicates += 1
                continue

            contact = Contact(
                email=email,
                first_name=str(row.get(mapping.get("first_name", ""), "")).strip() or None,
                last_name=str(row.get(mapping.get("last_name", ""), "")).strip() or None,
                phone=str(row.get(mapping.get("phone", ""), "")).strip() or None,
                company=str(row.get(mapping.get("company", ""), "")).strip() or None,
                tags=",".join(tags) if tags else "",
                source="csv_import",
                status="active",
            )
            db.add(contact)
            existing_emails.add(email)
            imported += 1

            job.processed_rows = idx + 1
            if imported % 500 == 0:
                await db.flush()
                await db.commit()

        await db.flush()
        await db.commit()

        job.status = "completed"
        job.imported_count = imported
        job.skipped_count = skipped
        job.duplicate_count = duplicates
        job.error_count = len(errors)
        job.errors = json.dumps(errors[:100]) if errors else None
        job.processed_rows = len(df)
        job.completed_at = datetime.now(timezone.utc).isoformat()
        await db.flush()
        await db.commit()

        logger.info(
            "csv_import_completed",
            job_id=job_id,
            imported=imported,
            skipped=skipped,
            duplicates=duplicates,
            errors=len(errors),
        )
        return {"imported": imported, "skipped": skipped, "duplicates": duplicates, "errors": len(errors)}

    def _detect_columns(self, df: pd.DataFrame) -> dict:
        """Auto-map CSV columns to contact fields."""
        mapping = {}
        columns_lower = {col.lower().strip(): col for col in df.columns}

        for field, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in columns_lower:
                    mapping[field] = columns_lower[alias]
                    break

        return mapping

    def _clean_data(self, df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
        """Strip whitespace and normalize data."""
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.strip()

        email_col = mapping.get("email")
        if email_col and email_col in df.columns:
            df[email_col] = df[email_col].str.lower()
            df = df[df[email_col].str.len() > 0]
            df = df.drop_duplicates(subset=[email_col], keep="first")

        return df
