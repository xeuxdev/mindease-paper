"""Run the LLM crisis classifier on every test item and cache raw responses.

Usage: python -I run_llm.py <model> <prompt:ng|generic> <run_index> [max_completion_tokens]
(The optional token budget is a control condition; output is labelled <model>-mt<N>.)
Writes results/raw/<model>__<prompt>__r<run>.jsonl, skipping items already done.
Request settings mirror aiCrisisAnalysis: max_completion_tokens=300,
response_format=json_object, default temperature.
"""
import csv, json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from detectors import PROMPTS  # noqa: E402

ROOT = HERE.parent
ENV = ROOT.parent / "mindease" / "backend" / ".env"


LOCAL_ENV = ROOT / ".env"  # paper/.env (gitignored) takes precedence over the MindEase .env


def load_env(path=None):
    vals = {}
    for line in (path or ENV).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def call(base, key, model, system, text, max_tokens=300):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": text}],
        "max_completion_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "stream": False,
    }).encode()
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    t0 = time.perf_counter()
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.loads(r.read())
            ms = (time.perf_counter() - t0) * 1000
            ch = d["choices"][0]
            return {"content": ch["message"].get("content"), "finish_reason": ch.get("finish_reason"),
                    "usage": d.get("usage"), "latency_ms": ms, "error": None}
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(2 ** attempt * 2)
                t0 = time.perf_counter()
                continue
            return {"content": None, "error": f"HTTP {e.code}: {e.read()[:300].decode(errors='replace')}",
                    "latency_ms": (time.perf_counter() - t0) * 1000}
        except Exception as e:  # timeouts etc.
            if attempt < 4:
                time.sleep(2 ** attempt)
                t0 = time.perf_counter()
                continue
            return {"content": None, "error": repr(e), "latency_ms": (time.perf_counter() - t0) * 1000}


def main():
    model, prompt, run = sys.argv[1], sys.argv[2], int(sys.argv[3])
    max_tokens = int(sys.argv[4]) if len(sys.argv) > 4 else 300
    label = model if max_tokens == 300 else f"{model}-mt{max_tokens}"
    env = load_env() if ENV.exists() else {}
    if LOCAL_ENV.exists():
        env.update(load_env(LOCAL_ENV))
    # Precedence: shell OPENAI_API_KEY > paper/.env > mindease/backend/.env
    key = os.environ.get("OPENAI_API_KEY") or env["OPENAI_API_KEY"]
    base = os.environ.get("OPENAI_BASE_URL") or env.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    if not base.rstrip("/").endswith("/v1"):
        base = base.rstrip("/") + "/v1"
    items = list(csv.DictReader(open(ROOT / "data" / "naijacrisis_v1.tsv", encoding="utf-8"), delimiter="\t"))
    out = ROOT / "results" / "raw" / f"{label}__{prompt}__r{run}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in open(out, encoding="utf-8"):
            r = json.loads(line)
            if not r.get("error"):
                done.add(r["id"])
    todo = [it for it in items if it["id"] not in done]
    print(f"{label}/{prompt}/r{run}: {len(todo)} to run", flush=True)

    if todo:  # fail fast on a bad key instead of writing 285 error rows
        probe = call(base, key, model, PROMPTS[prompt], "hello", max_tokens)
        if probe["error"] and probe["error"].startswith(("HTTP 401", "HTTP 403", "HTTP 404")):
            sys.exit(f"Aborting: {probe['error'][:120]}")

    def work(it):
        r = call(base, key, model, PROMPTS[prompt], it["text"], max_tokens)
        r.update(id=it["id"], model=label, prompt=prompt, run=run, max_tokens=max_tokens)
        return r

    with ThreadPoolExecutor(max_workers=8) as ex, open(out, "a", encoding="utf-8") as f:
        for r in ex.map(work, todo):
            f.write(json.dumps(r) + "\n")
            f.flush()
    errs = [json.loads(line) for line in open(out, encoding="utf-8") if json.loads(line).get("error")]
    print(f"done; error rows in file: {len(errs)}")



if __name__ == "__main__":
    main()
