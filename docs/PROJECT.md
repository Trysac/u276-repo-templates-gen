# Project record

## Objective

Generate GitHub issue forms, the issue chooser config and a pull request template from one JSON config, with schema checks and byte-exact YAML.

## Scope

In scope:
- Validating a JSON configuration with `load_config`, including size, depth, string-length, identifier, uniqueness, option and URL rules.
- Rendering `.github/ISSUE_TEMPLATE/<slug>.yml`, `.github/ISSUE_TEMPLATE/config.yml` and `.github/pull_request_template.md` from `TemplateConfig`.
- Writing those files under a caller-supplied root with optional overwrite, through `write_all`.
- A module entry point that reads `--config`, writes to `--out` and supports `--force`.
- The public dataclasses and functions listed in [README.md](../README.md).

Out of scope:
- Legacy Markdown issue templates.
- Discussion forms.
- Reading existing YAML.
- GitHub API calls.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 549422 / 62247 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.1370 |

## Factory run u276 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-11 | generation | deepseek-v4-pro | yes | 2214 | 22320 | 0 | 3328 | 0.0457 |
| 2026-11-11 | fix-1 | deepseek-v4-pro | no | 19433 | 9415 | 0 | 147200 | 0.0347 |
| 2026-11-11 | fix-2 | deepseek-v4-pro | no | 11060 | 1896 | 0 | 28416 | 0.0117 |
| 2026-11-11 | audit | deepseek-flash | no | 16372 | 13075 | 0 | 145152 | 0.0107 |
| 2026-11-11 | fix-3 | deepseek-v4-pro | no | 10730 | 2005 | 0 | 76288 | 0.0127 |
| 2026-11-11 | docs | deepseek-flash | no | 88973 | 13536 | 0 | 256 | 0.0215 |

Total: $0.1370. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
