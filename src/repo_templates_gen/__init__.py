"""Generate GitHub issue forms and pull request templates from a single JSON config.

This module provides:
- Dataclasses for configuration: ``Field``, ``IssueForm``, ``ContactLink``, ``TemplateConfig``.
- ``load_config`` to parse and validate a JSON configuration string.
- ``render_issue_form``, ``render_pr_template``, and ``render_all`` to produce
  byte-exact YAML and Markdown output.
- ``write_all`` to write rendered files to disk atomically after checking for conflicts.
- ``TemplateError`` for all validation and IO errors with a stable machine-readable code.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

__all__ = [
    "ContactLink",
    "Field",
    "IssueForm",
    "TemplateConfig",
    "TemplateError",
    "load_config",
    "render_all",
    "render_issue_form",
    "render_pr_template",
    "write_all",
]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())


class TemplateError(Exception):
    """Base error for the library with a stable machine-readable code."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        message = f"{code}: {detail}" if detail else code
        if len(message) > 200:
            message = message[:197] + "..."
        super().__init__(message)


@dataclass(frozen=True)
class Field:
    """Represents a single element in an issue form body.

    Attributes:
        type: The type of the element. Must be one of ``'markdown'``, ``'input'``,
            ``'textarea'``, ``'dropdown'``, or ``'checkboxes'``.
        id: Optional identifier for the element. If non-empty, must match
            ``^[A-Za-z0-9_-]+$`` and must be unique within a form.
        label: Display label for non-markdown elements. Must be non-empty.
        description: Optional longer description shown under the label.
        placeholder: Optional placeholder text.
        options: For dropdown and checkboxes, a tuple of valid options.
        multiple: For dropdown, whether multiple selections are allowed.
        required: Whether the element is required.
        value: For markdown elements, the markdown content. Required and non-empty.
    """

    type: Literal["markdown", "input", "textarea", "dropdown", "checkboxes"]
    id: str = ""
    label: str = ""
    description: str = ""
    placeholder: str = ""
    options: tuple[str, ...] = ()
    multiple: bool = False
    required: bool = False
    value: str = ""

    def __post_init__(self) -> None:
        if self.type not in ("markdown", "input", "textarea", "dropdown", "checkboxes"):
            raise ValueError(f"invalid field type: {self.type}")
        if self.id:
            if self.type == "markdown":
                raise TemplateError("invalid_id", "markdown elements cannot have an id")
            if not re.fullmatch(r"[A-Za-z0-9_-]+", self.id):
                raise TemplateError("invalid_id", f"id '{self.id}' contains invalid characters")
        if self.type != "markdown" and not self.label.strip():
            raise TemplateError("invalid_config", "non-markdown fields require a non-empty label")
        if self.type == "markdown" and not self.value.strip():
            raise TemplateError("invalid_config", "markdown fields require attributes.value")
        if self.type in ("dropdown", "checkboxes"):
            if not self.options:
                raise TemplateError("invalid_options", "options must not be empty")
            if len(set(self.options)) != len(self.options):
                raise TemplateError("invalid_options", "options must be distinct")
            if "None" in self.options:
                raise TemplateError("invalid_options", "'None' is a reserved option")


@dataclass(frozen=True)
class IssueForm:
    """Represents a single issue template file."""

    slug: str
    name: str
    description: str
    fields: Sequence[Field]
    title: str = ""
    labels: Sequence[str] = ()

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z0-9-]{1,64}", self.slug):
            raise TemplateError(
                "invalid_slug", f"slug '{self.slug}' must match ^[a-z0-9-]{{1,64}}$"
            )
        if not self.name.strip() or not self.description.strip():
            raise TemplateError("invalid_config", "name and description must be non-empty")
        if len(self.fields) > 30:
            raise TemplateError("too_many_fields", f"too many fields in form '{self.slug}'")
        non_markdown = [f for f in self.fields if f.type != "markdown"]
        if not non_markdown:
            raise TemplateError(
                "no_input_field", "form must contain at least one non-markdown field"
            )
        ids = [f.id for f in non_markdown if f.id]
        if len(ids) != len(set(ids)):
            raise TemplateError("duplicate_id", "duplicate id in form")
        labels = [f.label for f in non_markdown]
        if len(labels) != len(set(labels)):
            raise TemplateError("duplicate_label", "duplicate label in form")


@dataclass(frozen=True)
class ContactLink:
    """Represents a contact link entry in config.yml."""

    name: str
    url: str
    about: str = ""

    def __post_init__(self) -> None:
        if not self.url.startswith("https://"):
            raise TemplateError("invalid_url", "contact link URLs must start with https://")


@dataclass(frozen=True)
class TemplateConfig:
    """Top-level configuration for rendering templates."""

    forms: tuple[IssueForm, ...]
    pr_sections: tuple[str, ...]
    pr_checklist: tuple[str, ...]
    blank_issues_enabled: bool = True
    contact_links: tuple[ContactLink, ...] = ()

    def __post_init__(self) -> None:
        if len(self.forms) > 20:
            raise TemplateError("too_many_fields", "too many forms")


_MAX_FORMS = 20
_MAX_FIELDS_PER_FORM = 30
_MAX_STRING_LENGTH = 1000
_MAX_JSON_DEPTH = 16


def _check_depth(text: str, max_depth: int) -> bool:
    """Return True if JSON nesting depth does not exceed max_depth."""
    depth = 0
    in_string = False
    escape = False
    for ch in text:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch in "{[":
                depth += 1
                if depth > max_depth:
                    return False
            elif ch in "}]":
                depth -= 1
                if depth < 0:
                    # Unbalanced; json.loads will catch later
                    pass
    return True


def _validate_string_lengths(data: Any) -> None:
    """Recursively check that all strings are at most _MAX_STRING_LENGTH characters."""
    if isinstance(data, str):
        if len(data) > _MAX_STRING_LENGTH:
            raise TemplateError("invalid_config", "string exceeds 1000 characters")
    elif isinstance(data, list):
        for item in data:
            _validate_string_lengths(item)
    elif isinstance(data, dict):
        for value in data.values():
            _validate_string_lengths(value)


def load_config(text: str, *, max_bytes: int = 262_144) -> TemplateConfig:
    """Parse and validate a JSON configuration string.

    Args:
        text: The JSON configuration as a string.
        max_bytes: Maximum allowed size in bytes (default 262,144).

    Returns:
        A validated :class:`TemplateConfig` instance.

    Raises:
        TemplateError: with codes ``config_too_large``, ``invalid_config``,
            ``invalid_slug``, ``invalid_id``, ``duplicate_id``,
            ``duplicate_label``, ``no_input_field``, ``invalid_options``,
            ``invalid_url``, ``too_many_fields``.
    """
    if len(text.encode("utf-8")) > max_bytes:
        raise TemplateError("config_too_large")
    if not _check_depth(text, _MAX_JSON_DEPTH):
        raise TemplateError("invalid_config", "JSON nesting too deep")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise TemplateError("invalid_config", "invalid JSON") from None
    if not isinstance(data, dict):
        raise TemplateError("invalid_config", "top-level must be an object")
    _validate_string_lengths(data)

    # Parse issue forms
    if "issue_forms" not in data or not isinstance(data["issue_forms"], list):
        raise TemplateError("invalid_config", "missing 'issue_forms' list")
    forms_raw = data["issue_forms"]
    if len(forms_raw) > _MAX_FORMS:
        raise TemplateError("too_many_fields", "too many forms")
    forms = []
    for form_dict in forms_raw:
        if not isinstance(form_dict, dict):
            raise TemplateError("invalid_config", "each form must be an object")
        required = ("slug", "name", "description", "fields")
        if any(key not in form_dict for key in required):
            raise TemplateError("invalid_config", "form missing required fields")
        slug = form_dict["slug"]
        if not isinstance(slug, str):
            raise TemplateError("invalid_config", "slug must be a string")
        name = form_dict["name"]
        if not isinstance(name, str):
            raise TemplateError("invalid_config", "name must be a string")
        description = form_dict["description"]
        if not isinstance(description, str):
            raise TemplateError("invalid_config", "description must be a string")
        title = form_dict.get("title", "")
        if not isinstance(title, str):
            raise TemplateError("invalid_config", "title must be a string")
        labels = form_dict.get("labels", [])
        if not isinstance(labels, list) or not all(isinstance(label, str) for label in labels):
            raise TemplateError("invalid_config", "labels must be a list of strings")
        fields_raw = form_dict["fields"]
        if not isinstance(fields_raw, list):
            raise TemplateError("invalid_config", "fields must be a list")
        if len(fields_raw) > _MAX_FIELDS_PER_FORM:
            raise TemplateError("too_many_fields", "too many fields in form")
        fields = []
        for field_dict in fields_raw:
            if not isinstance(field_dict, dict):
                raise TemplateError("invalid_config", "each field must be an object")
            if "type" not in field_dict:
                raise TemplateError("invalid_config", "field missing 'type'")
            ftype = field_dict["type"]
            if ftype not in ("markdown", "input", "textarea", "dropdown", "checkboxes"):
                raise TemplateError("invalid_config", f"invalid field type '{ftype}'")
            fid = field_dict.get("id", "")
            if not isinstance(fid, str):
                raise TemplateError("invalid_config", "id must be a string")
            flabel = field_dict.get("label", "")
            if not isinstance(flabel, str):
                raise TemplateError("invalid_config", "label must be a string")
            fdescription = field_dict.get("description", "")
            if not isinstance(fdescription, str):
                raise TemplateError("invalid_config", "description must be a string")
            fplaceholder = field_dict.get("placeholder", "")
            if not isinstance(fplaceholder, str):
                raise TemplateError("invalid_config", "placeholder must be a string")
            foptions = field_dict.get("options", ())
            if foptions:
                if not isinstance(foptions, list) or not all(isinstance(o, str) for o in foptions):
                    raise TemplateError("invalid_config", "options must be a list of strings")
                foptions_tuple = tuple(foptions)
            else:
                foptions_tuple = ()
            fmultiple = field_dict.get("multiple", False)
            if not isinstance(fmultiple, bool):
                raise TemplateError("invalid_config", "multiple must be a boolean")
            frequired = field_dict.get("required", False)
            if not isinstance(frequired, bool):
                raise TemplateError("invalid_config", "required must be a boolean")
            fvalue = field_dict.get("value", "")
            if not isinstance(fvalue, str):
                raise TemplateError("invalid_config", "value must be a string")
            try:
                field = Field(
                    type=ftype,
                    id=fid,
                    label=flabel,
                    description=fdescription,
                    placeholder=fplaceholder,
                    options=foptions_tuple,
                    multiple=fmultiple,
                    required=frequired,
                    value=fvalue,
                )
            except TemplateError:
                raise
            fields.append(field)
        try:
            form = IssueForm(
                slug=slug,
                name=name,
                description=description,
                fields=tuple(fields),
                title=title,
                labels=tuple(labels),
            )
        except TemplateError:
            raise
        forms.append(form)

    blank = data.get("blank_issues_enabled", True)
    if not isinstance(blank, bool):
        raise TemplateError("invalid_config", "blank_issues_enabled must be a boolean")

    contact_links_raw = data.get("contact_links", ())
    contact_links = []
    if contact_links_raw:
        if not isinstance(contact_links_raw, list):
            raise TemplateError("invalid_config", "contact_links must be a list")
        for link in contact_links_raw:
            if not isinstance(link, dict):
                raise TemplateError("invalid_config", "each contact link must be an object")
            if "name" not in link or "url" not in link:
                raise TemplateError("invalid_config", "contact link missing name or url")
            name = link["name"]
            if not isinstance(name, str):
                raise TemplateError("invalid_config", "contact link name must be a string")
            url = link["url"]
            if not isinstance(url, str):
                raise TemplateError("invalid_config", "contact link url must be a string")
            about = link.get("about", "")
            if not isinstance(about, str):
                raise TemplateError("invalid_config", "contact link about must be a string")
            try:
                cl = ContactLink(name=name, url=url, about=about)
            except TemplateError:
                raise
            contact_links.append(cl)

    pull_request = data.get("pull_request", {})
    if not isinstance(pull_request, dict):
        raise TemplateError("invalid_config", "pull_request must be an object")
    pr_sections = pull_request.get("sections", [])
    pr_checklist = pull_request.get("checklist", [])
    if not isinstance(pr_sections, list) or not all(isinstance(s, str) for s in pr_sections):
        raise TemplateError("invalid_config", "pull_request.sections must be a list of strings")
    if not isinstance(pr_checklist, list) or not all(isinstance(s, str) for s in pr_checklist):
        raise TemplateError("invalid_config", "pull_request.checklist must be a list of strings")

    return TemplateConfig(
        forms=tuple(forms),
        blank_issues_enabled=blank,
        contact_links=tuple(contact_links),
        pr_sections=tuple(pr_sections),
        pr_checklist=tuple(pr_checklist),
    )


def render_issue_form(form: IssueForm) -> str:
    """Render a single issue form to a YAML string."""
    lines = []
    lines.append(f"name: {json.dumps(form.name, ensure_ascii=False)}")
    lines.append(f"description: {json.dumps(form.description, ensure_ascii=False)}")
    if form.title:
        lines.append(f"title: {json.dumps(form.title, ensure_ascii=False)}")
    if form.labels:
        labels_str = ", ".join(json.dumps(label, ensure_ascii=False) for label in form.labels)
        lines.append(f"labels: [{labels_str}]")
    lines.append("body:")
    for field in form.fields:
        lines.append(f"  - type: {field.type}")
        if field.type != "markdown" and field.id:
            lines.append(f"    id: {json.dumps(field.id, ensure_ascii=False)}")
        lines.append("    attributes:")
        if field.type == "markdown":
            lines.append(f"      value: {json.dumps(field.value, ensure_ascii=False)}")
        else:
            lines.append(f"      label: {json.dumps(field.label, ensure_ascii=False)}")
            if field.description:
                lines.append(
                    f"      description: {json.dumps(field.description, ensure_ascii=False)}"
                )
            if field.placeholder:
                lines.append(
                    f"      placeholder: {json.dumps(field.placeholder, ensure_ascii=False)}"
                )
            if field.value:
                lines.append(f"      value: {json.dumps(field.value, ensure_ascii=False)}")
            if field.type in ("dropdown", "checkboxes") and field.options:
                lines.append("      options:")
                for opt in field.options:
                    if field.type == "checkboxes":
                        lines.append(f"        - label: {json.dumps(opt, ensure_ascii=False)}")
                    else:
                        lines.append(f"        - {json.dumps(opt, ensure_ascii=False)}")
            if field.multiple:
                lines.append("      multiple: true")
        if field.required:
            lines.append("    validations:")
            lines.append("      required: true")
    return "\n".join(lines) + "\n"


def render_pr_template(sections: Sequence[str], checklist: Sequence[str] = ()) -> str:
    """Render a pull request template Markdown string."""
    result = "\n\n".join(f"## {s}" for s in sections)
    if checklist:
        result += "\n\n## Checklist\n\n"
        result += "".join(f"- [ ] {item}\n" for item in checklist)
        return result
    return result + "\n"


def render_all(config: TemplateConfig) -> dict[str, str]:
    """Render all output files from a TemplateConfig."""
    files = {}
    for form in config.forms:
        key = f".github/ISSUE_TEMPLATE/{form.slug}.yml"
        files[key] = render_issue_form(form)
    config_lines = [f"blank_issues_enabled: {str(config.blank_issues_enabled).lower()}"]
    if config.contact_links:
        config_lines.append("contact_links:")
        for link in config.contact_links:
            config_lines.append(f"  - name: {json.dumps(link.name, ensure_ascii=False)}")
            config_lines.append(f"    url: {json.dumps(link.url, ensure_ascii=False)}")
            config_lines.append(f"    about: {json.dumps(link.about, ensure_ascii=False)}")
    files[".github/ISSUE_TEMPLATE/config.yml"] = "\n".join(config_lines) + "\n"
    files[".github/pull_request_template.md"] = render_pr_template(
        config.pr_sections, config.pr_checklist
    )
    return files


def write_all(files: Mapping[str, str], root: Path, *, overwrite: bool = False) -> None:
    """Write rendered files to disk, not overwriting existing files unless allowed."""
    sorted_paths = sorted(files.keys())
    for rel_path in sorted_paths:
        target = root / rel_path
        if target.exists() and not overwrite:
            raise TemplateError("file_exists", rel_path)
    for rel_path, content in files.items():
        target = root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
