# Email parser

Module: `src/phishpipe/parser.py`. It uses only the Python standard library (`mailbox`, `email`) for parsing.

## Run

```
python -m phishpipe.parser <mbox-file-or-folder> [--config config.yaml]
```

The input is one mbox file or a folder with `.eml` files. Settings come from `config.yaml`.

## Rules

- One `.eml` per email is written to `data/interim/`. The file name is the SHA-256 hash of the cleaned email.
- Duplicates (same hash) are skipped, also across several runs.
- Placeholder entries of mbox files ("folder internal data") are skipped.
- The `Date` header is kept. Only emails dated **before 2022-12-01 (UTC)** are kept. A date without time zone is read as UTC.
- Emails with a missing or invalid `Date` are skipped and logged.
- Attachments and non-text parts are removed. Links are never opened and nothing is executed.
- A table `data/processed/metadata.csv` is written with the columns `source`, `year`, `hash`.

## Logs

The log shows only counts and reasons (`placeholder`, `missing_date`, `invalid_date`, `too_new`, `duplicate`) with the source name and the position of the email. It never shows subjects, addresses or text.
