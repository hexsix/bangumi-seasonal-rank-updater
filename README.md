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

## alembic

```bash
# check current
alembic current
# upgrade
alembic upgrade head
# downgrade
alembic downgrade
# drop alembic_version
docker exec postgres psql -U postgres -d rank -c "DROP TABLE IF EXISTS alembic_version;"
# check tables
docker exec postgres psql -U postgres -d rank -c "\dt"
```
