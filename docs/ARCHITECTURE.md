# Architecture

## Purpose

`repo-templates-gen` is a Python package that generates GitHub issue forms, the issue chooser config and a pull request template from one JSON config, with schema checks and byte-exact YAML.

## Shape

```text
caller code or CLI
    |
    +-- repo_templates_gen.__init__ (public API)
    |       load_config -> TemplateConfig
    |       render_issue_form / render_pr_template / render_all -> str / dict[str, str]
    |       write_all -> files under a root Path
    |
    +-- repo_templates_gen.__main__ (argparse CLI)
```

- Public API: names in `__all__` of `src/repo_templates_gen/__init__.py`.
- Configuration model: frozen dataclasses `Field`, `IssueForm`, `ContactLink` and `TemplateConfig` validate their own invariants in `__post_init__`.
- Errors: validation and file-existence failures raise `TemplateError` with a stable `code`; `Field` also raises `ValueError` for an unknown field type.
- Side effects: `write_all` creates parent directories and writes UTF-8 files with LF line endings; the rest of the public API is pure string processing.
- Logging: the module logger uses a `NullHandler` and emits no messages.

## Quality contract

The supplied source tree contains no `scripts/check.py`, coverage configuration or CI workflow file. The executable contract is the public API and the pytest module `tests/test_repo_templates_gen.py`.

## Decisions

No ADR directory is included in the supplied source tree.
