#!/usr/bin/env bash
# Build the arXiv source bundle (arxiv/ and arxiv-source.tar.gz) from the preprint layout.
# Refuses to package while placeholders remain unless run with --draft.
set -e
cd "$(dirname "$0")"
./build.sh >/dev/null
left=$(grep -nE '\[email\]|\[repository URL\]|\pending' manuscript/main.tex manuscript/body.tex || true)
if [ -n "$left" ] && [ "$1" != "--draft" ]; then
  echo "Placeholders still present, fix these first (or pass --draft):"; echo "$left"; exit 1
fi
rm -rf arxiv arxiv-source.tar.gz
mkdir -p arxiv/generated
cp manuscript/{main.tex,common.tex,body.tex,appendix.tex,main.bbl} arxiv/
cp manuscript/generated/{macros.tex,dataset.tex,results.tex} arxiv/generated/
# verify the bundle compiles on its own, from its root, without bibtex
(cd arxiv && pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null && pdflatex -interaction=nonstopmode -halt-on-error main.tex | grep "Output written")
(cd arxiv && rm -f main.aux main.log main.out main.pdf)
tar -czf arxiv-source.tar.gz -C arxiv .
echo "arxiv-source.tar.gz: $(tar -tzf arxiv-source.tar.gz | wc -l) files"
