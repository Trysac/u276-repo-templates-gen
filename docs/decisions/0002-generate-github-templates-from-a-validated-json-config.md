# Generate GitHub templates from a validated JSON config

Status: accepted (generated, pending human review)

## Context

Maintainers need consistent issue forms, chooser config, and pull request template across repositories. Manual copying introduces errors (IDs with spaces, missing options, markdown-only forms) and inconsistent YAML quoting for labels with special characters.

## Decision

Implement a Python library that parses a JSON configuration, validates it thoroughly (size, depth, string lengths, uniqueness, URL scheme, field counts), and renders byte-exact YAML and Markdown using deterministic quoting (json.dumps with ensure_ascii=False). A CLI wraps the library for automation.

## Consequences

Repositories using this library get uniform, valid GitHub templates. The single source of truth simplifies maintenance and diffs. The library enforces strict validation to catch common mistakes early. PyYAML is used only as a dev dependency for round-trip tests; the runtime remains stdlib-only.
