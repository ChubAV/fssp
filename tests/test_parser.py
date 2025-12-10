import pytest

from src.infrastructure.parser import FsspHtmlParser


HTML_SNIPPET = """
<div class="results-frame">
  <table class="list">
    <tr><th>header</th></tr>
    <tr class="region-title"><td colspan="8">Краснодарский край</td></tr>
    <tr>
      <td>Иванов Иван</td>
      <td>123/45/67890-ИП</td>
      <td>Документ</td>
      <td></td>
      <td></td>
      <td>1000</td>
      <td>Отдел</td>
      <td>Судебный пристав</td>
    </tr>
  </table>
</div>
"""


def test_parser_extracts_single_row():
    parser = FsspHtmlParser()

    rows = parser.parse_cases(HTML_SNIPPET)

    assert len(rows) == 1
    row = rows[0]
    assert row["region"] == "Краснодарский край"
    assert row["debtor"] == "Иванов Иван"
    assert row["ip"] == "123/45/67890-ИП"
    assert row["debt"] == "1000"


def test_parser_returns_empty_for_missing_table():
    parser = FsspHtmlParser()

    rows = parser.parse_cases("<html></html>")

    assert rows == []
