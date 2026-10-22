# Repository instructions

- Preserve the split trust boundary: browsers talk only to Streamlit; only the private API holds Specify credentials.
- Never accept a query ID, collection ID, URL, or credentials from a browser. Publish datasets only through `backend/config/datasets.yaml` after reviewing every displayed field for public disclosure.
- Use the released `specify-client` for authentication, retries, rate limits, collection context, and pagination. This repository owns CSV formatting and the public dataset allowlist; it does not own Darwin Core behavior.
- Keep backend and frontend deployment manifests independent and reuse the logical generated secret `datavis_api_api_token` in both.
- Deploy only through `ansible-deploy`; never add checkout-based deploy scripts.
- Run both test suites, both Service Creator validators, and `git diff --check` before committing.

## Saved-query columns in Streamlit

- Treat a Specify export supplied for review as evidence of values and approved displayed fields, not as the schema of the API CSV. `backend/src/datavis_api/csv_export.py` names API columns from each saved-query field's `columnalias`, then `title`, then `stringid`; these can differ from the export's display headings.
- For a page that needs particular fields, fetch `DatasetClient.column_labels(slug)` alongside `DatasetClient.dataframe(slug)`. The private API's `/v1/datasets/{slug}/columns` endpoint uses `specify-metadata-service` to map each API source header to a collection-specific display label. Resolve field roles from that mapping and keep the original source headers when selecting DataFrame columns. Do not hardcode or infer localized Specify labels from `stringid` paths.
- Treat missing or ambiguous required fields, or unavailable metadata needed to identify them, as explicit page errors. Do not silently select a different field. Keep query IDs, collection IDs, and private service details out of browser-facing errors.
- Test with the API shape: source headers in the DataFrame plus a separate source-to-label mapping. A test using only a manually exported CSV with display headings will miss this integration boundary.

## Files shipped with frontend code

- A Streamlit page may run with `datavis` installed in `site-packages`, so do not locate runtime data relative to the source checkout. Put required assets under `frontend/src/datavis/`, include them in `frontend/pyproject.toml` package data, and resolve them relative to the installed module.
- For a new packaged asset, build a frontend wheel and verify that it contains the asset and that code loaded from the extracted wheel can read it. A source-tree test alone does not establish that the deployed app can find the file.

## Public-facing copy

- Write for visitors using the app. Explain what the records, controls, and maps show. Do not call a page a teaching example, worked example, reviewed query, or Streamlit demonstration in the finished interface. Keep query IDs, deployment steps, service names, and troubleshooting details in operator documentation and logs rather than visitor-facing errors.
