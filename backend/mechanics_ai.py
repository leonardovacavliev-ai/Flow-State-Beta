"""
The language model's two jobs in finding a partner's mechanics articles
(Leo's design, 2026-10-14).

1. extract_functions: read what Yotpo and the partner wrote about the
   integration (the Yotpo guides, the partner's own Yotpo articles) and list
   every function of the partner app that the integration touches: what
   Yotpo does there, and what to search for in the partner's help centre.
2. verify: read the text of the articles the search found and accept only
   those that explain one of those functions.
Between the two, for a help centre with no search API, shortlist: pick from
the centre's list of article titles the ones worth reading for each function.

Accepted articles go into the knowledge base without a human review, so the
checks here are strict: the model answers in JSON, a verified article must
be one of the numbered candidates (it cannot add a link) and must name one of
the functions it listed; anything else is dropped. A failed call means no
articles for that integration, never a guess.

Prompts and parsing are pure and tested with a fake model; GeminiChooser is
the only part that calls out (the app's GEMINI_API_KEY and default model).
"""

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

DEFAULT_MODEL = 'gemini-flash-latest'   # the app's default (config_manager)
SOURCE_CHARS = 4000                     # per source document read in step 1
SOURCES_MAX = 6
EXCERPT_CHARS = 1500                    # per candidate article read in step 2
MAX_FUNCTIONS = 6
MAX_SEARCHES = 2                        # per function
PER_FUNCTION = 2                        # accepted articles per function
TITLES_MAX = 600                        # titles shown to shortlist
SHORTLIST_MAX = 20

_ROLE = ("You build the knowledge base of Flow State, an assistant that explains to Yotpo customers "
         "how to set up and use a Yotpo Loyalty & Referrals or Yotpo Reviews integration with "
         "another app. Yotpo's guide explains how to connect them. What the assistant also needs is "
         "the partner app's own documentation of each of its functions the integration touches, so "
         "it can explain how the partner's side behaves. Examples: for Klaviyo, how flows, flow "
         "triggers and filters, custom profile properties and segments work, because Yotpo sends "
         "events and properties that merchants use there; for Recharge, how subscription discount "
         "codes work, because Yotpo Loyalty creates coupon codes that apply to subscriptions.")


@dataclass
class Function:
    name: str                   # "discount codes on subscriptions"
    yotpo_role: str             # what Yotpo does with it
    searches: List[str] = field(default_factory=list)


def _sources_block(sources: Sequence[Tuple[str, str]]) -> str:
    parts = []
    for i, (label, text) in enumerate(list(sources)[:SOURCES_MAX], 1):
        parts.append(f'--- Source {i}: {label}\n{(text or "").strip()[:SOURCE_CHARS]}')
    return '\n\n'.join(parts) or '(no documents could be read)'


def functions_prompt(app: str, categories: Sequence[str], sources: Sequence[Tuple[str, str]]) -> str:
    return (f"{_ROLE}\n\nIntegration: Yotpo with {app}\n"
            f"Catalog categories: {', '.join(categories) or 'none'}\n\n"
            f"What Yotpo and {app} wrote about this integration:\n\n{_sources_block(sources)}\n\n"
            f"List every function of {app} itself that this integration touches: where Yotpo sends "
            f"data into {app}, where {app} sends data to Yotpo, and the {app} features a merchant "
            f"uses to act on that data. At most {MAX_FUNCTIONS}, most important first. Only "
            f"functions these documents support; none about Yotpo's own settings. For each, give "
            f"up to {MAX_SEARCHES} short searches (2-5 words, without the words Yotpo or "
            f"integration) to find {app}'s help article explaining that function.\n"
            'Answer with JSON only: {"functions": [{"name": "...", "yotpo_role": "...", '
            '"searches": ["..."]}]}')


def verify_prompt(app: str, functions: Sequence[Function],
                  candidates: Sequence[Tuple[str, str, str]]) -> str:
    funcs = '\n'.join(f'- {f.name}: {f.yotpo_role}' for f in functions)
    cands = '\n\n'.join(f'[{i}] {title} ({url})\n{(text or "").strip()[:EXCERPT_CHARS]}'
                        for i, (url, title, text) in enumerate(candidates, 1))
    return (f"{_ROLE}\n\nIntegration: Yotpo with {app}\n\nThe {app} functions this integration "
            f"touches:\n{funcs}\n\nCandidate articles from {app}'s help centre, with the start of "
            f"their text:\n\n{cands}\n\n"
            f"Accept a candidate only if its text explains how one of these functions works in "
            f"{app}, in English, well enough to help a merchant use it with Yotpo. Reject "
            f"troubleshooting notes, release notes, billing, pages mainly about another app, and "
            f"pages that only mention the function in passing. At most {PER_FUNCTION} per "
            f"function. Name the function exactly as listed, and say in one sentence what the "
            f"article explains.\n"
            'Answer with JSON only: {"accepted": [{"n": <candidate number>, "function": "...", '
            '"why": "..."}]}')


def shortlist_prompt(app: str, functions: Sequence[Function], titles: Sequence[str]) -> str:
    funcs = '\n'.join(f'- {f.name}: {f.yotpo_role}' for f in functions)
    lines = '\n'.join(f'[{i}] {t}' for i, t in enumerate(list(titles)[:TITLES_MAX], 1))
    return (f"{_ROLE}\n\nIntegration: Yotpo with {app}\n\nThe {app} functions this integration "
            f"touches:\n{funcs}\n\nArticles in {app}'s help centre:\n{lines}\n\n"
            f"Which of these articles most likely explain how one of those functions works? Pick up "
            f"to {SHORTLIST_MAX}, best first. They will be read before anything is accepted.\n"
            'Answer with JSON only: {"read": [<article number>, ...]}')


def parse_shortlist(text: str, n_titles: int) -> List[int]:
    """Indices into the titles; anything outside the list is dropped."""
    data = _json_object(text) or {}
    out = []
    for n in data.get('read') or []:
        if isinstance(n, str) and n.strip().isdigit():
            n = int(n)
        if isinstance(n, int) and not isinstance(n, bool) and 1 <= n <= min(n_titles, TITLES_MAX) \
                and n - 1 not in out:
            out.append(n - 1)
    return out[:SHORTLIST_MAX]


def _json_object(text: str) -> Optional[dict]:
    """The first JSON object in a model's answer."""
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


def _clean(value, limit) -> str:
    return re.sub(r'\s+', ' ', value).strip()[:limit] if isinstance(value, str) else ''


def parse_functions(text: str) -> Optional[List[Function]]:
    """The functions, or None when the answer is unusable."""
    data = _json_object(text)
    if data is None or not isinstance(data.get('functions'), list):
        return None
    out, names = [], set()
    for f in data['functions']:
        if not isinstance(f, dict):
            continue
        name = _clean(f.get('name'), 80)
        if not name or name.lower() in names:
            continue
        searches = []
        for q in f.get('searches') or []:
            q = re.sub(r'\b(yotpo|integrations?)\b', '', _clean(q, 60), flags=re.I).strip()
            if len(q) >= 3 and q.lower() not in [s.lower() for s in searches]:
                searches.append(q)
        if not searches:
            searches = [name]
        names.add(name.lower())
        out.append(Function(name, _clean(f.get('yotpo_role'), 300), searches[:MAX_SEARCHES]))
        if len(out) >= MAX_FUNCTIONS:
            break
    return out


def parse_verified(text: str, functions: Sequence[Function],
                   n_candidates: int) -> Optional[List[Tuple[int, str, str]]]:
    """[(candidate index, function name, why)], or None when unusable.
    Unknown numbers, unknown functions, repeats and anything over
    PER_FUNCTION per function are dropped."""
    data = _json_object(text)
    if data is None or not isinstance(data.get('accepted'), list):
        return None
    by_name = {f.name.lower(): f.name for f in functions}
    out, seen, per = [], set(), {}
    for a in data['accepted']:
        if not isinstance(a, dict):
            continue
        n = a.get('n')
        if isinstance(n, str) and n.strip().isdigit():
            n = int(n)
        if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= n_candidates or n in seen:
            continue
        function = by_name.get(_clean(a.get('function'), 80).lower())
        if not function or per.get(function, 0) >= PER_FUNCTION:
            continue
        seen.add(n)
        per[function] = per.get(function, 0) + 1
        out.append((n - 1, function, _clean(a.get('why'), 300)))
    return out


class GeminiChooser:
    """The two calls, with Gemini. Counts calls and tokens for the report."""

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
        """The model's answer; one retry on an error or an unreadable answer
        (timeouts happen on the long reading prompts)."""
        import time
        for attempt in range(2):
            self.usage['calls'] += 1
            try:
                response = self.model.generate_content(prompt, request_options={'timeout': 120})
                meta = getattr(response, 'usage_metadata', None)
                if meta is not None:
                    self.usage['input_tokens'] += getattr(meta, 'prompt_token_count', 0) or 0
                    self.usage['output_tokens'] += getattr(meta, 'candidates_token_count', 0) or 0
                text = response.text or ''
                if _json_object(text) is not None:
                    return text
                self.usage['failures'] += 1
            except Exception as e:
                self.usage['failures'] += 1
                print(f'  [ai] {type(e).__name__}: {str(e)[:120]}')
            if attempt == 0:
                time.sleep(5)
        return ''

    def extract_functions(self, app, categories, sources) -> Optional[List[Function]]:
        return parse_functions(self._ask(functions_prompt(app, categories, sources)))

    def shortlist(self, app, functions, titles) -> List[int]:
        return parse_shortlist(self._ask(shortlist_prompt(app, functions, titles)), len(titles))

    def verify(self, app, functions, candidates) -> Optional[List[Tuple[int, str, str]]]:
        return parse_verified(self._ask(verify_prompt(app, functions, candidates)),
                              functions, len(candidates))
