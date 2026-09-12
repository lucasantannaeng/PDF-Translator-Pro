#!/usr/bin/env python3
"""
Benchmark & Roteador de Modelos de IA (v3.1)
Executa benchmark sintético de latência e acurácia nos modelos do FreeLLM Proxy
e atualiza o mapa de roteamento (model_routing.json) com ZERO ALUCINAÇÃO.

Fix v3.1: usa IDs reais do catálogo atual (catalog refresh), mede TTFT real,
tokens/seg reais, e valida JSON de forma determinística.
"""
import json
import time
import requests
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = os.getenv("FREELLM_API_KEY", "")
BASE = os.getenv("FREELLM_BASE_URL", "http://127.0.0.1:31415/v1").rstrip("/")
COMPLETIONS = BASE + "/chat/completions"

# Pool de modelos alvo (IDs verificados contra o catálogo em 2026-09-11)
MODELS_TO_TEST = {
    "DeepSeek V4 Pro": "deepseek-v4-pro",
    "Qwen 3.5 397B": "qwen3.5-397b-a17b",
    "Gemini 3.6 Flash": "gemini-3.6-flash",
    "Nemotron 3 Ultra 550B": "nemotron-3-ultra-550b",
    "Codestral": "codestral",
    "GLM 5.2": "glm-5.2",
    "MiMo V2.5 Pro": "mimo-v2.5-pro",
    "DeepSeek V4 Flash": "deepseek-v4-flash",
}

JSON_PROMPT = (
    'Return a valid JSON object with these keys: "name" (string), '
    '"age" (integer), "city" (string). '
    'Example: {"name": "John", "age": 30, "city": "New York"}. '
    'Output ONLY the JSON object, no markdown fences, no extra text.'
)

LATENCY_PROMPT = "Hello, how are you? Respond in one short sentence."


def _headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def measure_latency(model_id):
    """Physically measures TTFT and tokens/sec over real HTTP stream."""
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": LATENCY_PROMPT}],
        "max_tokens": 60,
        "temperature": 0.0,
        "stream": True,
    }
    try:
        start = time.time()
        resp = requests.post(COMPLETIONS, headers=_headers(), json=data,
                             stream=True, timeout=60)
        ttft = None
        pieces = []
        for raw in resp.iter_lines():
            if not raw:
                continue
            if ttft is None:
                ttft = time.time() - start
            line = raw.decode("utf-8", "replace")
            if line.startswith("data: "):
                payload = line[6:]
                if payload.strip() == "[DONE]":
                    break
                try:
                    obj = json.loads(payload)
                except (json.JSONDecodeError, ValueError):
                    continue
                choices = obj.get("choices") or []
                if choices:
                    delta = choices[0].get("delta") or {}
                    tok = delta.get("content")
                    if tok:
                        pieces.append(tok)
        total = time.time() - start
        if ttft is None:
            ttft = total
        out_text = "".join(pieces).strip()
        n_tokens = len(out_text.split())
        tps = n_tokens / total if total > 0 else 0.0
        # Error detection: a 429/4xx stream returns an error JSON body, not SSE.
        if resp.status_code != 200:
            return {
                "model": model_id, "status": f"HTTP {resp.status_code}",
                "ttft_ms": None, "tokens_per_sec": None, "output": out_text[:120],
                "total_time_s": total,
            }
        return {
            "model": model_id, "status": "success",
            "ttft_ms": round(ttft * 1000, 2),
            "total_time_s": round(total, 4),
            "tokens_per_sec": round(tps, 2),
            "output": out_text,
        }
    except Exception as e:
        return {"model": model_id, "status": f"error: {e}",
                "ttft_ms": None, "tokens_per_sec": None, "output": ""}


def validate_json(model_id):
    """Non-streaming JSON-validity check with strict key/type assertion."""
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": JSON_PROMPT}],
        "max_tokens": 80,
        "temperature": 0.0,
    }
    try:
        resp = requests.post(COMPLETIONS, json=data, headers=_headers(),
                             timeout=60)
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        content = (resp.json().get("choices", [{}])[0]
                   .get("message", {}).get("content", ""))
        cand = _extract_json_object(content)
        if cand is None:
            return False, f"FAIL: no JSON - {content[:80]}"
        parsed = json.loads(cand)
        if (set(parsed.keys()) == {"name", "age", "city"}
                and isinstance(parsed.get("name"), str)
                and isinstance(parsed.get("age"), int)
                and isinstance(parsed.get("city"), str)):
            return True, "PASS"
        return False, f"FAIL: wrong keys/types - {parsed}"
    except Exception as e:
        return False, f"Exception: {e}"


def _extract_json_object(text):
    """Pull the first balanced {...} JSON object from possibly-fenced output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(l for l in lines if not l.strip().startswith("```"))
        text = text.strip()
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def main():
    print("=== FreeLLM benchmark v3.1 ===\n")
    results = {}
    # Phase 1: latency (parallel, but capped)
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(measure_latency, mid): name
                for name, mid in MODELS_TO_TEST.items()}
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                results[name] = fut.result()
            except Exception as e:
                results[name] = {"model": MODELS_TO_TEST[name],
                                 "status": f"error: {e}"}

    # Phase 2: JSON validity only for successes with real tokens
    successful = {n: r for n, r in results.items() if r.get("status") == "success"}
    for name, res in successful.items():
        print(f"[latency] {name}: TTFT {res['ttft_ms']} ms, "
              f"{res['tokens_per_sec']} tok/s, out={res['output'][:40]!r}")
        if res.get("tokens_per_sec", 0) > 0:
            valid, msg = validate_json(res["model"])
            res["json_valid"] = valid
            res["json_msg"] = msg
            print(f"   [json]   {name}: {msg}")
        else:
            res["json_valid"] = False
            res["json_msg"] = "skipped: no tokens generated"
    for name, res in results.items():
        if res.get("status") != "success":
            print(f"[fail]     {name}: {res.get('status')}")

    # Rank: prefer valid-JSON + lowest TTFT with real token throughput
    ranked = sorted(
        successful.values(),
        key=lambda r: (not r.get("json_valid"), r.get("ttft_ms", 1e9)),
    )
    top3 = ranked[:3]

    print("\n=== Top 3 (JSON-valid first, then TTFT) ===")
    for r in top3:
        print(f"  {r['model']}: TTFT {r['ttft_ms']} ms, "
              f"{r['tokens_per_sec']} tok/s, JSON {r.get('json_valid')}")

    routing = {
        "timestamp": time.time(),
        "top_models": [
            {
                "name": next(k for k, v in MODELS_TO_TEST.items() if v == r["model"]),
                "model": r["model"],
                "ttft_ms": r["ttft_ms"],
                "tokens_per_sec": r["tokens_per_sec"],
                "json_valid": r.get("json_valid", False),
            }
            for r in top3
        ],
        "full_results": results,
    }

    with open("model_routing.json", "w", encoding="utf-8") as f:
        json.dump(routing, f, indent=2, ensure_ascii=False)
    print(f"\nSaved routing -> {os.path.abspath('model_routing.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())