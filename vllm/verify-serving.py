"""Run inside the vLLM pod to verify its Kubernetes Service and generation."""
import json
import time
import urllib.request

base = "http://vllm.inference.svc.cluster.local:8000"
with urllib.request.urlopen(base + "/health", timeout=10) as response:
    print("health_status:", response.status, flush=True)
with urllib.request.urlopen(base + "/v1/models", timeout=10) as response:
    print("models:", response.read().decode(), flush=True)
payload = {
    "model": "qwen3-0.6b",
    "messages": [{"role": "user", "content": "Explain a Kubernetes pod in two sentences."}],
    "temperature": 0,
    "max_tokens": 128,
    "stream": False,
    "chat_template_kwargs": {"enable_thinking": False},
}
request = urllib.request.Request(base + "/v1/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
started = time.perf_counter()
with urllib.request.urlopen(request, timeout=180) as response:
    result = json.load(response)
assert result["choices"][0]["message"]["content"]
print("response:", json.dumps(result), flush=True)
print("request_elapsed_seconds:", round(time.perf_counter() - started, 3), flush=True)
