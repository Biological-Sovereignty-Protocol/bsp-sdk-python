# Contributing to BSP Python SDK

Thanks for your interest in contributing to the Biological Sovereignty Protocol Python SDK.

## Prerequisites

- Python `>=3.10`
- Git
- (Optional) [uv](https://github.com/astral-sh/uv) for fast env management

## Local setup (venv + pip)

```bash
git clone https://github.com/Biological-Sovereignty-Protocol/bsp-sdk-python.git
cd bsp-sdk-python
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Local setup (uv — recommended)

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev,docs]"
```

The `uv` path automatically applies the `ecdsa>=0.19.2` override defined in `pyproject.toml` (see `SECURITY.md` for context).

## Run tests

```bash
pytest
pytest --cov=bsp_sdk --cov-report=term-missing
```

## Lint & type-check

```bash
ruff check .
mypy bsp_sdk
```

## Build documentation

Install optional docs extras and build with Sphinx:

```bash
pip install -e ".[docs]"
sphinx-build docs docs/_build
```

Then open `docs/_build/index.html`. The `_build/` folder is git-ignored.

## Run examples

Runnable examples live in `examples/`:

```bash
python examples/01_create_beo.py
python examples/02_grant_consent.py
python examples/03_submit_biorecord.py
python examples/04_destroy_beo.py
```

Without `BSP_RELAYER_URL` set, examples run in simulated mode.

## Code style

- Ruff enforces formatting (line-length 100, target py310).
- Public APIs must have type hints. The project is `mypy --strict` clean.
- Google-style or NumPy-style docstrings on all public functions/classes (picked up by Sphinx Napoleon).
- Names follow PEP 8: `snake_case` for functions/variables, `PascalCase` for classes.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(access): add batch revoke API
fix(crypto): validate Ed25519 signature length
docs(sdk-python): expand BEOClient usage examples
```

## Pull requests

1. Fork or branch from `main`: `git checkout -b feat/my-thing`.
2. Add or update tests. New public functions must ship with coverage.
3. Run `pytest && ruff check . && mypy bsp_sdk` locally before pushing.
4. Update `CHANGELOG.md` under the `[Unreleased]` section.
5. Open a PR against `main` with a clear summary and link to any related issue.
6. Be responsive to review feedback.

## Security

Do **not** file public issues for security vulnerabilities. See `SECURITY.md` for private disclosure instructions.

## License

By contributing you agree that your contributions are licensed under the project's Apache-2.0 license.
