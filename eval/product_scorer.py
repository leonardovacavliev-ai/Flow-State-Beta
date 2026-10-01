"""
Mechanical scorer for the product-line experiment (PRODUCT_LINE_SPLIT_SCOPE.md, step 7).

Reads an answer and decides, without a model, whether it describes the product
the question was about. It is a heuristic by design: free, deterministic and
re-runnable after every prompt change. A CSM checks a sample of its verdicts
(eval/product_eval.py csm-agreement) before its numbers are trusted.

Signals, per product:
  - console and product names ("Yotpo Loyalty admin", "Integrations Center",
    "Yotpo Reviews", "Reviews admin")
  - property names that appear only in that product's labelled documents
    (built from the corpus at run time, so they follow the labels)

Outcomes for a question about one product:
  correct        names only that product, or neither
  wrong_product  names only the other product
  hedged         names both, or asks which product the user means
  no_answer      says the documentation isn't there
On an ESP with no Reviews documentation, a Reviews question is correct only
when the answer says so (the coverage guard doing its job); anything else is
answered_without_docs, which counts as wrong.

Outcomes for a question that names no product:
  correct        asks which product, or covers both
  picked_one     answers for one product without saying the other differs
  unclear        names neither
"""
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set

OTHER = {'loyalty': 'reviews', 'reviews': 'loyalty'}

CONSOLE_PATTERNS = {
    'loyalty': [
        r"\bLoyalty\s*(?:&|and)\s*Referrals\b",
        r"\bYotpo\s+Loyalty\b",
        r"\bLoyalty\s+admin\b",
        r"\bIntegrations\s+Center\b",
    ],
    'reviews': [
        r"\bYotpo\s+Reviews\b",
        r"\bReviews\s+admin\b",
    ],
}

DECLINED_PATTERNS = [
    r"\bno\s+(?:Yotpo\s+)?Reviews\s+documentation\b",
    # "I don't have documentation", "Flow State does not have Yotpo Reviews
    # documentation" -- up to three words between "have" and "documentation"
    r"\b(?:do|does)(?:n'?t|\s+not)\s+have\s+(?:any\s+)?(?:[\w&-]+\s+){0,3}(?:documentation|docs|information|details)\b",
    r"\bno\s+documentation\s+(?:for|on|about)\b",
    r"\bnot\s+(?:yet\s+)?(?:documented|covered)\b",
    r"\b(?:isn'?t|is not)\s+(?:any\s+)?documentation\b",
]

ASKS_PATTERNS = [
    r"\bwhich\s+(?:Yotpo\s+)?product\b",
    r"\bLoyalty(?:\s*&\s*Referrals)?\s+or\s+(?:Yotpo\s+)?Reviews\b",
    r"\bReviews\s+or\s+(?:Yotpo\s+)?Loyalty\b",
    r"\bare\s+you\s+(?:asking|referring)\s+(?:about|to)\b",
]

# snake_case identifiers and template variables: the shapes property names take
PROPERTY_TOKEN = re.compile(r"\{\{\s*([A-Za-z_][\w.]*)\s*\}\}|\b([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\b")


def property_tokens(text: str) -> Set[str]:
    return {a or b for a, b in PROPERTY_TOKEN.findall(text or "")}


def _any(patterns: Iterable[str], text: str) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


@dataclass
class Vocabulary:
    """Property names that appear in only one product's documents."""
    exclusive: Dict[str, Set[str]] = field(default_factory=lambda: {'loyalty': set(), 'reviews': set()})

    @classmethod
    def from_chunks(cls, chunks: Iterable[tuple]) -> "Vocabulary":
        """chunks: (product_label, text) pairs; unlabelled chunks are skipped."""
        seen = {'loyalty': set(), 'reviews': set(), 'shared': set()}
        for label, text in chunks:
            if label in seen:
                seen[label] |= property_tokens(text)
        return cls(exclusive={
            'loyalty': seen['loyalty'] - seen['reviews'] - seen['shared'],
            'reviews': seen['reviews'] - seen['loyalty'] - seen['shared'],
        })


@dataclass
class Score:
    outcome: str
    mentions: Dict[str, List[str]]          # product -> evidence found
    declined: bool
    asks: bool
    ungrounded_properties: List[str]        # property names absent from the context


def product_mentions(answer: str, vocab: Vocabulary) -> Dict[str, List[str]]:
    found = {}
    tokens = property_tokens(answer)
    for product in ('loyalty', 'reviews'):
        hits = [m.group(0) for p in CONSOLE_PATTERNS[product]
                for m in [re.search(p, answer, re.I)] if m]
        hits += sorted(tokens & vocab.exclusive[product])
        found[product] = hits
    return found


def score_answer(answer: str, question_product: Optional[str], vocab: Vocabulary,
                 context: str = "", reviews_coverage: bool = True) -> Score:
    answer = answer or ""
    mentions = product_mentions(answer, vocab)
    declined = _any(DECLINED_PATTERNS, answer)
    asks = _any(ASKS_PATTERNS, answer) and "?" in answer
    ungrounded = sorted(property_tokens(answer) - property_tokens(context)) if context else []
    loy, rev = bool(mentions['loyalty']), bool(mentions['reviews'])

    if question_product is None:
        if asks or (loy and rev):
            outcome = 'correct'
        elif loy or rev:
            outcome = 'picked_one'
        else:
            outcome = 'unclear'
    elif question_product == 'reviews' and not reviews_coverage:
        outcome = 'correct' if declined else 'answered_without_docs'
    elif declined:
        outcome = 'no_answer'
    elif asks:
        outcome = 'hedged'
    else:
        own, other = bool(mentions[question_product]), bool(mentions[OTHER[question_product]])
        if own and other:
            outcome = 'hedged'
        elif other:
            outcome = 'wrong_product'
        else:
            outcome = 'correct'
    return Score(outcome, mentions, declined, asks, ungrounded)


WRONG = {'wrong_product', 'answered_without_docs'}
SOFT = {'no_answer', 'hedged'}


def decide(counts: Dict[str, Dict[str, int]], screened: int) -> Dict:
    """Apply the pre-registered decision rule to per-arm outcome counts.

    counts: arm -> outcome -> n, over the screened named-product cells only.
    Rule (PRODUCT_LINE_SPLIT_SCOPE.md, step 7):
      1. A wrong on <= 10% of the set and <= 2: ship C2 if it adds <= 2
         no-answer/hedged outcomes over A, else keep A.
      2. Else the cheapest of C1, C2, D, B that at least halves A's wrong count
         without adding more than 2 no-answer/hedged outcomes.
      3. Else inconclusive: ship C2 and measure live answers.
    """
    def wrong(arm):
        return sum(counts.get(arm, {}).get(o, 0) for o in WRONG)

    def soft(arm):
        return sum(counts.get(arm, {}).get(o, 0) for o in SOFT)

    a_wrong, a_soft = wrong('A'), soft('A')
    summary = {arm: {'wrong': wrong(arm), 'no_answer_or_hedged': soft(arm)} for arm in counts}

    if screened and a_wrong <= min(2, 0.10 * screened):
        if 'C2' in counts and soft('C2') - a_soft <= 2:
            return {'ship': 'C2', 'reason': f"A is wrong on {a_wrong}/{screened}: low. C2 labels cost nothing extra in answers.", 'arms': summary}
        return {'ship': 'A', 'reason': f"A is wrong on {a_wrong}/{screened}: low, and C2 adds refusals or hedging.", 'arms': summary}

    for arm in ('C1', 'C2', 'D', 'B'):
        if arm in counts and wrong(arm) * 2 <= a_wrong and soft(arm) - a_soft <= 2:
            reason = f"{arm} cuts wrong-product answers from {a_wrong} to {wrong(arm)} without adding more than 2 refusals or hedges."
            if arm in ('D', 'B'):
                reason += " Needs the product selector (step 8)."
            return {'ship': arm, 'reason': reason, 'arms': summary}

    return {'ship': 'C2', 'reason': "Inconclusive: no arm halved A's wrong answers within the limits. Ship C2 and score live answers.",
            'arms': summary, 'inconclusive': True}
