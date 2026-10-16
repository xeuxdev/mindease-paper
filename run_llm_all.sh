#!/usr/bin/env bash
# Runs every LLM condition (2 models x 2 prompts x 3 runs = 3,420 calls), then rebuilds the paper.
# Needs a valid key:  export OPENAI_API_KEY=sk-...   (overrides mindease/backend/.env)
set -e
cd "$(dirname "$0")"
for model in gpt-5.1 gpt-5-mini; do
  for prompt in ng generic; do
    for run in 1 2 3; do
      python -I eval/run_llm.py "$model" "$prompt" "$run"
    done
  done
done
./build.sh
