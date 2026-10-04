# Session B: Source B, Wayback listing captures

Branch `feat/s0-wayback-source`. Decision number D-014.

Observe DOJ listing pages through Wayback captures, writing the shared listing
tables through `store.append_listing_capture`. Read-only against archive.org.

## Step 0: spike first, no code until it is answered

archive.org was offline earlier on 2026-10-04 and is back as of the coordinator's
check: the CDX lookup for `justice.gov/epstein/doj-disclosures` returned a 200
capture dated 20251219211448, 11,734 bytes (the Akamai holding page is about 2 KB).
That is a size comparison only. Serially, one request every 2 s, honest User-Agent:

1. Fetch that capture raw (`/web/<ts>id_/<url>`). Is it the real listing or the
   interstitial (markers: `bm-verify`, `/_sec/verify`, tiny body)?
2. CDX for the `data-set-N-files` pages (known slugs: `data-set-1-files`, `-2-`,
   `-3-`, `-12-`; also `first-phase-declassified-epstein-files`). Per page report
   capture count, date range, status codes, and real versus interstitial.
3. For the real listings, report using the doj-recon structure: markup shape,
   row selector, pagination, stable ids.
4. Do **not** use Save-Page-Now. It makes archive.org fetch DOJ on our behalf. If
   captures are too stale to be useful, that is a decision for D-014.

If archive.org is offline when you start, retry with backoff for about 10 minutes,
then stop and write up what you found. Do not build a speculative parser.

## If go

Read-only CDX client; interstitial detector (status `blocked`, zero file rows);
listing parser; write through `store.append_listing_capture` with `archive_url`,
`archive_ts` and the CDX digest per capture. Only court-record PDFs under numbered
`DataSet` paths (mirror `FILE_URL_RE` in `src/register/analytics.py`; D-002). Never
fetch PDFs. Fixtures from fixture-builder (synthetic CDX JSON and listing
snapshots). Add the poller to `.github/workflows/crawl.yml` as a separate job and
leave the daily Source A job untouched.

## Deliver

Spike findings recorded in D-014 even if no-go, and `docs/handover/b-status.md`.
