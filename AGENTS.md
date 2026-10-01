# Repository instructions

- Preserve the split trust boundary: browsers talk only to Streamlit; only the private API holds Specify credentials.
- Never accept a query ID, collection ID, URL, or credentials from a browser. Publish datasets only through `backend/config/datasets.yaml` after reviewing every displayed field for public disclosure.
- Use the released `specify-client` for authentication, retries, rate limits, collection context, and pagination. This repository owns CSV formatting and the public dataset allowlist; it does not own Darwin Core behavior.
- Keep backend and frontend deployment manifests independent and reuse the logical generated secret `datavis_api_api_token` in both.
- Deploy only through `ansible-deploy`; never add checkout-based deploy scripts.
- Run both test suites, both Service Creator validators, and `git diff --check` before committing.
