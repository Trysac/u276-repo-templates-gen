from __future__ import annotations

import json

import pytest
import yaml

from repo_templates_gen import (
    ContactLink,
    Field,
    IssueForm,
    TemplateConfig,
    TemplateError,
    load_config,
    render_all,
    render_issue_form,
    render_pr_template,
    write_all,
)


def test_field_invalid_id_raises_template_error():
    with pytest.raises(TemplateError) as exc:
        Field(type="input", id="what happened")
    assert exc.value.code == "invalid_id"


def test_field_markdown_with_id_raises_invalid_id():
    with pytest.raises(TemplateError) as exc:
        Field(type="markdown", id="m1", value="content")
    assert exc.value.code == "invalid_id"


def test_field_non_markdown_empty_label_raises_invalid_config():
    with pytest.raises(TemplateError) as exc:
        Field(type="input", label="")
    assert exc.value.code == "invalid_config"


def test_field_markdown_empty_value_raises_invalid_config():
    with pytest.raises(TemplateError) as exc:
        Field(type="markdown")
    assert exc.value.code == "invalid_config"


def test_field_dropdown_empty_options_raises_invalid_options():
    with pytest.raises(TemplateError) as exc:
        Field(type="dropdown", label="OS", options=())
    assert exc.value.code == "invalid_options"


def test_field_dropdown_duplicate_options_raises_invalid_options():
    with pytest.raises(TemplateError) as exc:
        Field(type="dropdown", label="OS", options=("a", "a"))
    assert exc.value.code == "invalid_options"


def test_field_dropdown_reserved_none_option_raises_invalid_options():
    with pytest.raises(TemplateError) as exc:
        Field(type="dropdown", label="OS", options=("None", "a"))
    assert exc.value.code == "invalid_options"


def test_field_checkboxes_similar_validation():
    with pytest.raises(TemplateError) as exc:
        Field(type="checkboxes", label="OS", options=())
    assert exc.value.code == "invalid_options"
    with pytest.raises(TemplateError) as exc:
        Field(type="checkboxes", label="OS", options=("a", "a"))
    assert exc.value.code == "invalid_options"
    with pytest.raises(TemplateError) as exc:
        Field(type="checkboxes", label="OS", options=("None", "a"))
    assert exc.value.code == "invalid_options"


def test_issue_form_duplicate_id():
    fields = [
        Field(type="input", id="what", label="What"),
        Field(type="textarea", id="what", label="Details"),
    ]
    with pytest.raises(TemplateError) as exc:
        IssueForm(slug="bug", name="Bug", description="desc", fields=fields)
    assert exc.value.code == "duplicate_id"


def test_issue_form_duplicate_label():
    fields = [
        Field(type="input", id="a", label="Steps"),
        Field(type="textarea", id="b", label="Steps"),
    ]
    with pytest.raises(TemplateError) as exc:
        IssueForm(slug="bug", name="Bug", description="desc", fields=fields)
    assert exc.value.code == "duplicate_label"


def test_issue_form_all_markdown_raises_no_input_field():
    fields = [Field(type="markdown", value="hello")]
    with pytest.raises(TemplateError) as exc:
        IssueForm(slug="bug", name="Bug", description="desc", fields=fields)
    assert exc.value.code == "no_input_field"


def test_issue_form_invalid_slug():
    with pytest.raises(TemplateError) as exc:
        IssueForm(
            slug="Bad Slug",
            name="Bug",
            description="desc",
            fields=[Field(type="input", label="x")],
        )
    assert exc.value.code == "invalid_slug"


def test_contact_link_invalid_url():
    with pytest.raises(TemplateError) as exc:
        ContactLink(name="x", url="http://example.com")
    assert exc.value.code == "invalid_url"


def test_render_issue_form_acceptance_exact():
    form = IssueForm(
        slug="bug",
        name="Bug report",
        description="Report a defect",
        labels=["bug"],
        fields=[
            Field(
                type="textarea",
                id="what",
                label="What happened",
                required=True,
            )
        ],
    )
    expected = (
        'name: "Bug report"\n'
        'description: "Report a defect"\n'
        'labels: ["bug"]\n'
        "body:\n"
        "  - type: textarea\n"
        '    id: "what"\n'
        "    attributes:\n"
        '      label: "What happened"\n'
        "    validations:\n"
        "      required: true\n"
    )
    assert render_issue_form(form) == expected


def test_render_issue_form_dropdown_with_options_and_multiple():
    form = IssueForm(
        slug="feat",
        name="Feature",
        description="Request a feature",
        fields=[
            Field(
                type="dropdown",
                id="platform",
                label="Platform",
                options=("Linux", "macOS"),
                multiple=True,
            )
        ],
    )
    output = render_issue_form(form)
    assert '      options:\n        - "Linux"\n        - "macOS"\n' in output
    assert "      multiple: true\n" in output


def test_render_issue_form_checkboxes_options():
    form = IssueForm(
        slug="bug",
        name="Bug",
        description="desc",
        fields=[
            Field(type="checkboxes", id="os", label="OS", options=("Linux", "macOS")),
        ],
    )
    output = render_issue_form(form)
    assert '      options:\n        - label: "Linux"\n        - label: "macOS"\n' in output


def test_render_issue_form_markdown_element():
    form = IssueForm(
        slug="bug",
        name="Bug",
        description="desc",
        fields=[
            Field(type="markdown", value="**Please** fill"),
            Field(type="input", label="Title"),
        ],
    )
    output = render_issue_form(form)
    assert "  - type: markdown\n" in output
    assert '      value: "**Please** fill"\n' in output
    assert "    id:" not in output  # markdown has no id


def test_render_issue_form_labels_with_special_chars():
    form = IssueForm(
        slug="bug",
        name="Bug",
        description="desc",
        labels=["needs: triage", "#1 priority", 'say "hi"', "café"],
        fields=[Field(type="input", label="x")],
    )
    output = render_issue_form(form)
    # Round trip through YAML
    parsed = yaml.safe_load(output)
    assert parsed["labels"] == ["needs: triage", "#1 priority", 'say "hi"', "café"]


def test_render_pr_template_exact_with_checklist():
    assert render_pr_template(["Summary", "Testing"], checklist=["Tests added"]) == (
        "## Summary\n\n## Testing\n\n## Checklist\n\n- [ ] Tests added\n"
    )


def test_render_pr_template_exact_without_checklist():
    assert render_pr_template(["Summary", "Testing"]) == "## Summary\n\n## Testing\n"


def test_render_all_paths_and_content():
    config = TemplateConfig(
        forms=(
            IssueForm(
                slug="bug",
                name="Bug",
                description="desc",
                fields=[Field(type="input", label="x")],
            ),
        ),
        pr_sections=("Summary", "Testing"),
        pr_checklist=("Tests added",),
        blank_issues_enabled=False,
    )
    files = render_all(config)
    assert sorted(files.keys()) == [
        ".github/ISSUE_TEMPLATE/bug.yml",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/pull_request_template.md",
    ]
    assert files[".github/ISSUE_TEMPLATE/config.yml"] == "blank_issues_enabled: false\n"
    assert (
        files[".github/pull_request_template.md"]
        == "## Summary\n\n## Testing\n\n## Checklist\n\n- [ ] Tests added\n"
    )


def test_render_all_with_contact_links():
    config = TemplateConfig(
        forms=(),
        pr_sections=(),
        pr_checklist=(),
        blank_issues_enabled=True,
        contact_links=(ContactLink(name="Docs", url="https://example.com", about="Read the docs"),),
    )
    files = render_all(config)
    assert "contact_links:\n" in files[".github/ISSUE_TEMPLATE/config.yml"]
    assert '  - name: "Docs"\n' in files[".github/ISSUE_TEMPLATE/config.yml"]
    assert '    url: "https://example.com"\n' in files[".github/ISSUE_TEMPLATE/config.yml"]
    assert '    about: "Read the docs"\n' in files[".github/ISSUE_TEMPLATE/config.yml"]


def test_load_config_basic():
    text = json.dumps(
        {
            "issue_forms": [
                {
                    "slug": "bug",
                    "name": "Bug",
                    "description": "Report a bug",
                    "fields": [
                        {
                            "type": "input",
                            "id": "title",
                            "label": "Title",
                            "required": True,
                        }
                    ],
                }
            ],
            "blank_issues_enabled": True,
            "contact_links": [],
            "pull_request": {"sections": ["Summary"], "checklist": []},
        }
    )
    config = load_config(text)
    assert len(config.forms) == 1
    assert config.forms[0].slug == "bug"
    assert config.blank_issues_enabled is True
    assert config.pr_sections == ("Summary",)
    assert config.pr_checklist == ()


def test_load_config_too_large():
    text = "x" * 262_145
    with pytest.raises(TemplateError) as exc:
        load_config(text)
    assert exc.value.code == "config_too_large"


def test_load_config_invalid_json():
    with pytest.raises(TemplateError) as exc:
        load_config("{")
    assert exc.value.code == "invalid_config"


def test_load_config_depth_too_deep():
    # 17 nested arrays
    text = "[" * 17 + "]" * 17
    with pytest.raises(TemplateError) as exc:
        load_config(text)
    assert exc.value.code == "invalid_config"


def test_load_config_string_too_long():
    long_str = "a" * 1001
    text = json.dumps(
        {
            "issue_forms": [
                {
                    "slug": "bug",
                    "name": long_str,
                    "description": "desc",
                    "fields": [{"type": "input", "label": "x"}],
                }
            ],
            "pull_request": {"sections": [], "checklist": []},
        }
    )
    with pytest.raises(TemplateError) as exc:
        load_config(text)
    assert exc.value.code == "invalid_config"


def test_load_config_too_many_forms():
    forms = []
    for i in range(21):
        forms.append(
            {
                "slug": f"bug{i}",
                "name": "Bug",
                "description": "desc",
                "fields": [{"type": "input", "label": "x"}],
            }
        )
    text = json.dumps({"issue_forms": forms, "pull_request": {"sections": [], "checklist": []}})
    with pytest.raises(TemplateError) as exc:
        load_config(text)
    assert exc.value.code == "too_many_fields"


def test_load_config_too_many_fields():
    fields = [{"type": "input", "label": f"f{i}"} for i in range(31)]
    text = json.dumps(
        {
            "issue_forms": [
                {
                    "slug": "bug",
                    "name": "Bug",
                    "description": "desc",
                    "fields": fields,
                }
            ],
            "pull_request": {"sections": [], "checklist": []},
        }
    )
    with pytest.raises(TemplateError) as exc:
        load_config(text)
    assert exc.value.code == "too_many_fields"


def test_load_config_missing_required_keys():
    with pytest.raises(TemplateError) as exc:
        load_config("{}")
    assert exc.value.code == "invalid_config"


def test_load_config_invalid_contact_link_url():
    text = json.dumps(
        {
            "issue_forms": [],
            "contact_links": [{"name": "x", "url": "http://example.com"}],
            "pull_request": {"sections": [], "checklist": []},
        }
    )
    with pytest.raises(TemplateError) as exc:
        load_config(text)
    assert exc.value.code == "invalid_url"


def test_write_all_creates_files(tmp_path):
    files = {"a.txt": "hello\n", "sub/b.txt": "world\n"}
    write_all(files, tmp_path)
    assert (tmp_path / "a.txt").read_text() == "hello\n"
    assert (tmp_path / "sub/b.txt").read_text() == "world\n"


def test_write_all_preserves_lf_bytes(tmp_path):
    files = {"a.txt": "hello\nworld\n"}
    write_all(files, tmp_path)
    assert (tmp_path / "a.txt").read_bytes() == b"hello\nworld\n"


def test_write_all_overwrite_false_raises_file_exists(tmp_path):
    (tmp_path / "b.txt").write_text("old")
    files = {"a.txt": "new", "b.txt": "new2"}
    with pytest.raises(TemplateError) as exc:
        write_all(files, tmp_path)
    assert exc.value.code == "file_exists"
    assert "b.txt" in str(exc.value)
    # Ensure nothing was written
    assert (tmp_path / "a.txt").exists() is False


def test_write_all_overwrite_true(tmp_path):
    (tmp_path / "a.txt").write_text("old")
    files = {"a.txt": "new"}
    write_all(files, tmp_path, overwrite=True)
    assert (tmp_path / "a.txt").read_text() == "new"


def test_cli_config_literal_c_json(tmp_path, monkeypatch):
    (tmp_path / "c.json").write_text(
        json.dumps(
            {
                "issue_forms": [
                    {
                        "slug": "bug",
                        "name": "Bug",
                        "description": "desc",
                        "fields": [{"type": "input", "label": "x"}],
                    }
                ],
                "pull_request": {"sections": ["Summary"], "checklist": []},
            }
        )
    )
    out_dir = tmp_path / "out"
    monkeypatch.chdir(tmp_path)
    from repo_templates_gen.__main__ import main

    ret = main(["--config", "c.json", "--out", str(out_dir)])
    assert ret == 0
    assert (out_dir / ".github/ISSUE_TEMPLATE/bug.yml").exists()


def test_cli_success(tmp_path, capsys):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "issue_forms": [
                    {
                        "slug": "bug",
                        "name": "Bug",
                        "description": "desc",
                        "fields": [{"type": "input", "label": "x"}],
                    }
                ],
                "pull_request": {"sections": ["Summary"], "checklist": []},
            }
        )
    )
    out_dir = tmp_path / "out"
    from repo_templates_gen.__main__ import main

    ret = main(["--config", str(config_path), "--out", str(out_dir)])
    assert ret == 0
    assert (out_dir / ".github/ISSUE_TEMPLATE/bug.yml").exists()


def test_cli_file_exists_returns_1(tmp_path, capsys):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "issue_forms": [
                    {
                        "slug": "bug",
                        "name": "Bug",
                        "description": "desc",
                        "fields": [{"type": "input", "label": "x"}],
                    }
                ],
                "pull_request": {"sections": ["Summary"], "checklist": []},
            }
        )
    )
    out_dir = tmp_path / "out"
    # Run once to create files
    from repo_templates_gen.__main__ import main

    assert main(["--config", str(config_path), "--out", str(out_dir)]) == 0
    # Run again without force
    assert main(["--config", str(config_path), "--out", str(out_dir)]) == 1
    captured = capsys.readouterr()
    assert "file_exists: .github/ISSUE_TEMPLATE/bug.yml" in captured.err


def test_cli_missing_config_returns_2():
    from repo_templates_gen.__main__ import main

    ret = main([])
    assert ret == 2


def test_cli_out_is_regular_file_returns_2(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "issue_forms": [
                    {
                        "slug": "bug",
                        "name": "Bug",
                        "description": "desc",
                        "fields": [{"type": "input", "label": "x"}],
                    }
                ],
                "pull_request": {"sections": ["Summary"], "checklist": []},
            }
        )
    )
    out_file = tmp_path / "out"
    out_file.write_text("not a directory")
    from repo_templates_gen.__main__ import main

    ret = main(["--config", str(config_path), "--out", str(out_file)])
    assert ret == 2


def test_cli_config_file_not_found_returns_2(tmp_path):
    from repo_templates_gen.__main__ import main

    ret = main(["--config", str(tmp_path / "nonexistent.json"), "--out", str(tmp_path)])
    assert ret == 2


def test_cli_domain_error_returns_1(tmp_path, capsys):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "issue_forms": [
                    {
                        "slug": "bad slug",  # invalid slug
                        "name": "Bug",
                        "description": "desc",
                        "fields": [{"type": "input", "label": "x"}],
                    }
                ],
                "pull_request": {"sections": [], "checklist": []},
            }
        )
    )
    from repo_templates_gen.__main__ import main

    ret = main(["--config", str(config_path), "--out", str(tmp_path)])
    assert ret == 1
    captured = capsys.readouterr()
    assert "invalid_slug" in captured.err
