# Data sources

The data itself is **not** stored in Git. This file only lists where it comes from.

| Source                                 | Link                                             | License                                                                   | Retrieval date     | SHA-256 |
| -------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------- | ------------------ | ------- |
| Nazario Phishing Corpus (Jose Nazario) | [monkey.org](https://monkey.org/~jose/phishing/) | CC-BY-4.0 ([license text](https://monkey.org/~jose/phishing/LICENSE.txt)) | November 8th, 2026 |         |

The pipeline only processes the data locally. Anyone who wants to use it downloads the data from the source above.

Folders (all ignored by Git, created when needed):

- `raw/` original mbox/eml files, never changed
- `interim/` cleaned emails, one `.eml` per email, no duplicates
- `processed/` later rewrite levels and the metadata table (`metadata.csv`: source, year, hash)
