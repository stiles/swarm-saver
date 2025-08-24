# swarm-saver

Export your Swarm check-ins to NDJSON, CSV and GeoJSON.

## Prerequisites

- Python 3.10+
- uv installed (see the [uv docs](https://docs.astral.sh/uv/))

## How to install

```bash
uv sync
```

This installs dependencies from `pyproject.toml` and `uv.lock` into `.venv/`.

## Usage

1) Set your Foursquare API token

```bash
export FOURSQUARE_TOKEN="<your_token>"
# or create a .env file in the project root:
# FOURSQUARE_TOKEN=<your_token>
```

2) Run the exporter

```bash
uv run ./export_swarm.py
# or
uv run python export_swarm.py
```

The script writes these files:

- `data/checkins.ndjson`
- `data/checkins.csv`
- `data/checkins.geojson`

## Notes

- The script paginates using the API page size and sleeps briefly between requests
- If you get 401 errors check `FOURSQUARE_TOKEN`
- Check-ins without coordinates do not appear in the GeoJSON output

## Environment variables

- Environment variables are loaded from the process and an optional `.env` file via `python-dotenv`
- Example file is provided as `.env.example`

## Development

- Add a dependency: `uv add <package>`
- Export a requirements file:
  - `uv export -o requirements.txt` (if available in your uv version)
  - or `uv pip freeze > requirements.txt`
- Python version is pinned in `.python-version`
