"""Score every detector configuration on the NaijaCrisis test set.

Usage: python -I analyze.py
Reads data/naijacrisis_v1.tsv and any results/raw/<model>__<prompt>__r<k>.jsonl.
Writes results/summary.json and manuscript/generated/results.tex (LaTeX tables
that the paper \\input{}s), and prints a readable report.
"""
import csv, json, math, random, statistics, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import detectors as D  # noqa: E402

ROOT = HERE.parent
ITEMS = list(csv.DictReader(open(ROOT / "data" / "naijacrisis_v1.tsv", encoding="utf-8"), delimiter="\t"))
for it in ITEMS:
    it["label"] = int(it["label"])
Y = [it["label"] for it in ITEMS]
CATS = ["C1", "C2", "C3", "C4", "N1", "N2", "N3", "N4", "N5"]
SEV_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


# ---------------------------------------------------------------- metrics
def confusion(pred):
    tp = sum(p and y for p, y in zip(pred, Y))
    fp = sum(p and not y for p, y in zip(pred, Y))
    fn = sum((not p) and y for p, y in zip(pred, Y))
    tn = sum((not p) and not y for p, y in zip(pred, Y))
    return tp, fp, fn, tn


def metrics(pred):
    tp, fp, fn, tn = confusion(pred)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    return {"precision": p, "recall": r, "f1": f1, "fpr": fpr,
            "accuracy": (tp + tn) / len(Y), "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def per_category(pred):
    """Positive-prediction rate per category: recall for C*, FPR for N*."""
    out = {}
    for c in CATS:
        idx = [i for i, it in enumerate(ITEMS) if it["category"] == c]
        out[c] = sum(bool(pred[i]) for i in idx) / len(idx)
    return out


def bootstrap_ci(pred, key, n=2000, seed=7):
    rng = random.Random(seed)
    N = len(Y)
    vals = []
    for _ in range(n):
        s = [rng.randrange(N) for _ in range(N)]
        tp = sum(pred[i] and Y[i] for i in s)
        fp = sum(pred[i] and not Y[i] for i in s)
        fn = sum((not pred[i]) and Y[i] for i in s)
        tn = len(s) - tp - fp - fn
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        v = {"precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0,
             "fpr": fp / (fp + tn) if fp + tn else 0.0}[key]
        vals.append(v)
    vals.sort()
    return vals[int(0.025 * n)], vals[int(0.975 * n) - 1]


def mcnemar_exact(pa, pb):
    """Exact two-sided McNemar test on correctness of two detectors."""
    b = sum((a == y) and (bb != y) for a, bb, y in zip(pa, pb, Y))
    c = sum((a != y) and (bb == y) for a, bb, y in zip(pa, pb, Y))
    n = b + c
    if n == 0:
        return b, c, 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return b, c, min(1.0, 2 * p)


# ---------------------------------------------------------------- data
def load_raw():
    runs = defaultdict(dict)  # (model, prompt) -> {run: {id: rec}}
    for f in sorted((ROOT / "results" / "raw").glob("*.jsonl")):
        model, prompt, r = f.stem.split("__")
        recs = {}
        for line in open(f, encoding="utf-8"):
            rec = json.loads(line)
            # keep the latest successful record per id (reruns append)
            if rec["id"] not in recs or not rec.get("error"):
                recs[rec["id"]] = rec
        if len(recs) == len(ITEMS):
            runs[(model, prompt)][int(r[1:])] = recs
        else:
            print(f"! skipping incomplete {f.name} ({len(recs)}/{len(ITEMS)})")
    return runs


# ---------------------------------------------------------------- conditions
def keyword_conditions():
    return {
        "KW-full": [D.keyword_hit(it["text"], D.CRISIS_KEYWORDS) for it in ITEMS],
        "KW-generic": [D.keyword_hit(it["text"], D.GENERIC_KEYWORDS) for it in ITEMS],
        "KW-critical": [D.critical_hit(it["text"]) for it in ITEMS],
    }


def llm_conditions(runs):
    """Return {name: [pred_run1, pred_run2, ...]} plus reliability stats."""
    conds, stats = {}, {}
    for (model, prompt), byrun in runs.items():
        for r in sorted(byrun):
            recs = byrun[r]
            ver = [D.llm_verdict(recs[it["id"]]) for it in ITEMS]
            llm = [bool(v[1]) if v[0] else False for v in ver]
            tag = "NG" if prompt == "ng" else "GEN"
            conds.setdefault(f"LLM-{tag} [{model}]", []).append(llm)
            if prompt == "ng":
                conds.setdefault(f"Hybrid-deployed [{model}]", []).append(
                    [D.hybrid(it["text"], recs[it["id"]], D.CRISIS_KEYWORDS) for it in ITEMS])
                conds.setdefault(f"LLM-NG, sev>=HIGH [{model}]", []).append(
                    [bool(v[0] and v[1] and SEV_RANK.get(str(v[2]).upper(), 1) >= 2) for v in ver])
                conds.setdefault(f"LLM-NG OR critical [{model}]", []).append(
                    [a or D.critical_hit(it["text"]) for a, it in zip(llm, ITEMS)])
                conds.setdefault(f"Recommended [{model}]", []).append(
                    [bool(v[0] and v[1] and SEV_RANK.get(str(v[2]).upper(), 1) >= 2) or D.critical_hit(it["text"])
                     for v, it in zip(ver, ITEMS)])
            else:
                conds.setdefault(f"Hybrid-generic [{model}]", []).append(
                    [D.hybrid(it["text"], recs[it["id"]], D.GENERIC_KEYWORDS) for it in ITEMS])
            lat = [recs[it["id"]]["latency_ms"] for it in ITEMS if not recs[it["id"]].get("error")]
            fail = sum(1 for v in ver if not v[0])
            empty = sum(1 for it in ITEMS if not recs[it["id"]].get("error")
                        and not recs[it["id"]].get("content"))
            toks = [((recs[it["id"]].get("usage") or {}).get("completion_tokens") or 0) for it in ITEMS]
            s = stats.setdefault(f"{model}/{prompt}", {"lat": [], "fail": [], "empty": [], "out_tokens": []})
            s["lat"] += lat
            s["fail"].append(fail)
            s["empty"].append(empty)
            s["out_tokens"] += toks
    return conds, stats


def agg(preds_list):
    ms = [metrics(p) for p in preds_list]
    out = {}
    for k in ("precision", "recall", "f1", "fpr", "accuracy"):
        vals = [m[k] for m in ms]
        out[k] = statistics.mean(vals)
        out[k + "_sd"] = statistics.stdev(vals) if len(vals) > 1 else 0.0
    out["runs"] = len(ms)
    out["ci_recall"] = bootstrap_ci(preds_list[0], "recall")
    out["ci_precision"] = bootstrap_ci(preds_list[0], "precision")
    out["ci_f1"] = bootstrap_ci(preds_list[0], "f1")
    cats = [per_category(p) for p in preds_list]
    out["per_category"] = {c: statistics.mean(x[c] for x in cats) for c in CATS}
    out["confusion_run1"] = {k: ms[0][k] for k in ("tp", "fp", "fn", "tn")}
    return out


# ---------------------------------------------------------------- output
def pct(x):
    return f"{100 * x:.1f}"


MODEL_ORDER = ["gpt-5.1", "gpt-5-mini-mt2000", "gpt-5-mini"]
COND_ORDER = ["Hybrid-deployed", "Hybrid-generic", "LLM-NG", "LLM-GEN", "LLM-NG, sev>=HIGH", "LLM-NG OR critical", "Recommended"]


def model_label(m):
    if m == "gpt-5.1":
        return r"\texttt{gpt-5.1} (deployed model)"
    if m.endswith("-mt2000"):
        return r"\texttt{gpt-5-mini}, 2{,}000-token budget (control)"
    if m == "gpt-5-mini":
        return r"\texttt{gpt-5-mini}, production 300-token budget"
    return r"\texttt{" + m + "}"


def grouped(summary):
    """[(model or '', [(display_name, v), ...]), ...] in a fixed reading order."""
    out = [("", [(n, v) for n, v in summary.items() if "[" not in n])]
    models = sorted({n[:-1].split(" [")[1] for n in summary if "[" in n},
                    key=lambda m: MODEL_ORDER.index(m) if m in MODEL_ORDER else 99)
    for m in models:
        rows = [(c, summary[f"{c} [{m}]"]) for c in COND_ORDER if f"{c} [{m}]" in summary]
        out.append((m, rows))
    return out


def latex_name(n):
    return n.replace(">=", r"$\geq$").replace("OR", r"$\lor$").replace("_", r"\_")


def write_latex(summary, stats, tests):
    g = ROOT / "manuscript" / "generated"
    g.mkdir(parents=True, exist_ok=True)
    L = []
    multi = any(v["runs"] > 1 for v in summary.values())
    L.append(r"\begin{table*}[t]\centering\small")
    L.append(r"\caption{Detection performance on NaijaCrisis-" + f"{len(Y)} ({sum(Y)} crisis, {len(Y) - sum(Y)} non-crisis messages). "
             + (r"Values are means over repeated runs (\,$\pm$\,SD); brackets give 95\% bootstrap CIs (run~1). "
                if multi else r"Brackets give 95\% bootstrap CIs. ")
             + r"FPR = false-positive rate.}")
    L.append(r"\label{tab:main}")
    L.append(r"\begin{tabular}{lcccc}\toprule")
    L.append(r"Detector & Precision & Recall & F1 & FPR \\\midrule")

    def cell(v, k):
        s = pct(v[k])
        if v["runs"] > 1:
            s += r"\,$\pm$\," + pct(v[k + "_sd"])
        return s

    for model, rows in grouped(summary):
        if model:
            L.append(r"\midrule\multicolumn{5}{l}{\textit{" + model_label(model) + r"}}\\")
        for name, v in rows:
            rec = cell(v, "recall") + r" {\scriptsize[" + pct(v["ci_recall"][0]) + "--" + pct(v["ci_recall"][1]) + "]}"
            L.append(f"{latex_name(name)} & {cell(v, 'precision')} & {rec} & {cell(v, 'f1')} & {cell(v, 'fpr')} \\\\")
    L.append(r"\bottomrule\end{tabular}\end{table*}")

    L.append("")
    L.append(r"\begin{table*}[t]\centering\small")
    L.append(r"\caption{Rate of crisis predictions per category (\%), keyword baselines and the deployed model (\texttt{gpt-5.1}). "
             r"For crisis categories (C1--C4) this is recall; for non-crisis categories (N1--N5) it is the false-positive rate, "
             r"so higher is better on the left and lower is better on the right.}")
    L.append(r"\label{tab:percat}")
    L.append(r"\begin{tabular}{l" + "c" * 4 + "|" + "c" * 5 + r"}\toprule")
    L.append("Detector & " + " & ".join(CATS) + r" \\\midrule")
    for model, rows in grouped(summary):
        if model not in ("", "gpt-5.1"):
            continue
        if model:
            L.append(r"\midrule")
        for name, v in rows:
            L.append(latex_name(name) + " & " + " & ".join(pct(v["per_category"][c]) for c in CATS) + r" \\")
    L.append(r"\bottomrule\end{tabular}\end{table*}")

    if stats:
        L.append("")
        L.append(r"\begin{table}[t]\centering\small")
        L.append(r"\caption{Operational behaviour of the LLM stage (all runs pooled).}\label{tab:ops}")
        L.append(r"\begin{tabular}{llccc}\toprule")
        L.append(r"Model & Prompt & Median lat. (s) & P95 lat. (s) & Failed calls (\%) \\\midrule")
        def okey(kv):
            m = kv[0].split("/")[0]
            return (MODEL_ORDER.index(m) if m in MODEL_ORDER else 99, kv[0])
        for k, s in sorted(stats.items(), key=okey):
            lat = sorted(s["lat"])
            med = statistics.median(lat) / 1000 if lat else float("nan")
            p95 = lat[int(0.95 * (len(lat) - 1))] / 1000 if lat else float("nan")
            fail = 100 * sum(s["fail"]) / (len(ITEMS) * len(s["fail"]))
            m, pr = k.split("/")
            mname = "gpt-5-mini (2,000 tok.)" if m.endswith("-mt2000") else m
            L.append(f"\\texttt{{{mname}}} & {'Nigerian' if pr == 'ng' else 'generic'} & {med:.2f} & {p95:.2f} & {fail:.1f} \\\\")
        L.append(r"\bottomrule\end{tabular}\end{table}")

    # Key numbers as macros so prose in the paper stays in sync with the data.
    M = []
    for name, tag in (("KW-full", "KWfull"), ("KW-generic", "KWgen"), ("KW-critical", "KWcrit")):
        v = summary[name]
        for k, kk in (("precision", "P"), ("recall", "R"), ("f1", "F"), ("fpr", "FPR")):
            M.append(f"\\newcommand{{\\{tag}{kk}}}{{{pct(v[k])}\\%}}")
        for c in CATS:
            # TeX control sequences cannot contain digits: C1 -> Cone, N5 -> Nfive
            cname = c[0] + ["one", "two", "three", "four", "five"][int(c[1]) - 1]
            M.append(f"\\newcommand{{\\{tag}{cname}}}{{{pct(v['per_category'][c])}\\%}}")
    M.append(f"\\newcommand{{\\Nitems}}{{{len(Y)}}}\\newcommand{{\\Npos}}{{{sum(Y)}}}\\newcommand{{\\Nneg}}{{{len(Y) - sum(Y)}}}")
    M.append(f"\\newcommand{{\\Nlex}}{{{len(D.CRISIS_KEYWORDS)}}}\\newcommand{{\\Nlexng}}{{{len(D.NIGERIAN_TERMS)}}}"
             f"\\newcommand{{\\Ncrit}}{{{len(D.CRITICAL_KEYWORDS)}}}")
    M.append(f"\\newcommand{{\\HaveLLM}}{{{'1' if stats else '0'}}}")
    # \res{<condition>}{<model>}{<metric>} for LLM conditions, e.g. \res{LLM-NG}{gpt-5.1}{R}.
    # Metrics: P R F FPR, per-category rates C1..N5, and SDs as Rsd/Psd/FPRsd.
    M.append(r"\makeatletter\newcommand{\res}[3]{\@ifundefined{res@#1@#2@#3}{\textbf{??}}{\csname res@#1@#2@#3\endcsname}}\makeatother")
    for name, v in summary.items():
        if "[" not in name:
            continue
        cond, model = name[:-1].split(" [")
        cond = cond.replace(">=", "ge").replace(" ", "").replace(",", "")
        vals = {"P": v["precision"], "R": v["recall"], "F": v["f1"], "FPR": v["fpr"],
                "Psd": v["precision_sd"], "Rsd": v["recall_sd"], "FPRsd": v["fpr_sd"]}
        vals.update(v["per_category"])
        for k, x in vals.items():
            M.append(f"\\expandafter\\def\\csname res@{cond}@{model}@{k}\\endcsname{{{pct(x)}\\%}}")
    for (a, b, x, y, p) in tests:
        ca, ma = a[:-1].split(" [")
        cb = b[:-1].split(" [")[0]
        key = f"{ca}@{cb}@{ma}".replace(" ", "")
        M.append(f"\\expandafter\\def\\csname mcn@{key}\\endcsname{{{'$p<0.001$' if p < 0.001 else f'$p={p:.3f}$'}}}")
    M.append(r"\makeatletter\newcommand{\mcn}[3]{\@ifundefined{mcn@#1@#2@#3}{\textbf{??}}{\csname mcn@#1@#2@#3\endcsname}}\makeatother")
    for k, s in stats.items():
        lat = sorted(s["lat"])
        tag = k.replace("/", "@")
        if lat:
            M.append(f"\\expandafter\\def\\csname lat@{tag}@med\\endcsname{{{statistics.median(lat) / 1000:.2f}}}")
            M.append(f"\\expandafter\\def\\csname lat@{tag}@p95\\endcsname{{{lat[int(0.95 * (len(lat) - 1))] / 1000:.2f}}}")
        M.append(f"\\expandafter\\def\\csname lat@{tag}@fail\\endcsname{{{sum(s['fail'])}}}")
        M.append(f"\\expandafter\\def\\csname lat@{tag}@failpct\\endcsname"
                 f"{{{100 * sum(s['fail']) / (len(ITEMS) * len(s['fail'])):.1f}\\%}}")
        M.append(f"\\expandafter\\def\\csname lat@{tag}@emptypct\\endcsname"
                 f"{{{100 * sum(s['empty']) / (len(ITEMS) * len(s['empty'])):.1f}\\%}}")
        M.append(f"\\expandafter\\def\\csname lat@{tag}@runs\\endcsname{{{len(s['fail'])}}}")
    M.append(r"\makeatletter\newcommand{\lat}[3]{\@ifundefined{lat@#1@#2@#3}{\textbf{??}}{\csname lat@#1@#2@#3\endcsname}}\makeatother")
    (g / "macros.tex").write_text("\n".join(M) + "\n", encoding="utf-8")

    ds = dataset_stats()
    names = {"C1": "English, explicit", "C2": "English, implicit", "C3": "Pidgin/slang, explicit",
             "C4": "Pidgin/slang, implicit", "N1": "Neutral, everyday", "N2": "English distress, no risk",
             "N3": "Pidgin distress, no risk", "N4": "English lexical trap", "N5": "Nigerian lexical trap"}
    T = [r"\begin{table}[t]\centering\small",
         r"\caption{Composition of the NaijaCrisis test set. \emph{Lexicon hits} counts items that contain at least one "
         r"of the deployed keywords (raw substring match), which is exactly the set the deployed hybrid forwards to the LLM.}",
         r"\label{tab:dataset}", r"\begin{tabular}{llcc}\toprule",
         r"Code & Description & $n$ & Lexicon hits \\\midrule"]
    for c in CATS:
        if c == "N1":
            T.append(r"\midrule")
        T.append(f"{c} & {names[c]} & {ds[c]['n']} & {ds[c]['lexicon_hits']} ({pct(ds[c]['lexicon_hits'] / ds[c]['n'])}\\%) \\\\")
    T += [r"\midrule", f"& Crisis (label 1) & {sum(Y)} & \\\\", f"& Non-crisis (label 0) & {len(Y) - sum(Y)} & \\\\",
          r"\bottomrule\end{tabular}\end{table}"]
    (g / "dataset.tex").write_text("\n".join(T) + "\n", encoding="utf-8")

    if tests:
        L.append("")
        L.append("% McNemar tests (run 1): " + "; ".join(f"{a} vs {b}: b={x}, c={y}, p={p:.3g}" for a, b, x, y, p in tests))
    (g / "results.tex").write_text("\n".join(L) + "\n", encoding="utf-8")


def dataset_stats():
    by = defaultdict(lambda: [0, 0])
    for it in ITEMS:
        by[it["category"]][0] += 1
        by[it["category"]][1] += D.keyword_hit(it["text"], D.CRISIS_KEYWORDS)
    return {c: {"n": by[c][0], "lexicon_hits": by[c][1]} for c in CATS}


def main():
    kw = keyword_conditions()
    runs = load_raw()
    llm, stats = llm_conditions(runs)
    allc = {k: [v] for k, v in kw.items()}
    allc.update(llm)
    summary = {k: agg(v) for k, v in allc.items()}

    tests = []
    for model in sorted({m for m, _ in runs}):
        pairs = [(f"Hybrid-deployed [{model}]", f"LLM-NG [{model}]"),
                 (f"LLM-NG [{model}]", f"LLM-GEN [{model}]"),
                 (f"Hybrid-deployed [{model}]", f"Hybrid-generic [{model}]"),
                 (f"Recommended [{model}]", f"Hybrid-deployed [{model}]"),
                 (f"Recommended [{model}]", f"LLM-NG [{model}]")]
        for a, b in pairs:
            if a in allc and b in allc:
                tests.append((a, b, *mcnemar_exact(allc[a][0], allc[b][0])))

    ds = dataset_stats()
    out = {"n_items": len(ITEMS), "n_pos": sum(Y), "dataset": ds, "summary": summary,
           "llm_stats": {k: {"median_latency_ms": statistics.median(s["lat"]) if s["lat"] else None,
                             "parse_failures_per_run": s["fail"], "empty_per_run": s["empty"],
                             "mean_completion_tokens": statistics.mean(s["out_tokens"]) if s["out_tokens"] else None}
                         for k, s in stats.items()},
           "mcnemar": [dict(a=a, b=b, b_only_a_correct=x, c_only_b_correct=y, p=p) for a, b, x, y, p in tests]}
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    write_latex(summary, stats, tests)

    print(f"items={len(ITEMS)} crisis={sum(Y)} non-crisis={len(Y) - sum(Y)}")
    print("lexicon hits per category:", {c: f"{d['lexicon_hits']}/{d['n']}" for c, d in ds.items()})
    print(f"\n{'detector':38s} {'P':>6s} {'R':>6s} {'F1':>6s} {'FPR':>6s}   " + " ".join(f"{c:>5s}" for c in CATS))
    for k, v in summary.items():
        print(f"{k:38s} {pct(v['precision']):>6s} {pct(v['recall']):>6s} {pct(v['f1']):>6s} {pct(v['fpr']):>6s}   "
              + " ".join(f"{pct(v['per_category'][c]):>5s}" for c in CATS))
    for t in tests:
        print("McNemar", t)
    for k, s in out["llm_stats"].items():
        print(k, s)


if __name__ == "__main__":
    main()
