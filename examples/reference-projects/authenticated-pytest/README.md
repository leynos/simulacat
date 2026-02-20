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
   SIMULACAT_JS_ROOT="$(python -c 'from simulacat.orchestration import sim_package_root; print(sim_package_root())')"

   bun install --cwd "${SIMULACAT_JS_ROOT}"
   ```

3. Run tests:

   ```bash
   pytest -v tests
   ```

## Continuous integration (CI)

The workflow in `.github/workflows/ci.yml` demonstrates authenticated reference
usage in GitHub Actions with Python + Node.js toolchain setup.
