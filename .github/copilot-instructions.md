## Repository Snapshot

This repository stores model artifacts and minimal tooling for a local RAG/LLM workflow. The primary content is under [models/stablelm-3b/README.md](models/stablelm-3b/README.md) and the downloader script [download.sh](download.sh).

## Big Picture (what an AI agent must know)
- **Purpose**: Keep and package LLM model artifacts for local experiments and deployment. The repo is not a full application — it focuses on model files and a small helper script.
- **Where to look**: `models/stablelm-3b/` contains model config, tokenizer, and weights (e.g., `model.safetensors`, `tokenizer.json`, `modeling_stablelm.py`). See [models/stablelm-3b/README.md](models/stablelm-3b/README.md) for usage examples.
- **Key workflow**: `download.sh` uses the `hf` CLI to fetch a Hugging Face model and then packages it to `model.tar.gz`.

## Developer workflows (concrete steps)
- Fetch and package the model (used by CI/deploy):

```bash
./download.sh
```

- Requirements implied by scripts:
  - The `hf` CLI (Hugging Face) must be available and authenticated on the runner.
  - Enough disk space to store the model (multi-GB/safetensors).

## Project-specific conventions and patterns
- **Models-as-artifacts**: Models live under `models/` and are expected to be self-contained directories (config, weights, tokenizer). Keep this layout when adding new models.
- **Packaging**: The repo uses tarball packaging (`tar -czvf model.tar.gz stablelm-3b`) as the canonical packaged artifact for downstream steps.
- **Transformer-compatible layout**: The stablelm directory contains files and small Python adapters (`configuration_stablelm.py`, `modeling_stablelm.py`) intended to be loadable by Hugging Face-style code. Use the README's code snippet as the canonical loading pattern.

## Integration points & external dependencies
- `hf` CLI / Hugging Face hub: used by `download.sh` to fetch models.
- Consumers expect a packaged model directory or tarball — look for `model.tar.gz` in CI/deploy scripts.

## Useful examples to follow (from this repo)
- Loading example (see [models/stablelm-3b/README.md](models/stablelm-3b/README.md)) — the repository's README shows how to call `AutoTokenizer` and `AutoModelForCausalLM` and how to enable `flash_attention_2`.
- Packaging example: `cd models && tar -czvf model.tar.gz stablelm-3b` (from [download.sh](download.sh)).

## What to avoid / assumptions not present
- There are no application server files, inference endpoints, or dataset ingestion pipelines in this repo — an agent should not assume higher-level orchestration exists here.
- Do not modify model weights or large binary files in-place in PRs; provide guidance or scripts to re-generate artifacts instead.

## When you need more context (questions to ask the developer)
- Where are inference/deployment scripts that consume `model.tar.gz` located? (If outside this repo, ask for the target repo.)
- Do you want automated model checksum verification and smaller manifest files added alongside the tarball?

---
If any section is unclear or you want more detail (e.g., CI hooks, expected manifest schema, or packaging variants), tell me which area to expand and I will iterate.
