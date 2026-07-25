# Local LLM setup

SentinelAI uses **`Qwen/Qwen3-1.7B-MLX-4bit`** through MLX as an extraction-only adapter. The 4-bit MLX model is roughly 1 GB, Apache-2.0 licensed, and keeps inference local on Apple Silicon. It is used solely to convert natural-language input to a `FinancialRequest`; JSON rules remain the only source of governance decisions.

Fallback: `Qwen/Qwen3-0.6B-MLX-4bit` for machines where lower memory use is more important than extraction quality.

## One-command setup

```bash
source .venv/bin/activate
python scripts/setup_local_llm.py
```

The script installs MLX-LM, downloads the selected model on first use, warms it up, and prints measured load and generation latency for the local machine. It requires native Apple Silicon Python 3.12+ and macOS 14+.

## Use the existing CLI

```bash
sentinel analyze --prompt "Book a business flight to New York tomorrow for $1250 using my corporate card."
```

In zsh, use single quotes for prompts containing `$` so the shell does not expand the amount:

```bash
sentinel analyze --prompt 'Book a business flight to New York tomorrow for $1250 using my corporate card.'
```

The CLI retries malformed model output once, validates it using the existing Pydantic request schema, and prints a structured extraction error instead of crashing. The rule-driven experts then produce the governance report.
