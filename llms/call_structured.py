from __future__ import annotations

from typing import Type, TypeVar

from langfuse import get_client
from litellm import completion
from pydantic import BaseModel
from smartpy.utility.log_util import getLogger

from core.schemas import Settings

logger = getLogger(__name__)
langfuse = get_client()

T = TypeVar("T", bound=BaseModel)


def _extract_json(content: str) -> str:
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end < start:
        return content
    return content[start : end + 1]


def call_structured_llm(
    messages: list[dict[str, str]],
    response_model: Type[T],
    model: str,
    settings: Settings,
    temperature: float | None = None,
    retries: int = 5,
    retry_message: str | None = (
        "Your previous reply was invalid or truncated. "
        "Return only compact valid JSON. "
        "Shorten every long string aggressively. "
    ),
    langfuse_name: str | None = None,
    langfuse_metadata: dict | None = None,
) -> T:
    base_messages = messages
    max_tokens = settings.llm_max_tokens
    temp = settings.llm_temperature if temperature is None else temperature
    logger.info("LLM call start model=%s structured=%s traced=%s", model, response_model.__name__, bool(langfuse_name))

    if not langfuse_name:
        return _call_with_retries(base_messages, response_model, model, temp, max_tokens, retries, retry_message)

    input_text = "\n\n".join(f"[{m['role']}]: {m.get('content', '')}" for m in messages)

    with langfuse.start_as_current_observation(name=langfuse_name, as_type="generation") as gen:
        gen.update(
            input=input_text,
            model=model.split("/")[-1],
            model_parameters={
                "model": model.split("/")[-1],
                "temperature": temp,
                "max_tokens": max_tokens,
            },
            metadata=langfuse_metadata or {},
        )

        result = _call_with_retries(base_messages, response_model, model, temp, max_tokens, retries, retry_message)

        gen.update(
            output=result.model_dump_json(),
            metadata=langfuse_metadata or {},
        )
    logger.info("LLM call done model=%s structured=%s", model, response_model.__name__)

    return result


def _call_with_retries(
    base_messages: list[dict[str, str]],
    response_model: Type[T],
    model: str,
    temperature: float,
    max_tokens: int,
    retries: int,
    retry_message: str | None,
) -> T:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            logger.info("LLM attempt=%s/%s model=%s max_tokens=%s", attempt + 1, retries, model, max_tokens)
            retry_messages = base_messages
            if attempt > 0 and retry_message:
                retry_messages = [
                    *base_messages,
                    {"role": "user", "content": retry_message},
                ]
            response = completion(
                model=model,
                messages=retry_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_model,
            )
            finish_reason = response.choices[0].finish_reason
            if finish_reason == "length":
                logger.info("LLM truncated model=%s new_max_tokens=%s", model, max_tokens * 2)
                max_tokens *= 2
                continue
            content = _extract_json(response.choices[0].message.content or "{}")
            return response_model.model_validate_json(content)
        except Exception as exc:
            last_error = exc
            logger.warning("LLM attempt failed model=%s error=%s", model, str(exc))
    raise RuntimeError(str(last_error) if last_error else "LLM call failed")
