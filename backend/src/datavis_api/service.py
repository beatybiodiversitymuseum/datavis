"""HTTP application and bounded job entry point."""

import hmac
import logging
import os

import requests
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse

from .cache import (
    CachedCsv,
    atomic_cache_writer,
    dataset_lock,
    is_fresh,
    read_cached_csv,
)
from .config import Dataset, Settings, load_datasets
from .connections import get_specify_client
from .csv_export import ExportError, query_columns, write_query_csv
from .metadata import MetadataClient, MetadataError

app = FastAPI(title='Private allowlisted Specify query CSV API for Datavis applications')
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
    with dataset_lock(settings.state_dir, dataset.slug) as acquired:
        if not acquired:
            if cached is not None and allow_stale:
                return cached, "STALE"
            raise ExportError("a dataset export is already running")
        cached = read_cached_csv(settings.state_dir, dataset.slug)
        if not force and cached is not None and is_fresh(
            cached, settings.cache_ttl_seconds
        ):
            return cached, "HIT"
        try:
            with atomic_cache_writer(settings.state_dir, dataset.slug) as output:
                write_query_csv(get_specify_client(settings), dataset.query_id, output)
            refreshed = read_cached_csv(settings.state_dir, dataset.slug)
            assert refreshed is not None
            return refreshed, "MISS"
        except Exception:
            if cached is None or not allow_stale:
                raise
            logger.exception(
                "Dataset refresh failed; serving stale cache for %s", dataset.slug
            )
            return cached, "STALE"


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


@app.get(
    "/v1/datasets/{slug}/columns", dependencies=[Depends(require_service_token)]
)
def dataset_columns(slug: str) -> list[dict[str, str]]:
    settings = Settings.from_environment()
    dataset = load_datasets(settings.datasets_path).get(slug)
    if dataset is None:
        raise HTTPException(status_code=404, detail="dataset is not published")
    try:
        columns = query_columns(get_specify_client(settings), dataset.query_id)
        metadata = MetadataClient(
            settings.metadata_url,
            settings.specify_collection_id,
        )
        return [
            {
                "source": column.header,
                "label": metadata.column_label(column.string_id),
            }
            for column in columns
        ]
    except (ExportError, MetadataError, requests.RequestException) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/v1/datasets/{slug}.csv", dependencies=[Depends(require_service_token)])
def dataset_csv(slug: str) -> FileResponse:
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
    return FileResponse(
        path=cached.path,
        media_type="text/csv; charset=utf-8",
        filename=f"{slug}.csv",
        headers={
            "X-Datavis-Cache": cache_status,
            "X-Datavis-Generated-At": cached.generated_at.isoformat(),
        },
    )
