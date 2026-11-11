# repo-templates-gen

[![PyPI version](https://img.shields.io/pypi/v/trysac-repo-templates-gen)](https://pypi.org/project/trysac-repo-templates-gen/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-repo-templates-gen)](LICENSE)
[![CI](https://github.com/Trysac/u276-repo-templates-gen/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u276-repo-templates-gen/actions/workflows/ci.yml)

Generate GitHub issue forms, the issue chooser config and a pull request template from one JSON config, with schema checks and byte-exact YAML

## Problem

Maintainers copy issue templates between repositories by hand and break them: an id with a space, a dropdown without options or a form with only markdown makes GitHub silently fall back to a blank issue. Writing YAML by hand also mangles labels containing colons or hashes. This library renders the three `.github` files from one validated JSON config, with deterministic quoting, so every repository gets the same working templates.

## Install

```sh
pip install trysac-repo-templates-gen
```

Requires Python 3.10 or newer. The package has no runtime dependencies; PyYAML is used only by the test suite to check rendered YAML.

## Usage

```python
from pathlib import Path
from repo_templates_gen import load_config, render_all, write_all

config = load_config(Path("templates.json").read_text(encoding="utf-8"))
write_all(render_all(config), Path("."))
```

Run the module entry point as `python -m repo_templates_gen --config templates.json --out .`; add `--force` to overwrite existing files. It exits `0` on success, `1` on a `TemplateError` and `2` on usage or file-read/write errors.

## Public API

`load_config(text: str, *, max_bytes: int = 262_144) -> TemplateConfig` parses and validates a JSON string. `render_issue_form(form: IssueForm) -> str` renders one issue form to YAML. `render_pr_template(sections: Sequence[str], checklist: Sequence[str] = ()) -> str` renders Markdown. `render_all(config: TemplateConfig) -> dict[str, str]` returns the three output paths. `write_all(files: Mapping[str, str], root: Path, *, overwrite: bool = False) -> None` checks every target first and raises `TemplateError("file_exists", path)` before writing anything if a file exists and `overwrite` is false.

The dataclasses are `Field`, `IssueForm`, `ContactLink` and `TemplateConfig`. `Field` supports types `markdown`, `input`, `textarea`, `dropdown` and `checkboxes`; non-markdown fields need a non-empty `label`, markdown fields need a non-empty `value`, and dropdown/checkboxes need non-empty distinct `options` without the reserved string `None`. A form must have a slug matching `^[a-z0-9-]{1,64}$`, non-empty name and description, at least one non-markdown field, and unique ids and labels. Contact link URLs must start with `https://`.

Errors are `TemplateError` with a stable `code`: `config_too_large`, `invalid_config`, `invalid_slug`, `invalid_id`, `duplicate_id`, `duplicate_label`, `no_input_field`, `invalid_options`, `invalid_url`, `too_many_fields` or `file_exists`. Message text is truncated to 200 characters.

Limits: the config is at most 262,144 UTF-8 bytes, JSON nesting depth is at most 16, there are at most 20 forms and 30 fields per form, and every string is at most 1,000 characters.

## Why not copying a template repository

Copying a template repository gives many repositories a hand-maintained copy that drifts. This utility keeps one validated JSON source of truth and produces deterministic output that diffs cleanly across repositories.

## Documentation

- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md), [architecture](docs/ARCHITECTURE.md) and [stack](docs/STACK.md)
- [Security policy](docs/SECURITY.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
