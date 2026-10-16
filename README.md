# MindEase → research paper

Working title: **Keyword Gates Fail Silently: Evaluating Culturally Adapted Crisis Detection in an LLM-Based Mental Health Chatbot for Nigerian Users**

## Layout
| Path | What it is |
|---|---|
| `manuscript/body.tex`, `appendix.tex` | **The paper text, shared by both layouts. Edit here.** |
| `manuscript/main.tex` → `main.pdf` | Preprint / arXiv layout. |
| `acl/main.tex` → `acl/main.pdf` | ACL / AfricaNLP layout (review mode, anonymous). Remove `[review]` for camera-ready. |
| `make_arxiv.sh` → `arxiv-source.tar.gz` | arXiv source bundle. Refuses to build while placeholders remain. |
| `manuscript/refs.bib` | Verified bibliography. |
| `manuscript/generated/` | Tables and number macros written by `eval/analyze.py`. Don't edit these by hand. |
| `data/naijacrisis_v1.tsv` | The 285-item labelled test set. |
| `data/GUIDELINES.md` | Labelling rules. |
| `data/annotation_sheet.csv` | Shuffled, unlabelled copy for blind annotators. `annotation_key.csv` maps rows back to item IDs. |
| `eval/detectors.py` | Exact re-implementation of the MindEase crisis pipeline (lexicon, prompt, fail-safe). |
| `eval/run_llm.py` | Calls the LLM classifier on every item and caches raw responses. |
| `eval/analyze.py` | Scores every configuration and regenerates the LaTeX tables. |
| `eval/agreement.py` | Cohen's kappa from filled annotation sheets. |
| `REFERENCE_FIXES.md` | What was wrong with the report's references and what replaced it. |

## Commands
```bash
./build.sh                 # rescore + rebuild both PDFs
./make_arxiv.sh            # arXiv bundle (add --draft to ignore placeholders)
export OPENAI_API_KEY=sk-... && ./run_llm_all.sh   # all LLM runs (3,420 short calls), then rebuild
python -I eval/agreement.py data/annotator_A.csv data/annotator_B.csv
```

## Status (2026-10-16)
All LLM runs are complete: 18 runs × 285 items = 5,130 calls in `results/raw/`. The paper text is filled in from the generated macros. The gpt-5-mini 2,000-token control was produced with `python -I eval/run_llm.py gpt-5-mini <ng|generic> <run> 2000`. The API key used lives in `paper/.env`, which is gitignored. Delete that file once the key expires.

## Remaining steps before submission
0. **Review all 285 test items yourself.** The paper says they were AI-drafted and then reviewed and corrected by you, so that has to be true. Fix any unnatural Pidgin and re-run `./build.sh`.
1. **Blind annotation.** Give `annotation_sheet.csv` plus `GUIDELINES.md` to two Nigerian Pidgin speakers. Ideally one has a psychology or counselling background. Report kappa, and fix any items they flag as unnatural.
2. **Held-out items (strongly recommended).** Ask 2–3 people who have never seen the lexicon to write about 50 extra messages each, following the guidelines. This answers the obvious reviewer objection that the author wrote the test set while knowing the keywords.
3. **Co-authorship.** Confirm with Aisha Mustapha Ahmad that she wants to be listed, and agree the author order.
4. **Venue.** The ACL version fits AfricaNLP's long-paper format (≤8 pages of main text). The 2027 call isn't out yet; past deadlines were March 2025 and December 2025. Check sites.google.com/view/africanlp2026 and the ACL portal.
5. **Fill placeholders:** your email in `manuscript/main.tex` and `acl/main.tex`, and the repo URL in `body.tex`.
6. **arXiv:** you need an endorser in cs.CL, someone who has posted there before. Since January 2026 an institutional email no longer qualifies on its own. Ask your supervisor or a Masakhane/HausaNLP researcher. Then upload `arxiv-source.tar.gz`, category cs.CL, cross-list cs.CY.
7. **Public repo.** Publish `data/`, `eval/` and `results/` (never `.env` files), then put the URL in the paper.
