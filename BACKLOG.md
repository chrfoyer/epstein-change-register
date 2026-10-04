# Backlog — Epstein Library Change Register

> **What this is:** an independent completeness and change register for the DOJ
> Epstein Library. It tracks what was published, what moved, and what
> disappeared, with verifiable provenance. **It does not host the documents.**

## How this backlog is organised

Work is grouped into **slices**, not layers. Every slice ends with something
that can be shown to someone and that stands on its own if the next slice never
happens. A slice is sized for one weekend morning or two or three evenings —
roughly 4–6 hours.

Status: `[ ]` todo · `[~]` in progress · `[x]` done · `[-]` dropped (say why)

---

## Slice 0 — Start the clock

**Ships:** a crawler that has been running since day one.
**Why first:** the dataset's value is a function of elapsed observation time. A
week of delay is a week of history that cannot be recovered later. Ship this
before anything is pretty.

- [x] Scaffolding: `pyproject.toml`, `uv` setup, `.gitignore`, CI skeleton (pytest on push)
- [x] Source A: poll analytics.usa.gov top-downloads CSV daily (D-011) — first live run 2026-10-04: 93 PDFs kept, 7 excluded; state on `data` branch
- [ ] Source B: Wayback listing captures + CDX digest (D-014, spike complete 2026-10-04: archive.org reachable, 6 pages, 5–134 captures each, real listings confirmed)
- [ ] Source C: community hash lists as claimed hashes (yung-megafone/Epstein-Files)
- [-] ~~Download changed files; compute `sha256`~~ — dropped, PDFs are behind DOJ's age gate (D-011)
- [x] Conditional requests + polite delay; identifiable User-Agent with contact (Source A: serial, If-None-Match, UA from `REGISTER_CONTACT`)
- [x] Persist to DuckDB; commit or sync after every run (Parquet on `data` branch)
- [~] Runs unattended on a schedule without me touching it (daily cron from 2026-10-05; 0 of 3 unattended runs so far)

**Done when:** the job has completed three consecutive unattended runs.

---

## Slice 1 — First real output

**Ships:** a text report of what changed, generated from real observations.

- [ ] `change_event` table: `added`, `removed`, `reuploaded_identical`, `reuploaded_changed`, `moved_dataset`
- [ ] Removal rule: absent for 2+ consecutive polls (guards against flaky listings)
- [ ] Document identity: Bates number where present, else Wayback `archive_digest`; no fingerprint means "unknown", never "changed" (D-011)
- [ ] CLI: `report --since 7d` prints the week's events
- [ ] Unit tests on the event classifier with fixture data

**Done when:** the report describes a real change you can verify by hand on justice.gov.

---

## Slice 2 — Make it reusable (D1, D2)

**Ships:** a public dataset other people can build on.

- [ ] Publish gold tables as Parquet + CSV on a daily refresh
- [ ] `SCHEMA.md` with a documented, semver'd column contract
- [ ] Test fixtures with expected values, asserted in CI
- [ ] `LIMITATIONS.md` — what this cannot tell you (D3)

**Done when:** a stranger could reproduce your numbers from the docs alone.

---

## Slice 3 — The shareable artifact (C1, C2)

**Ships:** a public page you can put in a job application.

- [ ] Chart: cumulative documents live vs. removed over time
- [ ] Chart: mean redaction coverage per release date *(placeholder until Slice 6)*
- [ ] Weekly card feed, reverse-chronological, plain language
- [ ] Every card links to DOJ URL + archive snapshot
- [ ] Explicit "we do not host documents" statement, above the fold
- [ ] Static site build, loads in under 2s

**Done when:** you'd send the link to a stranger without caveats.

---

## Slice 4 — Provenance hardening (J1, J3)

**Ships:** claims that survive being challenged.

- [ ] Wayback CDX lookup per URL; store snapshot timestamps
- [ ] Save-Page-Now request on first observation of any new URL
- [ ] `corroboration_count` — independent sources producing the same hash
- [ ] Removal events cite the last capture proving the file was live
- [ ] Distinguish *removed* from *re-uploaded under a new filename* in the UI

**Done when:** every removal claim has third-party evidence attached.

---

## Slice 5 — Employer-facing (E1, E2, E3)

**Ships:** the repo reads well to someone giving it 60 seconds.

- [ ] `README.md`: problem → screenshot → architecture diagram, above the fold
- [ ] `DECISIONS.md` finalised (write entries as you go, not at the end)
- [ ] CI badge; data quality assertions that fail loudly
- [ ] Cost per run documented in the README
- [ ] Retention / `VACUUM` note — why bronze is append-only

**Done when:** someone who has never seen the project can explain it back to you.

---

## Slice 6 — Redaction coverage (J2) — *risky, do last*

**Ships:** the "did this get more redacted" feature.
**Risk:** scan noise can eat unlimited time. Timebox to two slices; if precision
is still poor, drop it and write up why in `LIMITATIONS.md`. That write-up is
itself a good outcome.
**Blocked (D-011):** every item below needs PDF bytes, and justice.gov PDFs sit
behind an age gate we do not pass. Do not start this slice until there is a lawful
byte source (DOJ feed or allowlist, verified Wayback PDF captures, or a mirror
with its own decision). If none appears, the slice becomes the `LIMITATIONS.md`
write-up.

- [ ] Rasterise at 150 DPI; dark-pixel ratio per page
- [ ] Threshold tuning against 20 hand-labelled pages — parallel path: `threshold-tuner` subagents, one parameter combination each
- [ ] Change event on coverage delta above threshold
- [ ] Side-by-side page render, changed regions highlighted
- [ ] Dual-layer extraction: embedded text vs. OCR of render
- [ ] Failed-redaction **findings** (page, bbox, char count) → public table
- [ ] Failed-redaction **content** → restricted schema, separate grants (E4)

**Done when:** precision on the hand-labelled set is good enough to publish, or
you have documented why it isn't.

---

## Slice 7 — Databricks port — *optional*

**Ships:** the same pipeline on the target architecture.
Only worth it if you want the platform on your CV or want the cost comparison
as a blog post. The product does not need it.

- [ ] Volumes + Auto Loader ingest
- [ ] Bronze / silver / gold as Delta
- [ ] Unity Catalog grants enforcing the restricted-schema split
- [ ] Cost comparison vs. the DuckDB version, published

---

## Icebox

- Jev integration (D-012, proposed): scope gate, anomaly triage, card text —
  advisory and metadata-only; via OpenRouter; blocked on reading TypeSafe's and
  OpenRouter's data terms and a privacy-setting smoke test
- Entity extraction and co-occurrence graph
- Full-text search over extracted text
- Coverage of House Oversight releases
- Alerting / RSS on new change events
