SHELL := /usr/bin/env bash
.ONESHELL:
.SHELLFLAGS := -euo pipefail -c

PY ?= python3
UV ?= uv

.PHONY: help
help:
	@printf '%s\n' \
	  'Targets:' \
	  '  setup        - install dev deps with uv' \
	  '  fmt          - ruff format' \
	  '  lint         - ruff check' \
	  '  test         - pytest' \
	  '  type         - pyrefly check (if configured)' \
	  '  build        - build sdist+wheel (PEP517)' \
	  '  clean        - remove build artifacts'

.PHONY: setup
setup:
	$(UV) sync --dev

.PHONY: fmt
fmt:
	$(UV) run ruff format .

.PHONY: lint
lint:
	$(UV) run ruff check .

.PHONY: test
test:
	$(UV) run pytest

.PHONY: type
type:
	@# Only runs if pyrefly is available in the env.
	$(UV) run pyrefly check

.PHONY: build
build:
	$(UV) run $(PY) -m build

.PHONY: clean
clean:
	rm -rf dist build .pytest_cache .ruff_cache .mypy_cache .pyrefly .coverage htmlcov *.egg-info
