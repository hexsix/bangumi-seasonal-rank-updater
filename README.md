# bangumi-seasonal-rank-updater

## Install

install uv and init uv venv

```bash
uv venv .venv
```

activate venv

```bash
source .venv/bin/activate
```

install dependecies

```bash
# dev
uv pip install ".[dev]"

# product
uv sync --no-cache
```

create a minimal .env file

```env
BGMTV_TOKEN=123456
```

run app development

```bash
fastapi run app/main.py --port 8000 --reload
```

run app product

```bash
fastapi run app/main.py --port 8000 --worker 4
```
