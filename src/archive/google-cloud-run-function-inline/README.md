# Cloud Run Function Inline Editor Files

Use these files when creating a Python HTTP function in the Google Cloud Run inline editor.

This is not the Streamlit UI. Cloud Run Functions run a request handler from `main.py`, so this bundle provides a simple upload form and returns the generated HTML report.

## Files to create in the editor

Create these files at the top level of the inline editor:

```text
main.py
requirements.txt
report.py
html_utils.py
preprocess.py
```

Copy the contents from this folder into the matching editor files.

## Cloud Run settings

- Runtime: Python 3.11
- Entry point: `apple_watch_health_report`
- Trigger: HTTP
- Authentication: your choice. For private health data, require authentication unless this is only a temporary test.
- Memory: 2 GiB or higher
- Timeout: 300 seconds or higher
Optional environment variables:

- `MAX_UPLOAD_BYTES`: defaults to `33554432`

## Important limits

Inline functions are convenient, but they are not ideal for large Apple Health exports. Multipart uploads are handled within one HTTP request and may hit request size, memory, or timeout limits. If your real `export.xml` is large, use the Docker/Cloud Run service approach instead.
