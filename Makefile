MDLINT ?= markdownlint-cli2
# `make fmt` and `make check-fmt` call mdtablefix directly. `--git` selects the
# Markdown files Git tracks and `--include-untracked` adds the untracked files
# Git does not ignore, so a new document is formatted before it is staged.
# Both modes need mdtablefix 0.6.0 or later; CI pins the version at the
# install-mdtablefix step.
MDTABLEFIX ?= mdtablefix
MDTABLEFIX_SELECT = --git --include-untracked
MDTABLEFIX_RULES = --wrap --renumber --breaks --ellipsis --fences
NIXIE ?= nixie
BIOME ?= ./node_modules/.bin/biome
TSC ?= ./node_modules/.bin/tsc
BUN ?= bun
UV ?= uv
NODE_TOOLS = $(BIOME) $(TSC)
TOOLS = $(MDLINT) uv $(BUN)
VENV_TOOLS = pytest
UV_ENV = UV_CACHE_DIR=.uv-cache UV_TOOL_DIR=.uv-tools
# One pinned ruff and one pinned ty for every gate. `uv tool install ruff`
# with no version is what turned main red: it followed upstream into a release
# whose noqa-comments rule rejected 59 suppressions the tree already carried,
# while the Makefile ran whichever ruff happened to be on PATH.
RUFF_VERSION ?= 0.15.20
TY_VERSION ?= 0.0.78
TYPOS_CONFIG_BUILDER_VERSION ?= v0.1.3
TYPOS_CONFIG_BUILDER = $(UV_ENV) $(UV) tool run --python 3.14 --from \
	"git+https://github.com/leynos/typos-config-builder.git@$(TYPOS_CONFIG_BUILDER_VERSION)" \
	typos-config-builder
RUFF = $(UV_ENV) $(UV) tool run ruff@$(RUFF_VERSION)
TY = $(UV_ENV) $(UV) tool run ty@$(TY_VERSION)

.PHONY: help all clean build build-release lint fmt check-fmt markdownlint \
        nixie spelling test typecheck $(TOOLS) $(VENV_TOOLS)
.PHONY: $(NODE_TOOLS)

.DEFAULT_GOAL := all

all: check-fmt lint typecheck test spelling

.venv: pyproject.toml
	$(UV_ENV) uv venv --clear

build: uv .venv ## Build virtual-env and install deps
	$(UV_ENV) uv sync --group dev

build-release: ## Build artefacts (sdist & wheel)
	python -m build --sdist --wheel

node_modules: package.json bun.lock
	$(call ensure_tool,$(BUN))
	$(BUN) install

clean: ## Remove build artefacts
	rm -rf build dist *.egg-info \
	  .mypy_cache .pytest_cache .coverage coverage.* \
	  lcov.info htmlcov .venv .uv-cache .uv-tools
	find . -type d -name '__pycache__' -print0 | xargs -0 -r rm -rf

define ensure_tool
	@command -v $(1) >/dev/null 2>&1 || { \
	  printf "Error: '%s' is required, but not installed\n" "$(1)" >&2; \
	  exit 1; \
	}
endef

define ensure_tool_venv
	@$(UV_ENV) uv run which $(1) >/dev/null 2>&1 || { \
	  printf "Error: '%s' is required in the virtualenv, but is not installed\n" "$(1)" >&2; \
	  exit 1; \
	}
endef

ifneq ($(strip $(TOOLS)),)
$(TOOLS): ## Verify required CLI tools
	$(call ensure_tool,$@)
endif

ifneq ($(strip $(NODE_TOOLS)),)
$(NODE_TOOLS): node_modules ## Verify required CLI tools installed via Bun
	$(call ensure_tool,$@)
endif


ifneq ($(strip $(VENV_TOOLS)),)
.PHONY: $(VENV_TOOLS)
$(VENV_TOOLS): ## Verify required CLI tools in venv
	$(call ensure_tool_venv,$@)
endif

fmt: $(BIOME) ## Format sources
	$(BIOME) check . --write
	$(RUFF) format
	$(RUFF) check --select I --fix
	$(MDTABLEFIX) --in-place $(MDTABLEFIX_SELECT) $(MDTABLEFIX_RULES)
	@unset FORCE_COLOR; $(MDLINT) --fix "**/*.md"

check-fmt: $(BIOME) ## Verify formatting
	$(BIOME) check .
	$(RUFF) format --check
	$(MDTABLEFIX) --check $(MDTABLEFIX_SELECT) $(MDTABLEFIX_RULES)

lint: $(BIOME) ## Run linters
	$(RUFF) check
	$(BIOME) lint .

typecheck: build $(TSC) ## Run typechecking
	$(TY) --version
	$(TY) check
	$(TSC) --noEmit

markdownlint: spelling $(MDLINT) ## Lint Markdown files and enforce spelling
	$(MDLINT) '**/*.md'

spelling: ## Enforce en-GB-oxendict spelling and shared phrase corrections
	$(TYPOS_CONFIG_BUILDER) gate --repository .





nixie: ## Validate Mermaid diagrams
	$(call ensure_tool,$(NIXIE))
	$(NIXIE) --no-sandbox

test: build node_modules uv $(VENV_TOOLS) ## Run tests
	$(UV_ENV) uv run pytest -v -n auto
	$(BUN) test

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS=":"; printf "Available targets:\n"} {printf "  %-20s %s\n", $$1, $$2}'
