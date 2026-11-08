# Pipeline: steps and results

This page describes what happens in the project, step by step, and what you have after each step. It is updated together with the code. Each step has the same fields.

## Overview

| # | Step | Result after this step | Status |
|---|---|---|---|
| 1 | Raw data | mbox/eml files in `data/raw/` (not in Git) | manual |
| 2 | Parse and clean | one cleaned `.eml` per email in `data/interim/`, plus `metadata.csv` | done |
| 3 | URL masking | email text with `{{URL_n}}` placeholders instead of links | planned |
| 4 | Integrity checks | a mail is accepted only if headers and URLs are unchanged | planned |
| 5 | LLM rewrite | levels Q1 (errors fixed) and Q2 (professional) in `data/processed/` | planned |
| 6 | Baseline classifier | detection results per level: text, metadata, hybrid | planned |

Q0 is the original text and needs no rewrite. Q3 (personalized) is optional.

## 1. Raw data

- **What happens:** The raw files are downloaded or copied by hand to `data/raw/`. They are never changed, opened in a mail program, or put into Git or a cloud sync.
- **Input:** public corpora. First source: Nazario Phishing Corpus (CC-BY-4.0), mbox file per year, starting with 2015.
- **Output:** files in `data/raw/`. Source, license, retrieval date and SHA-256 of each file are listed in `data/README.md`.
- **Rules:** never open links or attachments. Only English emails, only emails from before 2022-12-01.
- **Command:** none yet (a download script is planned).
- **Status:** manual.

## 2. Parse and clean

- **What happens:** Each email is read from an mbox file or a folder of `.eml` files. Placeholder entries, emails without a valid `Date` header, emails from 2022-12-01 or later, and duplicates are dropped. Attachments are removed. Headers stay as they are.
- **Input:** one mbox file or one folder with `.eml` files.
- **Output:**
  - `data/interim/<sha256>.eml`: one cleaned email per file
  - `data/processed/metadata.csv`: columns `source`, `year`, `hash`
  - a log with counts per reason (never mail content)
- **Rules and checks:** see [parser.md](parser.md). Windows paths work (`pathlib`).
- **Command:** `python -m phishpipe.parser data/raw/<file-or-folder>`
- **Result of the first run** (`phishing-2015`, numbers only): 307 emails read, 1 placeholder skipped, 1 without `Date` skipped, 305 written.
- **Status:** done.

## 3. URL masking

- **What happens:** In the plain text part of an email, every link (`http://`, `https://`, `www.`) is replaced by a placeholder `{{URL_1}}`, `{{URL_2}}`, and so on. Every link occurrence gets its own placeholder. Email addresses stay in the text. The LLM later sees only the placeholders, never real links or headers.
- **Input:** a cleaned `.eml` from `data/interim/`.
- **Output:** the masked text and the list of original URLs.
- **Rules and checks:** only the `text/plain` part counts as text. Emails without such a part are logged and skipped for now.
- **Command:** none yet (library functions first).
- **Status:** planned.

## 4. Integrity checks

- **What happens:** Python (not the LLM) checks every rewritten email: headers identical, every placeholder exactly once, URLs identical after they are put back. A failed email is dropped and logged. The original is never inserted silently.
- **Input:** the original email, the rewritten email and the URL list.
- **Output:** a list of failure reasons (empty list means accepted).
- **Rules and checks:** reason codes are short words, never mail content.
- **Command:** none yet.
- **Status:** planned.

## 5. LLM rewrite (Q1, Q2)

- **What happens:** A local model through Ollama rewrites only the masked text, once per level. Q1 fixes language errors, Q2 rewrites in a professional style. Refusals and empty answers are logged.
- **Model:** set in `config.yaml` (not in the code).
- **Output:** one rewritten email per level in `data/processed/`. Model, prompt and duration are logged for each run. The seed comes from `config.yaml`.
- **Status:** planned.

## 6. Baseline classifier

- **What happens:** A simple classifier (TF-IDF with logistic regression) is tested on each level in three variants: **text** (only the mail text), **metadata** (only headers and links), and **hybrid** (text and metadata together).
- **Why hybrid:** it shows whether metadata can make up for the loss when the rewritten text no longer looks suspicious.
- **Output:** precision, recall and F1 per level (and per source where possible).
- **Status:** planned.
