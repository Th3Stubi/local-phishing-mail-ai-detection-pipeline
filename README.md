# Detection Pipeline for AI-Rewritten Phishing Emails

Modern LLMs write phishing texts that are error-free and convincing. Classic text-based and pattern-based filters lose clues such as spelling mistakes. This project builds a reproducible test dataset, created locally, to measure how much detection suffers when the text is rewritten.

## Idea
Real phishing emails from before modern LLMs are read in. **Headers and links stay unchanged, only the text** is rewritten by a local LLM in quality levels:

| Level | Content |
|---|---|
| Q0 | original |
| Q1 | language errors fixed |
| Q2 | rewritten in a professional style |
| Q3 | personalized, very convincing (optional) |

## Goals and success criteria
- **K1 Dataset:** at least 1,000 phishing emails for each of Q0, Q1 and Q2, plus at least 1,000 legitimate emails
- **K2 Unchanged:** headers and links stay 100% identical in all levels (checked automatically)
- **K3 Traceable:** model and prompts documented for each level, a sample checked by hand, language errors drop from Q0 to Q2
- **K4 First detection test:** a simple classifier is tested on each level
- **K5 Repeatable:** runs locally without cloud services, with a fixed seed, and can be followed from the instructions

Not part of this repo: the comparison of detection methods and the answer to the research question (planned for the bachelor thesis). Also out of scope: attachments and images, gateway integration, cloud services.

## Pipeline overview
Details and the result after each step: [docs/pipeline.md](docs/pipeline.md).

1. Download raw data (mbox/eml) locally and check hashes
2. Parse, clean, remove duplicates (one `.eml` per email)
3. Replace URLs with placeholders, rewrite the text with a local LLM (Q1, Q2, optional Q3), put the URLs back
4. Python checks: headers and URLs unchanged, LLM refusals logged
5. Baseline classifier (text, metadata, hybrid), results per level

## Data
The data is **not** stored in this repo. It only contains scripts, configuration, source information and hashes (`data/README.md`).

- Phishing: [Nazario Phishing Corpus](https://monkey.org/~jose/phishing/), English emails, CC-BY-4.0 (credit required). Only emails from before December 2022 are used, at first just the year 2015.
- Legitimate emails: **open**
- Origin and license of the original emails must be checked before any dataset is published. The generated emails are used locally for research only and are never sent.

## Setup (rough steps)
Requirements: Python, [Ollama](https://ollama.com/download), an NVIDIA GPU with 6 GB VRAM (tested with GTX 1660 Ti on Windows).

1. Clone the repo, create a virtual environment and install the dependencies: `pip install -e .[dev]` (defined in `pyproject.toml`)
2. Download the model: `ollama pull gemma4:e4b`
3. Download and check the raw data (script follows: **open**)
4. Start the pipeline (command follows: **open**)

The model name is set in `config.yaml`. The model itself is not part of the repo.

## Parse emails
Put an mbox file or a folder with `.eml` files somewhere locally (for example in `data/raw/`) and run:

```
python -m phishpipe.parser data/raw/<file-or-folder>
```

Cleaned emails go to `data/interim/`, the metadata table to `data/processed/metadata.csv`. Run the tests with `pytest`. Details: [docs/parser.md](docs/parser.md).

See [docs/concept.md](docs/concept.md) for the full concept.

## License
TBD
