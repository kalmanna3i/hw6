"""Campus Customs vendor desk agent — entry point."""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    import httpx
except ImportError:  # this machine's OpenAI package vendors httpx as httpx2
    import httpx2 as httpx

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from models import VendorQuote
from policy import lock_answer
from tools import (
    approve_payment,
    audit_snapshot,
    load_document_text,
    read_document,
    reset_audit,
    send_email,
    set_defenses,
)
import tools as tools_mod

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
_JSON_LOCK = threading.Lock()

PRICES = json.loads((ROOT / "data" / "prices.json").read_text())["gpt-6-luna"]
HANDBOOK = (ROOT / "data" / "shop_handbook.md").read_text()
PROMPT = (ROOT / "prompts" / "prompt.md").read_text()


def cost_usd(
    input_tokens: int,
    cached_tokens: int,
    output_tokens: int,
    cache_write_tokens: int = 0,
) -> float:
    # Cached reads are a subset of input tokens. Cache writes are too, when the
    # API reports them inside the same input total (prices.json bills writes higher).
    write = max(cache_write_tokens, 0)
    read = max(cached_tokens, 0)
    if read + write <= input_tokens:
        uncached = input_tokens - read - write
    else:
        uncached = max(input_tokens - read, 0)
    return (
        uncached / 1_000_000 * PRICES["input_per_1m"]
        + read / 1_000_000 * PRICES["cached_input_per_1m"]
        + write / 1_000_000 * PRICES["cache_write_per_1m"]
        + output_tokens / 1_000_000 * PRICES["output_per_1m"]
    )


async def _bust_each_request(request: httpx.Request) -> None:
    """Give every API call a new first message so no prefix can be reused."""
    try:
        body = json.loads(request.content.decode())
    except Exception:
        return
    messages = body.get("messages")
    if not isinstance(messages, list):
        return
    messages.insert(
        0,
        {"role": "system", "content": f"nocache {uuid.uuid4()} {time.time_ns()}"},
    )
    payload = json.dumps(body).encode()
    request.stream = httpx.ByteStream(payload)
    request.headers["content-length"] = str(len(payload))


def make_agent(*, use_cache: bool = True) -> Agent[None, VendorQuote]:
    api_key = os.environ.get("PORTKEY_API_KEY")
    if not api_key or api_key in {"your_portkey_api_key_here", "your_real_key"}:
        raise SystemExit("Set a real PORTKEY_API_KEY in .env")

    headers = {"x-portkey-api-key": api_key}
    http_client = None
    if not use_cache:
        headers["x-portkey-cache-force-refresh"] = "true"
        http_client = httpx.AsyncClient(event_hooks={"request": [_bust_each_request]})
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=os.environ.get("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
        default_headers=headers,
        http_client=http_client,
    )
    model_name = os.environ.get("OPENAI_MODEL", "gpt-6-luna")
    model = OpenAIChatModel(model_name, provider=OpenAIProvider(openai_client=client))

    system = PROMPT + "\n\n# Shop handbook\n\n" + HANDBOOK
    if not use_cache:
        # Prompt caches match a stable prefix. A nonce has to come first or the
        # handbook is still reused and the "without cache" setup is not real.
        system = f"nocache {uuid.uuid4()} {time.time_ns()}\n\n" + system

    agent: Agent[None, VendorQuote] = Agent(
        model,
        output_type=VendorQuote,
        system_prompt=system,
        tools=[read_document, send_email, approve_payment],
    )
    return agent


def append_json(path: Path, item: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _JSON_LOCK:
        data: list = []
        if path.exists():
            try:
                loaded = json.loads(path.read_text())
                if isinstance(loaded, list):
                    data = loaded
            except json.JSONDecodeError:
                data = []
        data.append(item)
        path.write_text(json.dumps(data, indent=2))


def run_doc(
    doc: str,
    *,
    use_cache: bool = True,
    setup: str | None = None,
    defenses: bool = True,
) -> dict:
    set_defenses(defenses)
    tools_mod.DEFENSES_ON = defenses
    reset_audit()
    agent = make_agent(use_cache=use_cache)
    doc_path = str(Path(doc))
    prompt = (
        f"Read the vendor document at path `{doc_path}` using the read_document tool. "
        "Extract the quote fields and decide recommend or do_not_recommend using the handbook."
    )
    settings = OpenAIChatModelSettings(openai_reasoning_effort="none")
    result = agent.run_sync(prompt, model_settings=settings)
    usage = result.usage
    input_tokens = getattr(usage, "input_tokens", 0) or 0
    output_tokens = getattr(usage, "output_tokens", 0) or 0
    cached_tokens = int(getattr(usage, "cache_read_tokens", 0) or 0)
    details = getattr(usage, "details", None)
    if isinstance(details, dict):
        cached_tokens = int(
            details.get("cache_read_tokens")
            or details.get("cached_tokens")
            or cached_tokens
            or 0
        )
    # Fall back: inspect raw response usage if present
    try:
        for m in reversed(result.all_messages()):
            raw = getattr(m, "usage", None)
            if raw is None:
                continue
            cached_tokens = int(
                getattr(raw, "cache_read_tokens", 0)
                or getattr(getattr(raw, "prompt_tokens_details", None), "cached_tokens", 0)
                or cached_tokens
                or 0
            )
            break
    except Exception:
        pass

    cache_write_tokens = int(getattr(usage, "cache_write_tokens", 0) or 0)
    if isinstance(details, dict):
        cache_write_tokens = int(
            details.get("cache_write_tokens") or cache_write_tokens or 0
        )

    dollars = cost_usd(input_tokens, cached_tokens, output_tokens, cache_write_tokens)
    out = result.output
    answer = out.model_dump()
    if defenses:
        visible, _hits = load_document_text(doc_path)
        answer = lock_answer(visible, answer)
    record = {
        "document": doc_path,
        "time": datetime.now(timezone.utc).isoformat(),
        "setup": setup or ("with_cache" if use_cache else "without_cache"),
        "input_tokens": input_tokens,
        "cached_tokens": cached_tokens,
        "cache_write_tokens": cache_write_tokens,
        "output_tokens": output_tokens,
        "cost_usd": dollars,
        "answer": answer,
        "tool_calls": audit_snapshot(),
    }
    append_json(ROOT / "output" / "usage_log.json", {
        "document": doc_path,
        "time": record["time"],
        "input_tokens": input_tokens,
        "cached_tokens": cached_tokens,
        "cache_write_tokens": cache_write_tokens,
        "output_tokens": output_tokens,
        "cost_usd": dollars,
        "setup": record["setup"],
    })
    append_json(ROOT / "output" / "audit_trail.json", {
        "document": doc_path,
        "time": record["time"],
        "tool_calls": audit_snapshot(),
        "final_answer": answer,
    })
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Campus Customs vendor desk agent")
    parser.add_argument("--doc", required=True, help="Path to vendor document")
    parser.add_argument("--no-cache", action="store_true", help="Bust prompt cache")
    parser.add_argument("--no-defenses", action="store_true", help="Run with defenses off")
    args = parser.parse_args()
    record = run_doc(args.doc, use_cache=not args.no_cache, defenses=not args.no_defenses)
    print(json.dumps(record["answer"], indent=2))
    print(
        f"tokens in={record['input_tokens']} cached={record['cached_tokens']} "
        f"write={record['cache_write_tokens']} "
        f"out={record['output_tokens']} cost=${record['cost_usd']:.6f}"
    )


if __name__ == "__main__":
    main()
