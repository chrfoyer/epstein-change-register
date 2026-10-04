# Roadmap

## Assumptions

- Available capacity: **one 4–6 hour block per week**, give or take. Some weeks
  will be zero. The plan must survive that.
- Every slice is independently shippable. If the project stops after any slice,
  what exists still has value and can still be shown to someone.
- Slice 0 is the exception to all scheduling logic — see below.

## The one hard scheduling constraint

**Slice 0 ships in the first session, whatever else is unfinished.**

The register's value grows with elapsed observation time, and that clock cannot
be restarted. A crawler running for eight weeks against an ugly schema beats a
beautiful pipeline that starts in week eight. Everything else in this roadmap
can slip freely; this cannot.

## Phases

| Phase | Slices | Blocks | Elapsed (realistic) | Ships |
|---|---|---|---|---|
| **Collect** | 0 | 1 | Week 1 | Crawler running unattended |
| **Detect** | 1 | 1–2 | Weeks 2–3 | A real change report |
| **Publish** | 2, 3 | 2–3 | Weeks 4–6 | Public dataset + charts |
| **Harden** | 4, 5 | 2 | Weeks 7–9 | Provenance + a repo that reads well |
| **Extend** | 6 | 2 (timeboxed) | Weeks 10–12 | Redaction coverage, or a write-up of why not |
| **Optional** | 7 | 2 | — | Databricks port |

**Publishable v1 at the end of Phase "Harden" — realistically 8–10 weeks
elapsed, ~7 blocks of actual work.**

The gap between 7 blocks and 10 weeks is deliberate. Plan for the weeks you
lose; don't plan for the weeks you hope to have.

## Value at each stopping point

If the project ends after any of these, here is what you have:

- **After Slice 0** — a growing dataset nobody else is collecting. Not a
  portfolio piece yet, but an asset that appreciates while you do nothing.
- **After Slice 1** — a demonstrable claim: "I detected these removals on these
  dates." That is already a conversation starter in an interview.
- **After Slice 3** — a public link. This is the minimum viable portfolio piece.
  If capacity collapses, stop here and call it done.
- **After Slice 5** — a repo that stands up to technical review. This is the
  target.
- **After Slice 6** — a genuinely novel piece of analysis, plus a demonstrated
  approach to handling sensitive data under governance.

## Anti-goals

- Do not build the pipeline "properly" before it collects anything.
- Do not start with Databricks. Prove the concept on DuckDB where iteration is
  free, then port if there is a reason to.
- Do not expand scope to the image and video datasets. The legal exposure is
  real and the scope is unbounded.
- Do not let Slice 6 become the project.

## Cadence

- One block per week, same slot, protected. Consistency beats intensity here
  because the crawler is doing the compounding work between sessions.
- Write the `DECISIONS.md` entry at the *end of the block that made the
  decision*, while the alternatives are still fresh. Retrofitting a decision log
  produces a bad one.
- Every block ends with a commit that runs. No half-finished branches carried
  across a two-week gap — you will not remember the context.
