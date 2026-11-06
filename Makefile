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
# Every uv call goes through the vendored helper, which cleans the environment,
# uses the global uv cache, runs offline first and goes online at most once. See
# https://github.com/leynos/shared-actions/tree/main/uv_gate for the contract.
# The one exception is typos-config-builder at a release tag, which the spelling
# baseline requires to be called directly.
UV_GATE ?= python3 scripts/uv_gate.py
UV ?= uv
# The helper finds uv on PATH, so a caller's UV=/path/to/uv is honoured by putting
# that uv's directory first on PATH for every recipe.
export PATH := $(if $(findstring /,$(UV)),$(patsubst %/,%,$(dir $(UV))):)$(PATH)
# A UV given on the command line or in the environment must be uv itself or an executable
# file named uv: the helper finds uv on PATH by that name and would otherwise use another.
UV_SELECTION_CHECK := $(if $(filter command line environment,$(origin UV)),$(if $(filter uv,$(UV)),,$(if $(findstring /,$(UV)),$(if $(shell test -f '$(UV)' -a -x '$(UV)' && printf y),$(if $(filter uv,$(notdir $(UV))),,$(error UV=$(UV) must be named uv)),$(error UV=$(UV) is not an executable file)),$(error UV=$(UV) must be uv or a path to an executable file named uv))))



NODE_TOOLS = $(BIOME) $(TSC)
TOOLS = $(MDLINT) uv $(BUN)
VENV_TOOLS = pytest

# The CV-005 CodeScene contracts live in shared-actions and run from a full
# commit, so a fix is a pin bump. `.github/cv005.toml` holds this repository's
# only parameters.
CV005_CONTRACTS_REF ?= 88977798a5c3bae1549afb99642529488c665276
CV005_CONTRACTS = $(UV_GATE) tool --python 3.13 --from 'git+https://github.com/leynos/shared-actions@$(CV005_CONTRACTS_REF)\#subdirectory=packages/cv005-contracts' -- cv005-contracts

# One pinned ruff and one pinned ty for every gate. `uv tool install ruff`
# with no version is what turned main red: it followed upstream into a release
# whose noqa-comments rule rejected 59 suppressions the tree already carried,
# while the Makefile ran whichever ruff happened to be on PATH.
RUFF_VERSION ?= 0.15.20
TY_VERSION ?= 0.0.78
TYPOS_CONFIG_BUILDER_VERSION ?= v0.1.3
TYPOS_CONFIG_BUILDER = $(UV) tool run --python 3.14 --from \
	"git+https://github.com/leynos/typos-config-builder.git@$(TYPOS_CONFIG_BUILDER_VERSION)" \
	typos-config-builder
RUFF = $(UV_GATE) tool --from ruff@$(RUFF_VERSION) -- ruff
TY = $(UV_GATE) tool --from ty@$(TY_VERSION) -- ty

.PHONY: prepare help all clean build build-release lint fmt check-fmt markdownlint \
        nixie spelling test typecheck $(TOOLS) $(VENV_TOOLS) test-workflow-contracts

prepare: ## Install the locked development environment, offline first
	$(UV_GATE) prepare --group dev
.PHONY: $(NODE_TOOLS)

.DEFAULT_GOAL := all

test-workflow-contracts: ## Check the CV-005 CodeScene workflow contracts
	$(CV005_CONTRACTS) check --repository .

all: check-fmt lint typecheck test spelling test-workflow-contracts

build: uv prepare ## Build virtual-env and install deps

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
	@$(UV_GATE) run -- which $(1) >/dev/null 2>&1 || { \
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
$(VENV_TOOLS): prepare ## Verify required CLI tools in venv
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

test: build node_modules uv $(VENV_TOOLS) test-workflow-contracts ## Run tests
	$(UV_GATE) run -- pytest -v -n auto
	$(BUN) test

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS=":"; printf "Available targets:\n"} {printf "  %-20s %s\n", $$1, $$2}'
