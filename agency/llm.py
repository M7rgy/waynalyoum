"""Thin Claude API wrapper: cached system prompt, JSON-only replies, optional Batch API (50% cheaper, slower)."""
import json
import os
import re
import time

from common import config, prompt, log

_client = None


def client():
    global _client
    if _client is None:
        import anthropic  # pip install anthropic
        ws = os.environ.get("ANTHROPIC_WORKSPACE_ID", "").strip()
        # Keys not scoped to a workspace must send this header on every request.
        headers = {"anthropic-workspace-id": ws} if ws else None
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], default_headers=headers)
    return _client


def _system(role_prompt):
    # Brand Bible first + cache_control: identical prefix every call -> cache hits on re-runs/regens.
    return [
        {"type": "text", "text": prompt("brand_bible"), "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": role_prompt},
    ]


def _text(message):
    """Join only the text blocks (skips thinking / other block types)."""
    return "".join(b.text for b in message.content if getattr(b, "type", "") == "text")


def _parse_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start = min([i for i in (text.find("["), text.find("{")) if i >= 0], default=0)
    return json.loads(text[start:])


def ask(agent, role_prompt_name, user_payload):
    """agent: 'gatekeeper' | 'creative'. Returns parsed JSON."""
    cfg = config()
    model, max_tokens = cfg["models"][agent], cfg["max_tokens"][agent]
    params = {
        "model": model,
        "max_tokens": max_tokens,
        "system": _system(prompt(role_prompt_name)),
        "messages": [{"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}],
    }
    if cfg.get("use_batch_api"):
        text, usage = _via_batch(params)
    else:
        with client().messages.stream(**params) as stream:  # streaming avoids timeouts on long replies
            resp = stream.get_final_message()
        text, usage = _text(resp), resp.usage
        if getattr(resp, "stop_reason", "") == "max_tokens":
            raise RuntimeError(f"{agent}: reply was cut off — raise max_tokens.{agent} in config.json")
    log(f"llm[{agent}] {model} in={getattr(usage,'input_tokens','?')} "
        f"cache_read={getattr(usage,'cache_read_input_tokens',0)} out={getattr(usage,'output_tokens','?')}")
    return _parse_json(text)


def _via_batch(params, poll_every=30, timeout_s=3600):
    c = client()
    batch = c.messages.batches.create(requests=[{"custom_id": "job", "params": params}])
    t0 = time.time()
    while True:
        b = c.messages.batches.retrieve(batch.id)
        if b.processing_status == "ended":
            break
        if time.time() - t0 > timeout_s:
            raise TimeoutError("batch did not finish in time")
        time.sleep(poll_every)
    for res in c.messages.batches.results(batch.id):
        if res.result.type == "succeeded":
            m = res.result.message
            return _text(m), m.usage
        raise RuntimeError(f"batch failed: {res.result}")
