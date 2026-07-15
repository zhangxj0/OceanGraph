# Contributing to OceanGraph

Thank you for helping improve OceanGraph-R1.

## Development setup

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

Copy an example configuration without placing credentials in the file:

```bash
cp configs/oceangraph.yaml.example config.yaml
```

Provide API keys through environment variables such as
`PARATERA_API_KEY` and `DEEPSEEK_API_KEY`.

## Source layout

- `src/oceangraph/`: public API, engine, retrieval, generation, and verification
- `configs/`: versioned configuration examples without secrets
- `scripts/`: dataset preparation and Search-R1 conversion helpers
- `tests/`: focused regression tests
- `run_oceangraph.py`: source-checkout command-line entry point

The package has one canonical namespace: `oceangraph`. Do not add parallel
compatibility packages or duplicate environment-variable prefixes.

## Quality checks

Run the focused checks before submitting a change:

```bash
python -m compileall -q src scripts tests run_oceangraph.py
python -m pytest -q
python run_oceangraph.py --help
```

Keep changes focused, update user-facing documentation, and add tests for new
behavior. Never commit API keys, server credentials, local `config.yaml`, or
generated data under `data/`, `output/`, or `tmp/`.

## License

Contributions are licensed under the Apache License 2.0.
