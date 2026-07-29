"""Background jobs.

The CSV reader below is written the way you would write it for a 2 GB file,
even though you will test it with 20 rows. It reads one line at a time from S3
and never holds the file in memory. Change nothing and it handles 2 GB on a
t3.micro.
"""
import codecs
import csv

from .celery_app import celery_app
from .config import settings
from .db import SessionLocal
from .models import Upload
from .storage import open_stream


@celery_app.task(name="process_csv", bind=True, max_retries=3, default_retry_delay=30)
def process_csv(self, upload_id: str) -> None:
    db = SessionLocal()
    try:
        upload = db.get(Upload, upload_id)
        if upload is None:
            return
        # Idempotent: safe to run twice. Required, because acks_late means a
        # job CAN be delivered twice after a crash.
        if upload.status == "done":
            return

        upload.status = "processing"
        upload.processed_rows = 0
        upload.error = ""
        db.commit()

        rows = 0
        stream = codecs.getreader("utf-8")(open_stream(upload.s3_key))
        reader = csv.reader(stream)
        next(reader, None)  # skip the header row

        for _ in reader:
            rows += 1
            # Write progress occasionally, not every row -- otherwise the
            # database becomes the bottleneck instead of the file.
            if rows % settings.csv_progress_every == 0:
                upload.processed_rows = rows
                db.commit()

        upload.row_count = rows
        upload.processed_rows = rows
        upload.status = "done"
        db.commit()

    except Exception as exc:
        db.rollback()
        row = db.get(Upload, upload_id)
        if row is not None:
            row.status = "failed"
            row.error = str(exc)[:500]
            db.commit()
        raise self.retry(exc=exc) from exc
    finally:
        db.close()
