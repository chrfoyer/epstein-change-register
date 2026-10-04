from pathlib import Path

import httpx

from register import analytics, store

FIXTURES = Path(__file__).parent / "fixtures"
CSV = (FIXTURES / "analytics_top_downloads.csv").read_text()
BLOCKED = (FIXTURES / "analytics_blocked.html").read_text()


def client_for(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def csv_response(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, text=CSV, headers={"etag": 'W/"abc"', "content-type": "text/csv"})


def test_parse_keeps_only_numbered_dataset_pdfs():
    rows, excluded = analytics.parse(CSV)
    assert len(rows) == 6
    assert excluded == 3  # two mp4 rows, one non-epstein row
    assert all(r["file_url"].endswith(".pdf") for r in rows)
    assert {r["dataset"] for r in rows} == {"1", "2", "12"}
    assert all(r["bates_id"].startswith("EFTA9") for r in rows)


def test_parse_rejects_non_csv():
    assert analytics.parse(BLOCKED) is None


def test_run_appends_rows_and_view_spans():
    con = store.connect(":memory:")
    with client_for(csv_response) as c:
        assert analytics.run(con, c) == "ok"
    assert con.execute("SELECT count(*) FROM analytics_file_observation").fetchone()[0] == 6
    assert con.execute("SELECT count(*) FROM observed_file_span").fetchone()[0] == 6
    fetch = con.execute("SELECT status, row_count, excluded_count FROM analytics_fetch").fetchone()
    assert fetch == ("ok", 6, 3)


def test_identical_body_logs_fetch_but_no_duplicate_rows():
    con = store.connect(":memory:")
    with client_for(csv_response) as c:
        analytics.run(con, c)
        assert analytics.run(con, c) == "unchanged"
    assert con.execute("SELECT count(*) FROM analytics_file_observation").fetchone()[0] == 6
    assert con.execute("SELECT count(*) FROM analytics_fetch").fetchone()[0] == 2


def test_sends_stored_etag_and_handles_304():
    con = store.connect(":memory:")
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("if-none-match"))
        if request.headers.get("if-none-match"):
            return httpx.Response(304)
        return csv_response(request)

    with client_for(handler) as c:
        analytics.run(con, c)
        assert analytics.run(con, c) == "not_modified"
    assert seen == [None, 'W/"abc"']


def test_bot_wall_is_unexpected_and_writes_no_file_rows():
    con = store.connect(":memory:")
    handler = lambda request: httpx.Response(200, text=BLOCKED, headers={"content-type": "text/html"})
    with client_for(handler) as c:
        assert analytics.run(con, c) == "unexpected"
    assert con.execute("SELECT count(*) FROM analytics_file_observation").fetchone()[0] == 0
    assert con.execute("SELECT status FROM analytics_fetch").fetchone()[0] == "unexpected"


def test_server_error_is_error_not_empty_listing():
    con = store.connect(":memory:")
    with client_for(lambda request: httpx.Response(503)) as c:
        assert analytics.run(con, c) == "unexpected"
    assert con.execute("SELECT count(*) FROM analytics_file_observation").fetchone()[0] == 0


def test_parquet_roundtrip(tmp_path):
    con = store.connect(":memory:")
    with client_for(csv_response) as c:
        analytics.run(con, c)
    store.export(con, str(tmp_path))
    restored = store.connect(":memory:", import_dir=str(tmp_path))
    assert restored.execute("SELECT count(*) FROM analytics_file_observation").fetchone()[0] == 6
    assert restored.execute("SELECT count(*) FROM analytics_fetch").fetchone()[0] == 1
