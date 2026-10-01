# Datavis private API

This component exposes only two token-authenticated contracts to the server-side Streamlit host:

- `GET /v1/datasets` lists reviewed public dataset metadata.
- `GET /v1/datasets/{slug}.csv` returns the 24-hour cached CSV for the fixed
  Specify saved query mapped to that slug, refreshing when necessary and
  retaining the last successful copy during a temporary upstream failure.

It also exposes unauthenticated liveness and readiness at `/health/live` and `/health/ready`. Dataset slugs and query IDs are owned by `config/datasets.yaml`; callers cannot submit query IDs, collection IDs, or remote URLs. Specify authentication and transport belong to the released `specify-client` package.

See the repository-root [README](../README.md) for setup, validation, deployment, configuration, and security boundaries. Deploy this component with the `datavis_api` controller key and `deploy/deployment.yml`.
