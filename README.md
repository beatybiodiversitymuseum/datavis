# Datavis

Datavis hosts multiple public Streamlit applications at `https://apps.beatymuseum.ubc.ca/datavis`. Each application reads a reviewed CSV dataset from a private FastAPI service. The API maps a public dataset slug to a fixed numbered Specify saved query and uses `specify-client` for the authenticated Specify session, retries, rate limiting, and pagination.

The browser never receives Specify credentials, the private API URL, its service token, collection IDs, or query IDs. The API does not accept arbitrary query identifiers. This service is independent of the DwCA export pipeline and does not use `dwca-config` or Darwin Core mappings.

## Architecture

```text
browser -> nginx /datavis -> Streamlit (datavis)
                              -> private FastAPI (datavis-api)
                                   -> specify-client -> Specify saved query
                                   -> specify-metadata-service -> localized field labels
```

- `frontend/`: public multipage Streamlit host. Add one file under `pages/` for each visualization application and reuse `datavis.ui.dataset_client()`.
- `backend/`: private, token-authenticated CSV API and source-controlled dataset allowlist.
- `backend/config/datasets.yaml`: the only mapping from public slugs to saved query numbers. Empty by default so no collection data is accidentally published.

## Publishing a dataset and app

1. Review the saved query's displayed fields and results for public release.
2. Add a stable slug, title, description, and positive `query_id` under `datasets` in `backend/config/datasets.yaml`.
3. Add a Streamlit page under `frontend/pages/`. Request only the slug, never a query number, and use the returned DataFrame for visualization.
4. Add focused tests and run the validation commands below.

## Local development

Python 3.11+, Git, and access to the `specify-client` dependency are required. Configure backend and frontend separately:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r runtime-requirements.lock
python -m pip install --no-build-isolation --no-deps -e .
cp .env.example .env
set -a; source .env; set +a
datavis-api serve
```

In another terminal:

```bash
cd frontend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r runtime-requirements.lock
python -m pip install --no-build-isolation --no-deps -e .
cp .env.example .env
set -a; source .env; set +a
datavis serve
```

Open `http://127.0.0.1:8501/datavis/`. The local backend `.env` requires a reviewed Specify account and collection ID. Never commit `.env`.

Complete validation from the repository root:

```bash
python3 ../service-creator/skills/create-api-service/scripts/validate_api_service.py backend
python3 ../service-creator/skills/create-service/scripts/validate_service.py frontend
python -m pytest backend/tests frontend/tests
git diff --check
```

## Configuration and security

The controller supplies externally managed `SPECIFY_USERNAME` and `SPECIFY_PASSWORD` to `datavis_api`. It allocates `SPECIFY_COLLECTION_ID`, both loopback ports, and the private backend URL. Ansible generates one internal `datavis_api_api_token` and maps it to `DATAVIS_API_API_TOKEN` in the backend and `DATAVIS_BACKEND_TOKEN` in the frontend.

The backend does not impose a row limit: the reviewed saved query controls the result size as well as its displayed fields and order. The backend rejects unlisted slugs, strips Specify's internal record ID, validates unique headers and row widths, and writes each result directly to an atomic disk cache without assembling the CSV in memory. No Darwin Core transformation is performed.

Query Explorer obtains collection-specific table, relationship, field, and
tree-rank labels from `specify-metadata-service`; Datavis does not embed or
infer Specify schema labels. If that dependency is temporarily unavailable,
the CSV remains usable and Query Explorer explicitly falls back to the saved
query names.

The backend keeps the last successful CSV for each dataset under
`/var/lib/datavis-api/cache`. Cached data is fresh for 24 hours, controlled by
`DATAVIS_CACHE_TTL_SECONDS=86400`. Requests refresh expired data synchronously
and fall back to the last successful CSV when Specify is temporarily
unavailable. Response headers report `X-Datavis-Cache` as `HIT`, `MISS`, or
`STALE` and include `X-Datavis-Generated-At`. A systemd timer refreshes every
published dataset nightly at 03:15 America/Vancouver with up to 30 minutes of
random delay; timer failures remain visible to operators while the prior cache
is preserved.

Refreshes use a per-dataset filesystem lock shared by the API and nightly
refresh process. The prior cache remains active until a complete replacement
has been flushed to disk and atomically installed. Streamlit downloads the CSV
to a temporary file before pandas parses it, avoiding a second complete
in-memory response buffer.

## Production deployment

The backend exposes a controller-built offline wheelhouse, the frontend exposes
a source artifact, and both deploy only through
`beatybiodiversitymuseum/ansible-deploy`:

```bash
cd /path/to/ansible-deploy
source .venv/bin/activate
./deploy datavis_api <git-revision>
./deploy datavis <git-revision>
```

Deploy `datavis_api` first. Its manifest is `backend/deploy/deployment.yml`; the public Streamlit manifest is `frontend/deploy/deployment.yml`. Production readiness is not established until matching controller inventory entries, secrets, allocations, nginx ingress, and a reviewed dataset have been added and both deployments pass.

Service logs:

```bash
journalctl -u datavis-api.service --since today --no-pager
journalctl -u datavis-api-cache-refresh.service --since today --no-pager
systemctl status datavis-api-cache-refresh.timer
journalctl -u datavis.service --since today --no-pager
```

The approved Beaty logo asset is intentionally not approximated in source; add the official horizontal logo when the asset is available. The current UI uses the approved Beaty red accent and documented local font fallbacks.
