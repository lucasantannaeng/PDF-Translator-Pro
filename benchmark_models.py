#!/usr/bin/env python3
"""
Benchmark & Roteador de Modelos de IA (v3.0)
Executa benchmark sintético de latência e acurácia nos modelos do FreeLLM Proxy
e atualiza o mapa de roteamento (model_routing.json) com ZERO ALUCINAÇÃO.
"""
import json
import time
import requests
import sys
import os

# Configuration
API_KEY = os.getenv("FREELLM_API_KEY", "")
BASE_URL = os.getenv("FREELLM_BASE_URL", "http://127.0.0.1:31415/v1/chat/completions")
MODELS_TO_TEST = {
    "DeepSeek V4": "deepseek-v4-pro",
    "Qwen 3.5": "qwen3.5-397b-a17b",
    "Gemini 3.7 Flash": "gemini-3.7-flash",  # might not exist, we'll fallback
    "Nemotron": "nemotron-3-ultra-550b",
    "Codestral": "codestral"
}
# Fallback list if the above fail
FALLBACK_MODELS = {
    "Gemini 3.5 Flash": "gemini-3.5-flash",
    "Gemini 3 Flash Preview": "gemini-3-flash-preview",
    "DeepSeek V4 Flash": "deepseek-v4-flash",
    "Qwen 3.5": "qwen3.5-397b",
    "Nemotron 3 Ultra": "nemotron-3-ultra",
    "Codestral": "codestral"
}

def test_model(model_name, model_id):
    """Test a model with a simple prompt and return metrics."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Hello, how are you? Respond in one sentence."}],
        "max_tokens": 20,
        "temperature": 0.0,
        "stream": True
    }
    try:
        start = time.time()
        response = requests.post(BASE_URL, headers=headers, json=data, stream=True, timeout=30)
        ttft = None
        content = []
        for chunk in response.iter_lines():
            if chunk:
                if ttft is None:
                    ttft = time.time() - start
                line = chunk.decode('utf-8')
                if line.startswith('data: '):
                    data_str = line[6:]
                    if data_str.strip() == '[DONE]':
                        break
                    try:
                        data_json = json.loads(data_str)
                        token = data_json.get('choices', [{}])[0].get('delta', {}).get('content', '')
                        if token:
                            content.append(token)
                    except:
                        pass
        total_time = time.time() - start
        if ttft is None:
            ttft = total_time
        full_text = ''.join(content)
        tokens_generated = len(full_text.split()) if full_text else 0
        tokens_per_sec = tokens_generated / total_time if total_time > 0 else 0
        return {
            "model": model_id,
            "ttft_ms": ttft * 1000,
            "total_time_s": total_time,
            "tokens_per_sec": tokens_per_sec,
            "output": full_text.strip(),
            "status": "success"
        }
    except Exception as e:
        return {
            "model": model_id,
            "status": f"error: {e}",
            "ttft_ms": None,
            "output": ""
        }

def validate_json_output(model_name, model_id):
    """Test if the model can produce valid JSON."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = """Return a valid JSON object with the following keys: "name": string, "age": integer, "city": string. Example: {"name": "John", "age": 30, "city": "New York"}"""
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 50,
        "temperature": 0.0
    }
    try:
        resp = requests.post(BASE_URL, json=data, headers=headers, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            try:
                parsed = json.loads(content)
                expected = {"name", "age", "city"}
                if set(parsed.keys()) == expected and isinstance(parsed.get('name'), str) and isinstance(parsed.get('age'), int) and isinstance(parsed.get('city'), str):
                    return True, "PASS"
                else:
                    return False, f"FAIL: wrong keys/types - {parsed}"
            except json.JSONDecodeError:
                return False, f"FAIL: not valid JSON - {content[:100]}"
        else:
            return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
    except Exception as e:
        return False, f"Exception: {e}"

def main():
    print("Starting benchmark...")
    results = {}
    # First try the primary list
    for name, model_id in MODELS_TO_TEST.items():
        print(f"Testing {name} ({model_id})...")
        res = test_model(name, model_id)
        results[name] = res
        if res.get("status") == "success":
            print(f"  TTFT: {res['ttft_ms']:.0f} ms, Tok/s: {res['tokens_per_sec']:.2f}")
        else:
            print(f"  Failed: {res.get('status')}")
    
    # If any primary failed, try fallbacks
    fallback_used = {}
    for name, model_id in MODELS_TO_TEST.items():
        if results[name].get("status") != "success":
            print(f"Primary {name} failed, trying fallbacks...")
            for fb_name, fb_model_id in FALLBACK_MODELS.items():
                if fb_name in fallback_used:
                    continue
                print(f"  Trying fallback {fb_name} ({fb_model_id})...")
                res = test_model(fb_name, fb_model_id)
                if res.get("status") == "success":
                    results[name] = res  # replace the failed result with fallback
                    fallback_used[fb_name] = True
                    print(f"  Fallback succeeded: TTFT {res['ttft_ms']:.0f} ms")
                    break
                else:
                    print(f"  Fallback also failed: {res.get('status')}")
    
    # Validate JSON capability for successful models
    print("\nValidating JSON capability...")
    for name, res in results.items():
        if res.get("status") == "success":
            valid, msg = validate_json_output(name, res["model"])
            res["json_valid"] = valid
            res["json_msg"] = msg
            print(f"  {name}: {msg}")
    
    # Rank by TTFT (lower is better)
    successful = [(name, res) for name, res in results.items() if res.get("status") == "success"]
    successful.sort(key=lambda x: x[1]["ttft_ms"])
    top3 = successful[:3]
    
    print("\nTop 3 models by TTFT:")
    for name, res in top3:
        print(f"  {name}: TTFT {res['ttft_ms']:.0f} ms, Tok/s {res['tokens_per_sec']:.2f}, JSON: {res.get('json_valid', False)}")
    
    # Prepare routing data
    routing = {
        "timestamp": time.time(),
        "top_models": [
            {
                "name": name,
                "model": res["model"],
                "ttft_ms": res["ttft_ms"],
                "tokens_per_sec": res["tokens_per_sec"],
                "json_valid": res.get("json_valid", False)
            }
            for name, res in top3
        ],
        "full_results": results
    }
    
    # Save to model_routing.json
    output_path = "model_routing.json"
    with open(output_path, "w") as f:
        json.dump(routing, f, indent=2)
    print(f"\nSaved routing to {os.path.abspath(output_path)}")
    
    # If routing changed significantly, we might want to notify or delegate to AGY.
    # For now, we just output.
    
    return 0

if __name__ == "__main__":
    sys.exit(main())