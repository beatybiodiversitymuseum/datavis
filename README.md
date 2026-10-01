# Datavis

Datavis hosts multiple public Streamlit applications at `https://apps.beatymuseum.ubc.ca/datavis`. Each application reads a reviewed CSV dataset from a private FastAPI service. The API maps a public dataset slug to a fixed numbered Specify saved query and uses `specify-client` for the authenticated Specify session, retries, rate limiting, and pagination.

The browser never receives Specify credentials, the private API URL, its service token, collection IDs, or query IDs. The API does not accept arbitrary query identifiers. This service is independent of the DwCA export pipeline and does not use `dwca-config` or Darwin Core mappings.

## Architecture

```text
browser -> nginx /datavis -> Streamlit (datavis)
                              -> private FastAPI (datavis-api)
                                   -> specify-client -> Specify saved query
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

Responses are bounded by `DATAVIS_MAX_CSV_ROWS` (100,000 by default). The backend rejects unlisted slugs and strips Specify's internal record ID from the CSV. Query headers come from the saved query's own displayed-field metadata; no Darwin Core transformation is performed.

## Production deployment

The repository exposes source artifacts and deploys only through `beatybiodiversitymuseum/ansible-deploy`:

```bash
cd /path/to/ansible-deploy
source .venv/bin/activate
ansible-playbook playbooks/deploy_app.yml -e app=datavis_api -e app_revision=<git-revision>
ansible-playbook playbooks/deploy_app.yml -e app=datavis -e app_revision=<git-revision>
```

Deploy `datavis_api` first. Its manifest is `backend/deploy/deployment.yml`; the public Streamlit manifest is `frontend/deploy/deployment.yml`. Production readiness is not established until matching controller inventory entries, secrets, allocations, nginx ingress, and a reviewed dataset have been added and both deployments pass.

Service logs:

```bash
journalctl -u datavis-api.service --since today --no-pager
journalctl -u datavis.service --since today --no-pager
```

The approved Beaty logo asset is intentionally not approximated in source; add the official horizontal logo when the asset is available. The current UI uses the approved Beaty red accent and documented local font fallbacks.
