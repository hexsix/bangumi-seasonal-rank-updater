import os
from typing import Dict

HEADER = "# Auto-generated season to bangumi index mapping\n# Format: DATA = {season_id: index_id}\n\nDATA = {\n}\n"


def _mapping_path() -> str:
    root_dir = os.path.dirname(os.path.dirname(__file__))
    mappings_dir = os.path.join(root_dir, "mappings")
    os.makedirs(mappings_dir, exist_ok=True)
    return os.path.join(mappings_dir, "season_to_index.py")


def load_mapping() -> Dict[int, int]:
    path = _mapping_path()
    if not os.path.exists(path):
        # initialize file
        with open(path, "w", encoding="utf-8") as f:
            f.write(HEADER)
        return {}
    # execute in isolated namespace
    ns: Dict[str, object] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        exec(compile(code, path, "exec"), ns, ns)
        data = ns.get("DATA")
        if isinstance(data, dict):
            # ensure int keys
            return {int(k): int(v) for k, v in data.items()}
        return {}
    except Exception:
        # if corrupted, reset
        return {}


def save_mapping(mapping: Dict[int, int]) -> None:
    path = _mapping_path()
    # sort by season id
    items = sorted(mapping.items())
    lines = [
        "# Auto-generated season to bangumi index mapping",
        "# Format: DATA = {season_id: index_id}",
        "",
        "DATA = {",
    ]
    for k, v in items:
        lines.append(f"    {k}: {v},")
    lines.append("}")
    content = "\n".join(lines) + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def upsert(season_id: int, index_id: int) -> None:
    data = load_mapping()
    if data.get(season_id) == index_id:
        return
    data[season_id] = index_id
    save_mapping(data)
