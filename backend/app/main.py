"""The API.

Notice what is NOT here: no file bytes, no in-memory dictionaries, no local
disk writes, no background threads. The API only reads and writes the database
and drops messages on a queue. That is what "stateless" means, and it is why
you can run one copy or fifty behind a load balancer with no code changes.
"""
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .models import Item, Upload
from .schemas import ItemIn, ItemOut, UploadOut, UploadStartIn, UploadStartOut
from .storage import presigned_put_url
from .tasks import process_csv

@asynccontextmanager
async def lifespan(_: FastAPI):
    # Runs once when a server starts, not when the module is imported.
    # Import-time database calls make the app impossible to test and make
    # startup fail if the database is briefly unreachable.
    if settings.create_tables:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Report Builder", lifespan=lifespan)


@app.get("/health")
def health():
    """The load balancer calls this every 30 seconds to decide if this server
    should receive traffic. Keep it fast and dependency-free."""
    return {"status": "ok"}


# ---------- CRUD ----------

@app.post("/items", response_model=ItemOut, status_code=201)
def create_item(payload: ItemIn, db: Session = Depends(get_db)):
    item = Item(name=payload.name, description=payload.description)
    db.add(item)
    db.commit()
    return item


@app.get("/items", response_model=list[ItemOut])
def list_items(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    # Always paginate. A list endpoint with no limit is a future outage.
    stmt = select(Item).order_by(Item.created_at.desc()).limit(min(limit, 200)).offset(offset)
    return list(db.scalars(stmt))


@app.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: str, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(404, "not found")
    return item


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: str, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if item is not None:
        db.delete(item)
        db.commit()


# ---------- Upload ----------

@app.post("/uploads", response_model=UploadStartOut, status_code=201)
def start_upload(payload: UploadStartIn, db: Session = Depends(get_db)):
    """Step 1 of 3: hand out a permission slip. No file touches this server."""
    upload = Upload(
        filename=payload.filename,
        s3_key=f"uploads/{uuid.uuid4()}/{payload.filename}",
    )
    db.add(upload)
    db.commit()
    return UploadStartOut(upload_id=upload.id, upload_url=presigned_put_url(upload.s3_key))


@app.post("/uploads/{upload_id}/complete", response_model=UploadOut)
def complete_upload(upload_id: str, db: Session = Depends(get_db)):
    """Step 2 of 3: the browser finished uploading, so queue the work.

    This returns instantly. The slow part happens in a worker, on a different
    machine, that you can scale separately.
    """
    upload = db.get(Upload, upload_id)
    if upload is None:
        raise HTTPException(404, "not found")
    upload.status = "queued"
    db.commit()
    process_csv.delay(upload.id)
    return upload


@app.get("/uploads/{upload_id}", response_model=UploadOut)
def get_upload(upload_id: str, db: Session = Depends(get_db)):
    """Step 3 of 3: the browser polls this for progress."""
    upload = db.get(Upload, upload_id)
    if upload is None:
        raise HTTPException(404, "not found")
    return upload
