import json
from pathlib import Path

from pipeline.crawl_wiki import html_to_markdown_bundle


def test_html_to_markdown_produces_bundle(tmp_path):
    html_dir = Path(__file__).parent / "fixtures" / "mini-vg13" / "wiki_html"
    out_dir = tmp_path / "wiki"
    html_to_markdown_bundle(html_dir, out_dir)

    md_files = sorted(p.name for p in out_dir.glob("*.md"))
    assert md_files == ["Super_widget.md", "Widget.md"]

    widget = (out_dir / "Widget.md").read_text()
    assert "# Widget" in widget
    assert "simple test object" in widget

    index = json.loads((out_dir / "index.json").read_text())
    assert {"page": "Widget", "title": "Widget"} in index
    assert {"page": "Super_widget", "title": "Super widget"} in index
