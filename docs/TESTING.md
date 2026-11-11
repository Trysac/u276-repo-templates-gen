# Testing

## Running

```sh
pytest tests/test_repo_templates_gen.py
```

The tests import the public package as `repo_templates_gen`; install the project or put `src` on `PYTHONPATH` before running them.

## Policy

- Tests exercise the public API and assert returned strings, raised `TemplateError` codes and CLI exit codes.
- Tests are deterministic and use temporary directories for `write_all` checks.
- No coverage threshold or gate script is present in the supplied source tree.

## Test module

`tests/test_repo_templates_gen.py` is the test module (a compiled pytest cache artifact is present under `tests/__pycache__/`). The visible test functions cover:
- `test_field_invalid_id_raises_template_error` — a field id containing invalid characters raises `TemplateError` with code `invalid_id`.
- `test_field_markdown_with_id_raises_invalid_id` — a markdown field with an id raises `invalid_id`.
- `test_field_non_markdown_empty_label_raises_invalid_config` — a non-markdown field with an empty label raises `invalid_config`.
- `test_field_markdown_empty_value_raises_invalid_config` — a markdown field with an empty value raises `invalid_config`.
- `test_field_dropdown_empty_options_raises_invalid_options` — a dropdown without options raises `invalid_options`.
- `test_field_dropdown_duplicate_options_raises_invalid_options` — duplicate dropdown options raise `invalid_options`.
- `test_field_dropdown_reserved_none_option_raises_invalid_options` — the reserved option `None` raises `invalid_options`.
- `test_field_checkboxes_similar_validation` — checkboxes apply the same option validation as dropdowns.

The compiled module also contains tests for duplicate form identifiers; the source file is the authority for the complete list.

## Layout

There is one test module, `tests/test_repo_templates_gen.py`. No `tests/conftest.py` is present in the supplied source tree.
