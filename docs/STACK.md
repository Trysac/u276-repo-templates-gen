# Stack

## Used

| Tool | Why |
|---|---|
| Python >= 3.10 | Code uses `from __future__ import annotations`, `list[str] | None` and `tuple[str, ...]`. |
| Python standard library | `json`, `logging`, `re`, `dataclasses`, `pathlib`, `argparse`, `collections.abc` and `typing` cover config parsing, validation, rendering and the CLI; no runtime dependencies. |
| pytest | The test module uses `pytest.raises`. |
| PyYAML >=6,<7 | Development-only oracle for checking that rendered issue forms load as YAML. |

## Discarded

| Tool | Why not |
|---|---|
| PyYAML as a runtime dependency | Rendering uses `json.dumps` for YAML-compatible double-quoted scalars; PyYAML is only a test oracle. |
| Template repository copying | Replaced by one validated JSON source and deterministic rendering. |
