import asyncio
import logging
import os
from time import perf_counter

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import (
    Base,
    engine,
    migrate_customers_nullable,
    migrate_inheritance_case_properties_schema,
    migrate_inheritance_cases_schema,
    migrate_properties_schema,
    migrate_property_land_rows,
    migrate_zalo_exchange_schema,
    migrate_zalo_schema,
)
from observability import configure_process_logging
from contextlib import asynccontextmanager
from routers import cases, customers, ocr_ai, participants, properties, zalo_inbox, zalo_sync

os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

WEB_LOG_PATH = configure_process_logging("web")
app_logger = logging.getLogger("notary.web")
app_logger.info("Web logging initialized at %s", WEB_LOG_PATH)

# Run schema migration before create_all.
migrate_customers_nullable()
migrate_inheritance_cases_schema()
migrate_properties_schema()
migrate_property_land_rows()
migrate_inheritance_case_properties_schema()
migrate_zalo_schema()
migrate_zalo_exchange_schema()
Base.metadata.create_all(bind=engine)


def _zalo_sync_interval_seconds() -> float:
    """MIN-99: 0 hoac am = tat periodic sync; mac dinh 300s."""
    try:
        return float(os.getenv("ZALO_SYNC_INTERVAL_SECONDS", "300"))
    except ValueError:
        return 300.0


async def _periodic_zalo_sync(interval_seconds: float) -> None:
    """Vong lap sync dinh ky — loi mot luot khong giet task (MIN-99)."""
    from database import SessionLocal

    while True:
        await asyncio.sleep(interval_seconds)
        db = SessionLocal()
        try:
            await asyncio.to_thread(zalo_sync.run_sync_once, db)
        except asyncio.CancelledError:
            raise
        except Exception:
            app_logger.exception("Periodic Zalo sync failed")
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    interval = _zalo_sync_interval_seconds()
    sync_task = (
        asyncio.create_task(_periodic_zalo_sync(interval)) if interval > 0 else None
    )
    try:
        yield
    finally:
        if sync_task is not None:
            sync_task.cancel()
            try:
                await sync_task
            except asyncio.CancelledError:
                pass
        zalo_inbox._terminate_connector_process()


app = FastAPI(
    title="He thong Quan ly Ho so Cong chung",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def http_timing_log(request: Request, call_next):
    path = request.url.path
    should_log = path.startswith("/api/ocr/")
    start = perf_counter()
    if not should_log:
        return await call_next(request)

    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed_ms = round((perf_counter() - start) * 1000.0, 2)
        app_logger.exception(
            "[HTTP_TIMING] method=%s path=%s status=500 elapsed_ms=%s client=%s error=%s",
            request.method,
            path,
            elapsed_ms,
            request.client.host if request.client else "-",
            exc,
        )
        raise

    elapsed_ms = round((perf_counter() - start) * 1000.0, 2)
    level = logging.WARNING if response.status_code >= 500 else logging.INFO
    app_logger.log(
        level,
        "[HTTP_TIMING] method=%s path=%s status=%s elapsed_ms=%s client=%s",
        request.method,
        path,
        response.status_code,
        elapsed_ms,
        request.client.host if request.client else "-",
    )
    return response


app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

app.include_router(customers.router, prefix="/customers", tags=["Khach hang"])
app.include_router(properties.router, prefix="/properties", tags=["Tai san"])
app.include_router(cases.router, prefix="/cases", tags=["Ho so thua ke"])
app.include_router(participants.router, prefix="/participants", tags=["Nguoi tham gia"])
app.include_router(ocr_ai.router, prefix="/api/ocr", tags=["OCR"])
app.include_router(zalo_inbox.router)
app.include_router(zalo_sync.router)


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/api/stats")
async def stats():
    from database import SessionLocal
    from models import InheritanceCase
    from routers.cases import _live_master_refs

    db = SessionLocal()
    try:
        # MIN-141 đợt 4: đếm người/tài sản THỰC SỰ gắn hồ sơ — DISTINCT qua
        # case (người chết/tài sản chính/người nhận ủy quyền) + participant
        # (kể cả parent_customer_id) + link tài sản phụ. Danh bạ trơ (chưa
        # gắn hồ sơ nào) không tính; primary/link trùng nhau đếm một lần.
        customer_ids, property_ids = _live_master_refs(db)
        return {
            "customers": len(customer_ids),
            "properties": len(property_ids),
            "cases": db.query(InheritanceCase).count(),
            "locked": db.query(InheritanceCase).filter(InheritanceCase.trang_thai == "locked").count(),
        }
    finally:
        db.close()
