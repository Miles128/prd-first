"""端到端试用:四个模板填满必填项并渲染/校验。"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from prd_first import storage
from prd_first.cli import _check_result, app
from prd_first.models import PrdMeta, list_templates, load_template
from prd_first.render import render_prd

runner = CliRunner()

SAMPLE_TEXT = "试用样例"
SAMPLE_LIST = ["项A", "项B"]


def _fill_required(template_type: str) -> PrdMeta:
    template = load_template(template_type)
    meta = PrdMeta.new(template_type)
    for field in template.fields:
        if not field.required:
            continue
        if field.type == "list":
            meta.set(field.key, list(SAMPLE_LIST))
        elif field.type == "single":
            meta.set(field.key, field.choices[0] if field.choices else SAMPLE_TEXT)
        else:
            meta.set(field.key, SAMPLE_TEXT)
    return meta


class TestTemplateTrial:
    def test_all_templates_complete(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        for t in list_templates():
            meta = _fill_required(t.type)
            storage.save_meta(meta)
            md = render_prd(t, meta)
            storage.save_prd(md)
            ok, missing = _check_result(t, meta)
            assert ok, f"{t.type} missing: {[f.key for f in missing]}"
            assert t.name in md
            for f in t.fields:
                if f.required:
                    assert f"### {f.label}" in md
            result = runner.invoke(app, ["check"])
            assert result.exit_code == 0, result.output

    def test_web_app_auth_is_last_optional(self):
        t = load_template("web-app")
        keys = [f.key for f in t.fields]
        assert keys[-1] == "auth"
        assert t.find("auth") is not None
        assert t.find("auth").required is False
        # all required come before auth
        auth_idx = keys.index("auth")
        for f in t.fields[:auth_idx]:
            assert f.required, f.key

    def test_every_field_has_why_and_prompt(self):
        for t in list_templates():
            assert len(t.fields) >= 8
            for f in t.fields:
                assert f.prompt.strip(), f"{t.type}.{f.key}"
                assert f.why.strip(), f"{t.type}.{f.key}"
