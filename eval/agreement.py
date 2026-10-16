"""Cohen's kappa between the reference labels and filled-in annotation sheets.

Usage: python -I agreement.py data/annotator_A.csv [data/annotator_B.csv ...]
Each file is a copy of data/annotation_sheet.csv with the `label` column filled (0/1).
"""
import csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ref = {r["id"]: int(r["label"]) for r in csv.DictReader(open(ROOT / "data" / "naijacrisis_v1.tsv", encoding="utf-8"), delimiter="\t")}
key = {r["row"]: r["id"] for r in csv.DictReader(open(ROOT / "data" / "annotation_key.csv", encoding="utf-8"))}


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


sheets = {}
for path in sys.argv[1:]:
    lab = {}
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        if r["label"].strip() in ("0", "1"):
            lab[key[r["item_id"]]] = int(r["label"])
    sheets[Path(path).stem] = lab
    ids = sorted(lab)
    k = kappa([ref[i] for i in ids], [lab[i] for i in ids])
    dis = [i for i in ids if ref[i] != lab[i]]
    print(f"{Path(path).stem}: {len(ids)} labelled, kappa vs reference = {k:.3f}, disagreements: {', '.join(dis) or 'none'}")

names = list(sheets)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        common = sorted(set(sheets[names[i]]) & set(sheets[names[j]]))
        k = kappa([sheets[names[i]][x] for x in common], [sheets[names[j]][x] for x in common])
        print(f"{names[i]} vs {names[j]}: kappa = {k:.3f} on {len(common)} items")
