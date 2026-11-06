"""Campus Customs vendor desk agent — entry point."""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from models import VendorQuote
from tools import (
    AUDIT_BUF,
    approve_payment,
    read_document,
    reset_audit,
    send_email,
)

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

PRICES = json.loads((ROOT / "data" / "prices.json").read_text())["gpt-6-luna"]
HANDBOOK = (ROOT / "data" / "shop_handbook.md").read_text()
PROMPT = (ROOT / "prompts" / "prompt.md").read_text()


def cost_usd(input_tokens: int, cached_tokens: int, output_tokens: int) -> float:
    uncached = max(input_tokens - cached_tokens, 0)
    return (
        uncached / 1_000_000 * PRICES["input_per_1m"]
        + cached_tokens / 1_000_000 * PRICES["cached_input_per_1m"]
        + output_tokens / 1_000_000 * PRICES["output_per_1m"]
    )


def make_agent(*, use_cache: bool = True) -> Agent[None, VendorQuote]:
    api_key = os.environ.get("PORTKEY_API_KEY")
    if not api_key or api_key in {"your_portkey_api_key_here", "your_real_key"}:
        raise SystemExit("Set a real PORTKEY_API_KEY in .env")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=os.environ.get("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
        default_headers={"x-portkey-api-key": api_key},
    )
    model_name = os.environ.get("OPENAI_MODEL", "gpt-6-luna")
    model = OpenAIChatModel(model_name, provider=OpenAIProvider(openai_client=client))

    system = PROMPT + "\n\n# Shop handbook\n\n" + HANDBOOK
    if not use_cache:
        # Bust prompt cache by appending a unique nonce each agent build.
        system = system + f"\n\n<!-- cache_bust:{time.time_ns()} -->\n"

    agent: Agent[None, VendorQuote] = Agent(
        model,
        output_type=VendorQuote,
        system_prompt=system,
        tools=[read_document, send_email, approve_payment],
    )
    return agent


def append_json(path: Path, item: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def run_doc(doc: str, *, use_cache: bool = True, setup: str | None = None) -> dict:
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

    dollars = cost_usd(input_tokens, cached_tokens, output_tokens)
    out = result.output
    answer = out.model_dump()
    record = {
        "document": doc_path,
        "time": datetime.now(timezone.utc).isoformat(),
        "setup": setup or ("with_cache" if use_cache else "without_cache"),
        "input_tokens": input_tokens,
        "cached_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "cost_usd": dollars,
        "answer": answer,
        "tool_calls": list(AUDIT_BUF),
    }
    append_json(ROOT / "output" / "usage_log.json", {
        "document": doc_path,
        "time": record["time"],
        "input_tokens": input_tokens,
        "cached_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "cost_usd": dollars,
        "setup": record["setup"],
    })
    append_json(ROOT / "output" / "audit_trail.json", {
        "document": doc_path,
        "time": record["time"],
        "tool_calls": list(AUDIT_BUF),
        "final_answer": answer,
    })
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Campus Customs vendor desk agent")
    parser.add_argument("--doc", required=True, help="Path to vendor document")
    parser.add_argument("--no-cache", action="store_true", help="Bust prompt cache")
    args = parser.parse_args()
    record = run_doc(args.doc, use_cache=not args.no_cache)
    print(json.dumps(record["answer"], indent=2))
    print(
        f"tokens in={record['input_tokens']} cached={record['cached_tokens']} "
        f"out={record['output_tokens']} cost=${record['cost_usd']:.6f}"
    )


if __name__ == "__main__":
    main()
