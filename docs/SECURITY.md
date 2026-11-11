# Security notes

## Threat model

`repo_templates_gen` processes a caller-supplied JSON string and writes rendered files under a caller-supplied directory. It makes no network calls and has no runtime dependencies.

Defended:
- Oversized configuration: `load_config` rejects UTF-8 input larger than 262,144 bytes with `config_too_large`.
- Deep JSON: a bracket-depth scan rejects nesting deeper than 16 before `json.loads`, with `invalid_config`.
- Oversized strings: every string in the parsed document is capped at 1,000 characters, with `invalid_config`.
- Excessive structure: at most 20 forms and 30 fields per form, with `too_many_fields`.
- Invalid identifiers: form slugs must match `^[a-z0-9-]{1,64}$`; non-empty field ids must match `^[A-Za-z0-9_-]+$` and are unique within a form; non-markdown labels are unique within a form.
- Incomplete forms: a form needs a non-empty name and description and at least one non-markdown field.
- Invalid choices: dropdown and checkboxes options must be non-empty, distinct and must not contain the reserved string `None`.
- Unsafe contact links: contact URLs must start with `https://`.
- Accidental overwrite: `write_all` checks all targets first and raises `file_exists` before writing when `overwrite` is false.
- Long error messages: `TemplateError` truncates its message to 200 characters.

Not defended:
- Hostile relative paths passed directly to `write_all`: the function joins caller-provided keys to `root` without a traversal or symlink check. `render_all` only produces fixed `.github/...` keys, but `write_all` is public.
- Secrets in the configuration: values are rendered into output files as supplied; the library does not scan for credentials.
- Filesystem races, permissions, disk-full conditions or partial writes: `write_all` is not atomic and does not roll back.
- YAML consumer differences: output is written with JSON double-quoted scalars, but the library does not parse the result with a YAML implementation at runtime.
- GitHub-side form semantics: the library validates documented structural rules but does not call GitHub or guarantee acceptance by a future GitHub schema.
- Authentication or authorization: the library has no users, sessions or access control.

## Publishing

No release or publishing automation is part of the source tree described here. PyPI publication, if performed, is outside the library runtime. To report a vulnerability, open an issue in the repository that hosts this package.
