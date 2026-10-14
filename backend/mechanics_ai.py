"""
A language model's two jobs in picking a partner's mechanics articles.

backend/app_mechanics.py finds the partner's help centre and gathers
candidate articles; code is reliable at that. Choosing among them is a
judgement call that word matching gets wrong: Shopify Flow's "reports"
articles share words with the data topics, a search app filed under
"eCommerce platform" gets storefront topics. So a model, given the
integration's own Yotpo guide:
  1. suggests a few searches for the partner's help centre (suggest_queries);
  2. picks the best articles from the numbered candidates (choose).

The model only ever answers with numbers from the list it was shown, so it
cannot invent a link; anything else in its answer is dropped
(parse_choice). Every pick is still a proposal a human approves. If the
model fails, app_mechanics falls back to its own scoring.

Prompts and parsing are pure and tested; GeminiChooser is the only part that
calls out, with the app's GEMINI_API_KEY and default model.
"""

import json
import re
from typing import Dict, List, Optional, Sequence, Tuple

DEFAULT_MODEL = 'gemini-flash-latest'   # the app's default (config_manager)
GUIDE_CHARS = 3000                      # how much of the Yotpo guide the model reads
MAX_QUERIES = 3

_ROLE = ("You help build the knowledge base of Flow State, an assistant that explains to Yotpo "
         "customers how to set up a Yotpo Loyalty or Reviews integration with another app. Yotpo's "
         "own guide explains how to connect the integration. What is missing is the partner app's "
         "own documentation of the features the integration plugs into, so the assistant can explain "
         "how the partner's side behaves. Examples of good choices: for Klaviyo, 'Guide to Flow "
         "Triggers and Flow Filters'; for Recharge, 'Managing subscription discount codes'. Bad "
         "choices: welcome or overview pages about the whole app, troubleshooting, release notes, "
         "billing, pages about other integrations, pages about Yotpo itself, pages not in English.")


def _integration_block(name: str, categories: Sequence[str], guide: str) -> str:
    return (f"Integration: {name}\n"
            f"Catalog categories: {', '.join(categories) or 'none'}\n"
            f"What Yotpo's guide and the catalog say about it (excerpt):\n"
            f"\"\"\"\n{(guide or '').strip()[:GUIDE_CHARS]}\n\"\"\"")


def queries_prompt(name: str, categories: Sequence[str], guide: str) -> str:
    return (f"{_ROLE}\n\n{_integration_block(name, categories, guide)}\n\n"
            f"Which features of {name} does this integration use? Write up to {MAX_QUERIES} short "
            f"searches (2-5 words each) to run in {name}'s own help centre to find the articles that "
            f"explain those features. Do not include the words Yotpo or integration.\n"
            'Answer with JSON only: {"queries": ["...", "..."]}')


def choose_prompt(name: str, categories: Sequence[str], guide: str,
                  candidates: Sequence[Tuple[str, str]], limit: int) -> str:
    lines = '\n'.join(f'[{i}] {title} ({url})' for i, (url, title) in enumerate(candidates, 1))
    return (f"{_ROLE}\n\n{_integration_block(name, categories, guide)}\n\n"
            f"Candidate articles from {name}'s help centre:\n{lines}\n\n"
            f"Choose up to {limit} candidates that best explain how the features this integration "
            f"uses work, best first. Choose fewer, or none, if the candidates are not good enough. "
            f"For each, say in one plain sentence what it explains that matters for this "
            f"integration.\n"
            'Answer with JSON only: {"picks": [{"n": <candidate number>, "why": "..."}]}')


def _json_object(text: str) -> Optional[dict]:
    """The first JSON object in a model's answer (models sometimes wrap it in
    a code fence or a sentence)."""
    if not text:
        return None
    match = re.search(r'\{.*\}', text, re.S)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def parse_queries(text: str) -> List[str]:
    data = _json_object(text) or {}
    out = []
    for q in data.get('queries') or []:
        if isinstance(q, str):
            q = re.sub(r'\b(yotpo|integrations?)\b', '', q, flags=re.I).strip()
            if 2 <= len(q) <= 60 and q.lower() not in [o.lower() for o in out]:
                out.append(q)
    return out[:MAX_QUERIES]


def parse_choice(text: str, n_candidates: int, limit: int) -> Optional[List[Tuple[int, str]]]:
    """[(index into the candidates, why)], or None when the answer is
    unusable (then the caller falls back to scoring). Numbers outside the
    list, repeats and anything past `limit` are dropped."""
    data = _json_object(text)
    if data is None or not isinstance(data.get('picks'), list):
        return None
    out, seen = [], set()
    for p in data['picks']:
        if not isinstance(p, dict):
            continue
        n = p.get('n')
        if isinstance(n, str) and n.strip().isdigit():
            n = int(n)
        if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= n_candidates or n in seen:
            continue
        seen.add(n)
        why = p.get('why') if isinstance(p.get('why'), str) else ''
        out.append((n - 1, re.sub(r'\s+', ' ', why).strip()[:300]))
        if len(out) >= limit:
            break
    return out


class GeminiChooser:
    """suggest_queries / choose with Gemini. Counts calls and tokens so the
    dry run can report what it cost."""

    def __init__(self, model: str = DEFAULT_MODEL, api_key: Optional[str] = None):
        import os
        import google.generativeai as genai
        key = api_key or os.environ.get('GEMINI_API_KEY')
        if not key:
            raise RuntimeError('GEMINI_API_KEY is not set')
        genai.configure(api_key=key)
        self.model_name = model
        self.model = genai.GenerativeModel(
            model, generation_config={'temperature': 0, 'response_mime_type': 'application/json'})
        self.usage: Dict[str, int] = {'calls': 0, 'input_tokens': 0, 'output_tokens': 0, 'failures': 0}

    def _ask(self, prompt: str) -> str:
        self.usage['calls'] += 1
        try:
            response = self.model.generate_content(prompt, request_options={'timeout': 60})
            meta = getattr(response, 'usage_metadata', None)
            if meta is not None:
                self.usage['input_tokens'] += getattr(meta, 'prompt_token_count', 0) or 0
                self.usage['output_tokens'] += getattr(meta, 'candidates_token_count', 0) or 0
            return response.text or ''
        except Exception as e:  # the caller falls back to scoring
            self.usage['failures'] += 1
            print(f'  [ai] {type(e).__name__}: {str(e)[:120]}')
            return ''

    def suggest_queries(self, name, categories, guide) -> List[str]:
        return parse_queries(self._ask(queries_prompt(name, categories, guide)))

    def choose(self, name, categories, guide, candidates, limit) -> Optional[List[Tuple[int, str]]]:
        return parse_choice(self._ask(choose_prompt(name, categories, guide, candidates, limit)),
                            len(candidates), limit)
