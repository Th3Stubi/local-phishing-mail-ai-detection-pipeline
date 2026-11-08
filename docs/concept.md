
# Concept: Detection Pipeline for AI-Rewritten Phishing Emails

Items marked **open** are not decided yet.

## 1. Starting point and problem

Modern LLMs let attackers write phishing texts that have no spelling errors and sound convincing. They can do this fast and in large numbers. Classic filters based on text and patterns often rely on exactly the clues that disappear: spelling mistakes, clumsy wording, typical phrases.

Pure AI solutions need a lot of computing power. They also tend to ignore technical features of an email (headers, routing, URLs) that do not change when only the text is rewritten.

To measure how much detection suffers when the text is rewritten, we need a dataset that combines real technical features with LLM-rewritten texts in defined quality levels. Such a dataset is missing.

## 2. Audience and purpose

**Audience:** people who build email security tools, operators of mail gateways, small companies without a security team, and anyone interested in cybersecurity.

**Purpose:** a reproducible test dataset that is created locally (no data leaves the machine). It can be used to test phishing filters against AI-written mails and to support a light detection layer in front of the mailbox.

## 3. Result and success criteria

The result is a Python pipeline (public repository). It reads phishing emails from the time before modern LLMs. It keeps headers and URLs unchanged and rewrites **only the text** with a local LLM in quality levels:

| Level | Content | Status |
|---|---|---|
| Q0 | original | required |
| Q1 | language errors fixed | required |
| Q2 | rewritten in a professional style | required |
| Q3 | personalized, very convincing | optional |

The pipeline also contains an integrity and quality check, a simple baseline classifier as proof of feasibility, a dataset description, and instructions.

- **K1 Dataset:** at least 1,000 phishing emails for each of Q0, Q1 and Q2, and at least 1,000 legitimate (ham) emails. Q3 only if there is enough time. The ham source is **open** (see section 5).
- **K2 Headers and URLs unchanged:** an automatic check confirms that headers and URLs stay 100% identical in all levels. Automatic tests for parsing and checking pass.
- **K3 Levels are traceable:** for each level, the model and the prompts are documented. A sample of 50 emails per level is checked by hand. The number of language errors drops from Q0 to Q2.
- **K4 First detection test:** a simple classifier is trained on the dataset and tested on each level. It shows how many phishing mails it still finds. This shows that the dataset is useful for later evaluation.
- **K5 Repeatable:** the pipeline runs locally with one command, without cloud services, and gives the same results on every run (fixed seed). A third person can run it by following the instructions. The command is **open**.

## 4. Approach

1. **Hardware and model.** Check the available computing power and choose a local LLM that runs through Ollama (quantized if needed). Current candidates: `gemma4:e4b` and `qwen3.5:9b` (final choice **open**). The model name is set in `config.yaml`.
2. **Data.** Use public datasets. Parse them, clean them, and remove duplicates (one `.eml` file per email).
3. **Rewrite.** Replace URLs with placeholders, rewrite the text with a prompt template per level, and put the URLs back.
4. **Check.** Python checks that headers and URLs are unchanged. Refusals and broken answers by the model are logged, never hidden.
5. **Baseline.** Train a simple classifier (TF-IDF with logistic regression) in three variants: text only, metadata only, and both together. Report results per level.
6. **Document.** Describe sources, licenses, models, prompts and results.

### Data rules

- **Language:** English emails only.
- **Time range:** only emails whose `Date` header is **before 1 December 2022**. ChatGPT was released on 30 November 2022, so these mails are very unlikely to be written by a modern LLM.
- **Raw data is never stored in Git.** The repository only holds scripts, configuration, and source information. Each source is documented with link, license, retrieval date, and hash in `data/README.md`. This is needed because of the licenses and because mails contain personal data. Licenses must be checked before anything is published.
- **Raw formats:** mbox and eml.
- **Phishing source:** the Nazario Phishing Corpus (CC-BY-4.0, mbox file per year). Start with the year 2015, then add more years up to 30 November 2022. The corpus is hand-classified and may contain errors, so a sample is checked by hand for each year.
- **Ham source: open.** For 2015 to 2022 there is no checked public source that keeps full headers. See `recherche/AP3_Datensaetze.md`, section 1c.
- **Collector headers.** Some corpora add their own headers (for example `X-Spam-Summary`). They must be removed or tested separately, so the classifier does not learn them.

### Dataset bias

Phishing and ham mails come from different sources and different times. A classifier can then learn the year, the mail software, or the topic instead of phishing. Countermeasures:

- Keep source and year as columns in the metadata table.
- Report results per level and, where possible, per source.
- Remove or separately test collector headers.
- Prefer a ham source from the same time range (the choice is **open**).

**Order of work:** build and test Q0 to Q2 with **phishing mails only** first. Add ham when the source question is solved.

## 5. Scope

In scope: English emails, text rewriting in levels, automatic integrity checks, a simple baseline classifier, documentation.

Out of scope:

- attachments and images
- a comparison of detection methods (this is done later, outside this repository)
- use inside a production mail gateway
- cloud services and external APIs
- local models larger than about 8 billion parameters
- sending the generated emails. They are used locally for research only.
- translation or German emails (only an idea for later)

## 6. Research question

The pipeline creates the measurable base for this question, which is answered outside this repository:

> By how much do precision, recall and F1 of a text-based phishing classifier drop for each quality level of the LLM-rewritten mails, and how much of this is made up by an approach that uses metadata (headers, URLs) or by a hybrid approach?
