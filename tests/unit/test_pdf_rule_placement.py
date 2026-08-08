"""PDF section rules must sit BELOW their text, not strike through it
(v8.5.2 fix: the rule was drawn 3 pt above the baseline)."""
import re
import zlib

from rgcs_desktop.services import pdf_sheets


def _page_ops(pdf: bytes) -> str:
    """Decompress every FlateDecode content stream in the file."""
    ops = []
    for m in re.finditer(rb"stream\n(.*?)\nendstream", pdf, re.S):
        try:
            ops.append(zlib.decompress(m.group(1)).decode("latin-1"))
        except zlib.error:
            continue
    assert ops, "no decodable content streams found"
    return "\n".join(ops)


def test_rule_is_below_heading_baseline(tmp_path):
    out = tmp_path / "sheet.pdf"
    pdf_sheets.render_sheet_pdf(
        title="Rule placement check",
        subtitle="sub",
        sections=[("Heading A", pdf_sheets.rows_block([("k", "v")])),
                  ("Heading B", pdf_sheets.table_block(
                      ["col1", "col2"], [["a", "b"], ["c", "d"]]))],
        boundary="boundary text",
        out_path=out,
        input_hash="0" * 64)
    ops = _page_ops(out.read_bytes())

    # pair every rule with the text drawn immediately before it
    text_re = re.compile(
        r"BT /F\d [\d.]+ Tf ([\d.]+) ([\d.]+) Td \((.*?)\) Tj ET")
    rule_re = re.compile(r"([\d.]+) ([\d.]+) m [\d.]+ ([\d.]+) l S")
    events = []
    for m in text_re.finditer(ops):
        events.append(("text", m.start(), float(m.group(2)), m.group(3)))
    for m in rule_re.finditer(ops):
        assert m.group(2) == m.group(3), "rules are horizontal"
        events.append(("rule", m.start(), float(m.group(2)), ""))
    events.sort(key=lambda e: e[1])

    checked = 0
    for i, (kind, _pos, y, _txt) in enumerate(events):
        if kind != "rule" or i == 0:
            continue
        prev = events[i - 1]
        assert prev[0] == "text", "every rule follows its text"
        baseline = prev[2]
        assert y < baseline, (
            f"rule at y={y} must be BELOW the baseline {baseline} of "
            f"{prev[3]!r} — above the baseline strikes the text")
        checked += 1
    assert checked >= 2   # heading rules + table header rule exist
