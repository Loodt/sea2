# corpora/au-token-regulatory

Bedrock regulatory documents for the au-token research project. These are
the static, known-in-advance sources the LocalCorpusSearcher indexes once
per repo bump; the conductor's web-search Searcher handles the long tail
and changing material.

## Populating

Two equivalent paths:

### Option A — drop files manually

Save each PDF/HTML in this directory under the filename listed in
`manifest.json`. Then index:

```bash
python -m sea2.retrieve.index_corpus corpora/au-token-regulatory \
  --output corpora/au-token-regulatory/index.sqlite
```

### Option B — fill in source_urls, run the downloader

Edit `manifest.json` and fill `source_url` for each document with the
canonical public URL (gov.za, fsca.co.za, saflii.org, etc.). Then:

```bash
python scripts/download_corpus.py corpora/au-token-regulatory/manifest.json
python -m sea2.retrieve.index_corpus corpora/au-token-regulatory \
  --output corpora/au-token-regulatory/index.sqlite
```

The downloader is idempotent — re-running skips files already present.

## What's tracked vs ignored

- `manifest.json` and this `README.md` are checked in.
- The actual PDFs (`*.pdf`, `*.html`) and the built `index.sqlite` are
  `.gitignore`d. They are reproducible from the manifest plus their
  upstream URLs.

## Notes on sources

- SA government gazettes are at `https://www.gov.za/documents/`. Some
  consolidated Acts are easier to find via `https://www.justice.gov.za/`
  or `lawsofsouthafrica.up.ac.za`.
- Case law: SAFLII (`https://www.saflii.org/`).
- FSCA notices: `https://www.fsca.co.za/` (Press Releases / Regulatory Frameworks).
- 2025 Bill: search "Mineral Resources Development Bill 2025 site:gov.za"
  for the gazetted version; later versions may sit with Parliament.
- SAMREC / SAMVAL: official PDFs at `https://www.samcode.co.za/`.

If a primary source moves, prefer the most recent consolidated version
and update the citation in `manifest.json`.
