"""Faithful re-implementation of the MindEase crisis-detection pipeline.

Source of truth: mindease/backend/src/config/constants.ts (crisisKeywords) and
mindease/backend/src/services/ai-service.ts (detectCrisis, aiCrisisAnalysis,
quickKeywordScan, containsCriticalKeywords). Matching semantics mirror the
JavaScript: String.prototype.toLowerCase() + includes(), i.e. raw substring.
"""

# constants.ts -> crisisKeywords (order preserved)
CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "end my life", "want to die",
    "better off dead", "no reason to live", "self-harm", "hurt myself",
    "cutting", "overdose", "jump off", "hanging", "gun", "pills", "razor",
    "abuse", "violent", "emergency", "crisis", "drink sniper", "take sniper",
    "sniper", "gbege", "die", "pai", "kpeme", "slump", "take poison",
    "swallow poison", "chop poison", "drink poison", "poison",
    "nothing dey work", "tired of life", "no hope", "give up", "jump lagoon",
    "jump bridge", "take my life", "end am", "log out", "go meet god",
    "everyone would be better off without me",
]

# Terms in CRISIS_KEYWORDS that are Nigerian-specific (slang, Pidgin or local
# brand names). Removing them gives the "generic English lexicon" ablation.
NIGERIAN_TERMS = {
    "drink sniper", "take sniper", "sniper", "gbege", "pai", "kpeme", "slump",
    "chop poison", "nothing dey work", "jump lagoon", "end am", "log out",
    "go meet god",
}
GENERIC_KEYWORDS = [k for k in CRISIS_KEYWORDS if k not in NIGERIAN_TERMS]

# ai-service.ts -> containsCriticalKeywords. Note the last entry: it is
# compared against a lower-cased message but contains an upper-case "I" and a
# curly apostrophe, so it can never match. Reproduced as-is.
CRITICAL_KEYWORDS = [
    "kill myself", "end my life", "suicide", "want to die", "drink sniper",
    "jump lagoon", "jump bridge", "take poison", "pai myself", "end am today",
    "I don’t want to be alive anymore.",
]

# ai-service.ts -> aiCrisisAnalysis systemPrompt, verbatim.
PROMPT_NG = """You are a crisis detection AI with expertise in Nigerian nuances and slang. Analyze the following message and determine if it indicates a mental health crisis.

Respond ONLY with a valid JSON object in this exact format (no markdown, no code blocks):
{
  "isCrisis": true,
  "severity": "LOW",
  "confidence": 0.8
}

Severity levels:
- LOW: Mild distress, no immediate danger
- MEDIUM: Moderate distress, some concerning thoughts
- HIGH: Severe distress, thoughts of self-harm
- CRITICAL: Immediate danger, active suicidal ideation or plan

Key Nigerian Context:
- Terms like "drink sniper", "jump lagoon", "oct 20", "pai myself", "kpeme" are effectively suicide/death ideation.
- "I don tire", "nothing dey work" can imply deep depression/despair.
"""

# Ablation: identical prompt with the cultural-adaptation text removed.
PROMPT_GENERIC = """You are a crisis detection AI. Analyze the following message and determine if it indicates a mental health crisis.

Respond ONLY with a valid JSON object in this exact format (no markdown, no code blocks):
{
  "isCrisis": true,
  "severity": "LOW",
  "confidence": 0.8
}

Severity levels:
- LOW: Mild distress, no immediate danger
- MEDIUM: Moderate distress, some concerning thoughts
- HIGH: Severe distress, thoughts of self-harm
- CRITICAL: Immediate danger, active suicidal ideation or plan
"""

PROMPTS = {"ng": PROMPT_NG, "generic": PROMPT_GENERIC}


def keyword_hit(text, keywords):
    low = text.lower()
    return any(k.lower() in low for k in keywords)


def critical_hit(text):
    # containsCriticalKeywords does NOT lower-case the keywords.
    low = text.lower()
    return any(k in low for k in CRITICAL_KEYWORDS)


def js_truthy(v):
    return v not in (None, False, 0, "", ) and not (isinstance(v, float) and v != v)


def llm_verdict(rec):
    """Return (ok, isCrisis, severity) for one stored LLM call, mirroring the
    parse path in aiCrisisAnalysis (empty content or bad JSON => throws)."""
    if rec.get("error") or not rec.get("content"):
        return False, None, None
    import json, re
    s = rec["content"].strip()
    m = re.search(r"```json\s*([\s\S]*?)\s*```", s) or re.search(r"```\s*([\s\S]*?)\s*```", s)
    if m:
        s = m.group(1).strip()
    try:
        a = json.loads(s)
    except Exception:
        return False, None, None
    if not isinstance(a, dict):
        return False, None, None
    return True, js_truthy(a.get("isCrisis")), (a.get("severity") or "MEDIUM")


def hybrid(text, rec, gate_keywords):
    """detectCrisis(): keyword gate -> LLM -> critical-keyword fail-safe."""
    if not keyword_hit(text, gate_keywords):
        return False
    ok, is_crisis, _ = llm_verdict(rec)
    if ok:
        return bool(is_crisis)
    return critical_hit(text)
