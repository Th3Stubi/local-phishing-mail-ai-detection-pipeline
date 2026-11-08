# Data sources

The data itself is **not** stored in Git. This file only lists where it comes from.

| Source | Link | License | Retrieval date | SHA-256 |
|---|---|---|---|---|
| (none added yet) | | | | |

Folders (all ignored by Git, created when needed):

- `raw/` original mbox/eml files, never changed
- `interim/` cleaned emails, one `.eml` per email, no duplicates
- `processed/` later rewrite levels and the metadata table (`metadata.csv`: source, year, hash)
