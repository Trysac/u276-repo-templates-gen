# repo-templates-gen

[![PyPI version](https://img.shields.io/pypi/v/trysac-repo-templates-gen)](https://pypi.org/project/trysac-repo-templates-gen/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-repo-templates-gen)](LICENSE)
[![CI](https://github.com/Trysac/u276-repo-templates-gen/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u276-repo-templates-gen/actions/workflows/ci.yml)

Generate GitHub issue forms, the issue chooser config and a pull request template from one JSON config, with schema checks and byte-exact YAML

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-repo-templates-gen
# or
uv add trysac-repo-templates-gen
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import repo_templates_gen

# normalize() trims surrounding whitespace and lower-cases the text.
print(repo_templates_gen.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    repo_templates_gen.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
