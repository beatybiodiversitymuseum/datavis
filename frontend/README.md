# Datavis Streamlit host

This component is the public multipage Streamlit application served below `/datavis`. It calls the private Datavis API from the server process using an Ansible-generated internal token; neither the API address nor token is sent to browser code.

Add visualization applications as numbered Python files under `pages/`. Reuse `datavis.ui.dataset_client()` and request a reviewed dataset slug. Never accept or forward query IDs, collection IDs, credentials, or arbitrary URLs.

See the repository-root [README](../README.md) for setup, validation, deployment, and application-authoring guidance. Deploy this component with the `datavis` controller key and `deploy/deployment.yml`.
