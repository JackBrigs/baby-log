# Project Workflow

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
source .venv/bin/activate
python -m baby_log.bot
```

## Test

```bash
source .venv/bin/activate
PYTHONPATH=src pytest tests/ -v
```

## Lint and Format

```bash
source .venv/bin/activate
ruff check --fix src/ tests/
ruff format src/ tests/
```

## Type Check

```bash
source .venv/bin/activate
mypy src/
```