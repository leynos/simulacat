# authenticated-pytest reference project

This reference project shows a minimal pytest suite that uses simulacat with
token metadata and verifies the configured Authorization header.

## Toolchain requirements

- Python 3.12 or later
- Node.js 20.x or 22.x
- Bun 1.2 or later

## Install and run locally

1. Install Python dependencies:

   ```bash
   python -m pip install "pytest>=9.0.0,<10.0.0" "simulacat>=0.1.0,<0.2.0"
   ```

2. Install simulator JavaScript dependencies from the installed simulacat
   package:

   ```bash
   SIMULACAT_JS_ROOT="$(python - <<'PY'
   from simulacat.orchestration import sim_entrypoint

   entrypoint = sim_entrypoint()
   for candidate in (entrypoint.parent, entrypoint.parent.parent):
       if (candidate / "package.json").is_file():
           print(candidate)
           break
   else:
       raise SystemExit("Unable to locate simulacat package.json")
   PY
   )"

   bun install --cwd "${SIMULACAT_JS_ROOT}"
   ```

3. Run tests:

   ```bash
   pytest -v tests
   ```

## CI

The workflow in `.github/workflows/ci.yml` demonstrates authenticated reference
usage in GitHub Actions with Python + Node.js toolchain setup.
