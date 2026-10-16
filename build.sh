#!/usr/bin/env bash
# Regenerate results tables from data + LLM runs, then build both PDFs:
#   manuscript/main.pdf  (preprint / arXiv layout)
#   acl/main.pdf         (ACL / AfricaNLP layout, review mode)
set -e
cd "$(dirname "$0")"
python -I eval/analyze.py >/dev/null

build() {
  (cd "$1"
   pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
   bibtex main >/dev/null
   pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
   pdflatex -interaction=nonstopmode -halt-on-error main.tex | grep -E "Output written|undefined" || true
   grep -E "^!|Citation .* undefined|Reference .* undefined" main.log || true)
}
echo "== preprint"; build manuscript
echo "== acl"; build acl
