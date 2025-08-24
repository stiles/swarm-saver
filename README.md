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

1) Set your [Foursquare API token](https://docs.foursquare.com/developer/reference/personalization-apis-authentication)

```bash
export FOURSQUARE_TOKEN="<your_token>"
# or create a .env file in the project root:
# FOURSQUARE_TOKEN=<your_token>
```

2) (Optional) Configure S3 upload

Set these if you want the outputs uploaded to S3 after they are written locally:

```bash
# destination bucket
export S3_BUCKET="stilesdata.com"

# optional path/prefix inside the bucket
export S3_PREFIX="data/swarm"

# choose a profile (uses AWS_PROFILE, MY_PERSONAL_PROFILE, or AWS_DEFAULT_PROFILE)
export AWS_PROFILE="haekeo"
export AWS_REGION="us-east-1"  # or your preferred region
```

3) Run the exporter

```bash
uv run ./export_swarm.py
# or
uv run python export_swarm.py
```

The script writes these files:

- `data/checkins.ndjson`
- `data/checkins.csv`
- `data/checkins.geojson`

If S3 is configured, the same filenames are uploaded to `s3://$S3_BUCKET/$S3_PREFIX/`.

If your AWS credentials are via SSO and you see ExpiredToken errors, run:

```bash
aws sso login --profile "$AWS_PROFILE"
```

## Notes

- The script paginates using the API page size and sleeps briefly between requests
- If you get 401 errors check `FOURSQUARE_TOKEN`
- Check-ins without coordinates do not appear in the GeoJSON output

## Environment variables

- Environment variables are loaded from the process and an optional `.env` file via `python-dotenv`
- Example file is provided as `.env.example`
 - S3 settings are optional: `S3_BUCKET`, `S3_PREFIX` (or `S3_PATH`), and one of `AWS_PROFILE`, `MY_PERSONAL_PROFILE`, or `AWS_DEFAULT_PROFILE`

## Development

- Add a dependency: `uv add <package>`
- Export a requirements file:
  - `uv export -o requirements.txt` (if available in your uv version)
  - or `uv pip freeze > requirements.txt`
- Python version is pinned in `.python-version`
