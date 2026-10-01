"""HTTP application and bounded job entry point."""

import hmac
import logging
import os
import threading

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import Response

from .cache import CachedCsv, is_fresh, read_cached_csv, write_cached_csv
from .config import Dataset, Settings, load_datasets
from .connections import get_specify_client
from .csv_export import ExportError, render_query_csv

app = FastAPI(title='Private allowlisted Specify query CSV API for Datavis applications')
query_lock = threading.Lock()
logger = logging.getLogger(__name__)


def initialize(settings: Settings) -> None:
    """Idempotently prepare durable API state."""
    (settings.state_dir / "cache").mkdir(parents=True, exist_ok=True)


def cached_dataset_csv(
    settings: Settings,
    dataset: Dataset,
    *,
    force: bool = False,
    allow_stale: bool = True,
) -> tuple[CachedCsv, str]:
    cached = read_cached_csv(settings.state_dir, dataset.slug)
    if not force and cached is not None and is_fresh(cached, settings.cache_ttl_seconds):
        return cached, "HIT"
    if not query_lock.acquire(timeout=1):
        if cached is not None and allow_stale:
            return cached, "STALE"
        raise ExportError("a dataset export is already running")
    try:
        cached = read_cached_csv(settings.state_dir, dataset.slug)
        if not force and cached is not None and is_fresh(
            cached, settings.cache_ttl_seconds
        ):
            return cached, "HIT"
        try:
            content = render_query_csv(
                get_specify_client(settings),
                dataset.query_id,
                settings.max_csv_rows,
                dataset.required_columns,
            )
            return write_cached_csv(settings.state_dir, dataset.slug, content), "MISS"
        except Exception:
            if cached is None or not allow_stale:
                raise
            logger.exception(
                "Dataset refresh failed; serving stale cache for %s", dataset.slug
            )
            return cached, "STALE"
    finally:
        query_lock.release()


def refresh_all_datasets(settings: Settings) -> None:
    for dataset in load_datasets(settings.datasets_path).values():
        cached_dataset_csv(settings, dataset, force=True, allow_stale=False)


def require_service_token(
    x_service_token: str = Header(alias="X-Service-Token"),
) -> None:
    expected = os.environ.get("DATAVIS_API_API_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="service authentication is not configured")
    if not hmac.compare_digest(x_service_token, expected):
        raise HTTPException(status_code=401, detail="invalid service credential")


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    try:
        settings = Settings.from_environment()
        load_datasets(settings.datasets_path)
    except Exception as error:
        raise HTTPException(status_code=503, detail="configuration is not ready") from error
    return {"status": "ready"}


@app.get("/v1/datasets", dependencies=[Depends(require_service_token)])
def list_datasets() -> list[dict[str, str]]:
    settings = Settings.from_environment()
    return [
        {"slug": item.slug, "title": item.title, "description": item.description}
        for item in load_datasets(settings.datasets_path).values()
    ]


@app.get("/v1/datasets/{slug}.csv", dependencies=[Depends(require_service_token)])
def dataset_csv(slug: str) -> Response:
    settings = Settings.from_environment()
    dataset = load_datasets(settings.datasets_path).get(slug)
    if dataset is None:
        raise HTTPException(status_code=404, detail="dataset is not published")
    try:
        cached, cache_status = cached_dataset_csv(settings, dataset)
    except ExportError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except Exception as error:
        logger.exception("Dataset export failed for %s", slug)
        raise HTTPException(status_code=502, detail="dataset refresh failed") from error
    return Response(
        content=cached.content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{slug}.csv"',
            "X-Datavis-Cache": cache_status,
            "X-Datavis-Generated-At": cached.generated_at.isoformat(),
        },
    )
