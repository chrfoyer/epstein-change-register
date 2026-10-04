# DOJ Outreach: Proposed Message

**Status:** Draft. Not yet sent. For maintainer review before posting.

**Recipient:** DOJ Office of Public Affairs or FOIA Liaison, Department of Justice

**Contact method:** [Find the appropriate liaison at](https://www.justice.gov/oip/find-foia-contact-doj/list)
or general FOIA email: MRUFOIA.Requests@usdoj.gov, phone: (301) 583-7354.

---

## Message

**Subject:** Machine-Readable File Manifest for Epstein Case Records

Dear [Recipient]:

We are maintaining an independent change register for the DOJ Epstein Library—a public,
completeness and audit log of court records and disclosures under the numbered dataset pages
at justice.gov/epstein/doj-disclosures. The register tracks what was published, what moved,
and what disappeared, with verifiable provenance and links to all original sources.

To improve the accuracy of this register and better serve researchers and archivists
tracking these records, we would like to request one or more of the following:

1. **A machine-readable manifest** listing all files currently published under each numbered
   dataset (DataSet 1 through DataSet 12, and any new sections), including:
   - Filename or file URL
   - EFTA Bates number (if assigned)
   - Publication or update date
   - Current status (live, superseded, redacted, etc.)

   A CSV, JSON, or API endpoint would all be suitable.

2. **An allowlist for direct access** to the dataset listing pages and file URLs, if they
   are subject to access controls or rate limits that prevent automated polling. We commit
   to polite, serial requests with rate limiting and an identifiable User-Agent.

3. **Documentation of any access policy** for these court records, including:
   - Whether there are planned changes to the dataset structure or availability
   - How removed or superseded files are handled
   - Contact channels for reporting missing or incorrectly linked files

This would help the register become a more reliable reference for researchers, journalists,
and archivists who depend on this data.

For questions about the register itself, please see:
https://github.com/chrfoyer/epstein-change-register

Thank you for your consideration.

Best regards,
[Maintainer name]
https://github.com/chrfoyer/epstein-change-register/issues

---

## Notes for Maintainer

- **Do not include personal email.** Use the repo issues URL as the only contact.
- **Be specific.** The three requests (manifest, allowlist, documentation) are concrete
  and actionable. A vague "help us track changes" will not get traction.
- **Lead with the public good.** Emphasize researcher and archivist use cases, not
  personal interest.
- **No technical jargon.** "Machine-readable" is clear; avoid acronyms beyond EFTA and
  Bates number.
- **Expect a slow response or none.** Government offices move slowly. Send this once and
  do not follow up unless they respond.
- **If you get a response, document it.** Add a note to DECISIONS.md or LIMITATIONS.md
  if DOJ clarifies their policy or plans.
