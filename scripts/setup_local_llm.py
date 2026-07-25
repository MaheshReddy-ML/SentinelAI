#!/usr/bin/env python3
"""One-command MLX setup, download, warm-up, and latency check for SentinelAI."""

from __future__ import annotations

import subprocess
import sys
from time import perf_counter

MODEL = "Qwen/Qwen3-1.7B-MLX-4bit"


def main() -> None:
    if sys.platform != "darwin" or sys.version_info < (3, 12):
        raise SystemExit("SentinelAI local LLM setup requires Apple Silicon macOS and Python 3.12+.")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "mlx-lm>=0.25.2"], check=True)
    from mlx_lm import generate, load
    from mlx_lm.sample_utils import make_sampler

    started = perf_counter()
    model, tokenizer = load(MODEL)
    load_seconds = perf_counter() - started
    prompt = tokenizer.apply_chat_template([{"role": "user", "content": "Return exactly: {\"ready\":true}"}], add_generation_prompt=True)
    started = perf_counter()
    output = generate(model, tokenizer, prompt=prompt, max_tokens=16, sampler=make_sampler(temp=0.0), verbose=False)
    latency_ms = (perf_counter() - started) * 1000
    print(f"Model: {MODEL}\nLoad/warm-up: {load_seconds:.2f}s\n16-token latency: {latency_ms:.0f}ms\nOutput: {output}")


if __name__ == "__main__":
    main()
