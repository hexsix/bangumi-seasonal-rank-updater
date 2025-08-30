# rank-completion

Script to fetch the highest-ranked anime poster per season (quarter) from rinshankaiho API.

## Prerequisites
- Python 3.13+
- Install dependencies:

```bash
pip install .
# or
pip install -e .
```

## Fetch top posters by season
Primary API endpoints used are:
- Season detail (ranked subjects): https://api.rinshankaiho.fun/api/v0/season/{season_id}
  - Example: https://api.rinshankaiho.fun/api/v0/season/200001
  - The response contains a `subjects` list already sorted by rank; `subjects[0]` is the target.
- Available seasons list: https://api.rinshankaiho.fun/api/v0/season/available
  - Returns `{ "current_season_id": <int>, "available_seasons": [<int>, ...] }`.

Run the script:

- Provide explicit season IDs and choose an output file:
```bash
python -m app.fetch_top_posters 201204 201207 -o posters_sample.json
```

- By default (no season IDs), the script fetches the seasons from `/season/available` and writes to `mappings/posters_by_season.json`:
```bash
python -m app.fetch_top_posters
```
The `mappings` directory will be created automatically if it doesn't exist.

- Optionally, discover season IDs from existing `done/*.json` files instead of `/season/available`:
```bash
python -m app.fetch_top_posters --source done
```

### Output
A JSON mapping from season_id to poster URL, e.g.:
```json
{
  "201204": "https://lain.bgm.tv/pic/cover/l/cd/38/27364_1ZFmr.jpg",
  "201207": "https://lain.bgm.tv/pic/cover/l/41/39/26449_G0Xzx.jpg"
}
```
Note: JSON keys are strings when saved; the logical mapping is {season_id(int): url(str)}.

### Fallbacks
The script prefers `images_large` then `images_grid` from the top subject. If missing, it will attempt nested `images.large` or `images.grid`.

### Logging
The script uses `loguru` for concise logs.
