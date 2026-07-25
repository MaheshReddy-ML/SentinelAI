from __future__ import annotations

from collections.abc import Callable
from time import perf_counter

from models.llm.base_provider import RequestProvider
from models.llm.parser import RequestValidationError, parse_request_json
from models.llm.prompt_builder import build_request_prompt
from schemas.request import FinancialRequest

PRIMARY_MODEL = "Qwen/Qwen3-1.7B-MLX-4bit"
FALLBACK_MODEL = "Qwen/Qwen3-0.6B-MLX-4bit"


class LocalMLXProvider(RequestProvider):
    """MLX adapter with one retry; no governance logic lives in this class."""

    def __init__(self, model_id: str = PRIMARY_MODEL, generate_text: Callable[[str], str] | None = None) -> None:
        self.model_id = model_id
        self._generate_text = generate_text
        self._runtime: tuple[object, object, Callable[..., object], Callable[..., object]] | None = None
        self.last_extraction_ms: float | None = None
        self.last_validation_ms: float | None = None

    def generate_request(self, prompt: str, user_id: str | None = None) -> FinancialRequest:
        if not prompt.strip():
            raise RequestValidationError("Enter a financial request before analysis.")
        instruction = build_request_prompt(prompt)
        last_error: RequestValidationError | None = None
        for attempt in range(2):
            started = perf_counter()
            response = self._generate(instruction if attempt == 0 else instruction + "\nYour prior output was invalid. Return corrected JSON only.")
            self.last_extraction_ms = (perf_counter() - started) * 1000
            try:
                started = perf_counter()
                request = parse_request_json(response, user_id=user_id, source_prompt=prompt)
                self.last_validation_ms = (perf_counter() - started) * 1000
                request.metadata["_extraction_metrics"] = {"llm_ms": self.last_extraction_ms, "validation_ms": self.last_validation_ms}
                return request
            except RequestValidationError as error:
                last_error = error
        raise RequestValidationError(f"Unable to extract a valid request after one retry: {last_error}")

    def _generate(self, prompt: str) -> str:
        if self._generate_text is not None:
            return self._generate_text(prompt)
        try:
            from huggingface_hub.utils import disable_progress_bars
            from mlx_lm import generate, load
            from mlx_lm.sample_utils import make_sampler
        except ImportError as error:
            raise RequestValidationError("Local MLX is not installed. Run: python scripts/setup_local_llm.py") from error
        if self._runtime is None:
            disable_progress_bars()
            model, tokenizer = load(self.model_id)
            self._runtime = model, tokenizer, generate, make_sampler
        model, tokenizer, generate, make_sampler = self._runtime
        try:
            rendered = tokenizer.apply_chat_template([{"role": "user", "content": prompt}], add_generation_prompt=True, enable_thinking=False)
        except TypeError:
            rendered = tokenizer.apply_chat_template([{"role": "user", "content": prompt}], add_generation_prompt=True)
        return generate(
            model,
            tokenizer,
            prompt=rendered,
            max_tokens=1024,
            sampler=make_sampler(temp=0.0),
            verbose=False,
        )
