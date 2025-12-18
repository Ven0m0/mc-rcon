set shell := ["bash", "-euo", "pipefail", "-c"]

py := "python3"
uv := "uv"

default:
  @just --list

setup:
  {{uv}} sync --dev

fmt:
  {{uv}} run ruff format .

lint:
  {{uv}} run ruff check .

test:
  {{uv}} run pytest

type:
  {{uv}} run pyrefly check

build:
  {{uv}} run {{py}} -m build

clean:
  rm -rf dist build .pytest_cache .ruff_cache .mypy_cache .pyrefly .coverage htmlcov *.egg-info
