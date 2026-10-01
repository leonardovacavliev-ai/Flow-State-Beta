#!/usr/bin/env python3
"""
The product-line experiment (PRODUCT_LINE_SPLIT_SCOPE.md, step 7).

Question: when Loyalty and Reviews documentation sit side by side, is it enough
to label each source in the context and instruct the model, or must retrieval
filter by product?

    python3 eval/product_eval.py status             # labels and Reviews coverage
    python3 eval/product_eval.py export-questions   # saved real questions -> file to tag
    python3 eval/product_eval.py screen             # retrieval only, no model calls
    python3 eval/product_eval.py run                # arms + scoring + decision
    python3 eval/product_eval.py rescore DIR        # re-score saved answers
    python3 eval/product_eval.py csm-agreement DIR  # scorer vs the CSM's verdicts

Arms (all on one base prompt, all with the coverage guard):
    A   today's context
    C1  + instruction: name the product you describe, ask if unclear
    C2  + C1 + "Yotpo product line: ..." on every source
    D   + C2, with the system prompt filled for the question's product -- what
        the chat product picker does in production
    B   + D + retrieval restricted to that product and shared documents

Production is only read: labels and prompts over a read-only Postgres session,
vectors by query. Model calls use GEMINI_API_KEY from .env at temperature 0,
set in this process only.
"""
import argparse
import contextlib
import csv
import hashlib
import io
import json
import os
import random
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL = os.path.join(BASE, 'eval')
sys.path.insert(0, os.path.join(BASE, 'backend'))
sys.path.insert(0, EVAL)

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(BASE, '.env'))

from product_scorer import Vocabulary, decide, score_answer  # noqa: E402

ARMS = ['A', 'C1', 'C2', 'D', 'B']
ARMS_NEEDING_LABELS = {'C2', 'D', 'B'}
ARMS_NEEDING_PRODUCT = {'D', 'B'}   # the user picked a product; not for questions naming none
UNTAGGED = '?'                       # product placeholder in exported questions
QUESTION_FILES = [os.path.join(EVAL, 'questions.json'), os.path.join(EVAL, 'questions_real.json')]


# ---------------------------------------------------------------- data access

def _pg():
    """Read-only connection straight to Postgres.

    Deliberately not the app's database adapter: that one runs schema
    migrations on connect, which would change production from an eval.
    """
    import psycopg2
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.set_session(readonly=True)
    return conn


def _documents(labels_db):
    """Rows (esp, url, product, content). labels_db: None for production, or a SQLite path."""
    if labels_db:
        import sqlite3
        conn = sqlite3.connect(labels_db)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(esp_documents)")}
        product = "d.product" if 'product' in cols else "NULL"
        rows = conn.execute(f"SELECT e.name, d.url, {product}, d.content FROM esp_documents d "
                            "JOIN esps e ON e.id = d.esp_id").fetchall()
        conn.close()
        return rows, 'product' in cols
    conn = _pg()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() "
                "AND table_name = 'esp_documents' AND column_name = 'product'")
    has_column = cur.fetchone() is not None
    product = "d.product" if has_column else "NULL"
    cur.execute(f"SELECT e.name, d.url, {product}, d.content FROM esp_documents d "
                "JOIN esps e ON e.id = d.esp_id")
    rows = cur.fetchall()
    conn.close()
    return rows, has_column


def _provisional_label(url, content):
    """Stand-in for a missing label: the Yotpo header, else the URL. Not a decision."""
    from product_labels import header_label
    h = header_label(content)
    if h:
        return h, 'header'
    u = (url or '').lower()
    if 'review' in u:
        return 'reviews', 'url'
    if 'loyalty' in u or 'referral' in u:
        return 'loyalty', 'url'
    return 'shared', 'url'


class Labels:
    def __init__(self, labels_db=None, provisional=False):
        rows, self.column_exists = _documents(labels_db)
        self.source = labels_db or 'production Postgres'
        self.by_key = {}
        self.provenance = Counter()
        self.unlabelled = []
        self.has_content = {}
        for esp, url, product, content in rows:
            self.has_content[(esp, url)] = content is not None
            if product:
                self.by_key[(esp, url)] = product
                self.provenance['admin'] += 1
            elif content is None:
                continue          # failed crawl: nothing retrievable to label
            elif provisional:
                label, how = _provisional_label(url, content)
                self.by_key[(esp, url)] = label
                self.provenance[f'provisional:{how}'] += 1
            else:
                self.unlabelled.append((esp, url))
        self.esps = sorted({esp for esp, _ in self.has_content} - {'global'})

    def product_of(self, metadata):
        return self.by_key.get((metadata.get('esp'), metadata.get('source_url')))

    def reviews_coverage(self, indexed):
        """ESP -> has a Reviews-labelled document with content and vectors."""
        covered = {esp: False for esp in self.esps}
        for (esp, url), product in self.by_key.items():
            if product == 'reviews' and self.has_content.get((esp, url)) and (esp, url) in indexed:
                covered[esp] = True
        return covered


def _vectorizer():
    from adapters.vector.vector_manager import get_vector_adapter
    return get_vector_adapter()


def _indexed_documents(vectorizer):
    """(esp, source_url) pairs that have at least one vector, and chunk texts for the vocabulary."""
    index = getattr(vectorizer, 'index', None)
    if index is None:
        return None, []
    ids = [i for page in index.list() for i in page]
    pairs, chunks = set(), []
    for i in range(0, len(ids), 100):
        for v in index.fetch(ids=ids[i:i + 100]).vectors.values():
            md = v.metadata or {}
            pairs.add((md.get('esp'), md.get('source_url')))
            chunks.append(md)
    return pairs, chunks


def _production_config():
    conn = _pg()
    cur = conn.cursor()
    cur.execute("SELECT value FROM app_settings WHERE key = 'app_config'")
    row = cur.fetchone()
    conn.close()
    return json.loads(row[0]) if row else {}


# ---------------------------------------------------------------- questions

def load_questions(paths, esps):
    """Expand question files into cells: one per (question, ESP)."""
    cells, untagged = [], 0
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path) as f:
            data = json.load(f)
        for q in data['questions']:
            if q.get('product') == UNTAGGED:
                untagged += 1
                continue
            targets = esps if q.get('esps', 'all') == 'all' else q['esps']
            for esp in targets:
                cells.append({
                    'cell': f"{q['id']}@{esp}", 'question_id': q['id'], 'esp': esp,
                    'text': q['text'], 'product': q.get('product'),
                    'history': q.get('history', []),
                })
    return cells, untagged


# ---------------------------------------------------------------- retrieval

def _arm_product(cell, arm):
    """The product the arm is told: only D and B, as if picked in chat."""
    return cell['product'] if arm in ARMS_NEEDING_PRODUCT else None


def _build(vectorizer, cell, arm, labels, coverage):
    from rag_context import build_rag_context
    # Every arm gets the coverage note where it applies; whether it is worded
    # as definite depends on whether the arm knows the product.
    kwargs = {'product': _arm_product(cell, arm),
              'reviews_coverage': False if not coverage.get(cell['esp'], False) else None}
    if arm in ('C1', 'C2', 'D', 'B'):
        kwargs['product_instruction'] = True
    if arm in ARMS_NEEDING_LABELS:
        kwargs['product_of'] = labels.product_of
    if arm == 'B':
        kwargs['filter_to_product'] = True
    with contextlib.redirect_stdout(io.StringIO()):   # filter_by_relevance logs every call
        return build_rag_context(vectorizer, cell['text'], cell['esp'], cell['history'], **kwargs)


def screen(vectorizer, cells, labels, coverage):
    """Keep only cells where arms can differ: the other product reaches the context."""
    kept = []
    for cell in cells:
        rag = _build(vectorizer, cell, 'A', labels, coverage)
        found = Counter(labels.product_of(m) for m in rag.metadatas)
        product = cell['product']
        if product is None:
            reason = 'both products retrieved' if found['loyalty'] and found['reviews'] else None
        elif product == 'reviews' and not coverage.get(cell['esp'], False):
            reason = 'Reviews question, no Reviews documentation'
        else:
            other = 'reviews' if product == 'loyalty' else 'loyalty'
            reason = f"{found[other]} {other} chunk(s) retrieved" if found[other] else None
        cell = dict(cell, retrieved=dict(found), unlabelled_retrieved=found[None], keep_reason=reason)
        if reason:
            kept.append(cell)
    return kept


# ---------------------------------------------------------------- commands

def cmd_status(args):
    labels = Labels(args.labels_db)
    vectorizer = _vectorizer()
    indexed, _ = _indexed_documents(vectorizer)
    print(f"labels from: {labels.source}"
          + ("" if labels.column_exists else "  (no `product` column yet: deploy, or label locally)"))
    per_esp = defaultdict(Counter)
    for (esp, url), product in labels.by_key.items():
        per_esp[esp][product] += 1
    for esp, url in labels.unlabelled:
        per_esp[esp]['unlabelled'] += 1
    print(f"\n{'esp':<15}{'loyalty':>8}{'reviews':>8}{'shared':>8}{'unlabelled':>12}")
    for esp in sorted(per_esp):
        c = per_esp[esp]
        print(f"{esp:<15}{c['loyalty']:>8}{c['reviews']:>8}{c['shared']:>8}{c['unlabelled']:>12}")
    coverage = labels.reviews_coverage(indexed or set(labels.by_key))
    print("\nReviews coverage (a Reviews-labelled document with content and vectors):")
    for esp in labels.esps:
        print(f"  {esp:<15}{'yes' if coverage[esp] else 'no'}")
    if labels.unlabelled:
        print(f"\n{len(labels.unlabelled)} documents with content still need a label.")


def cmd_export_questions(args):
    """Saved user questions with their history, to tag by hand. Prints counts only."""
    conn = _pg()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.esp, m.seq, m.role, m.content
        FROM conversation_messages m JOIN conversations c ON c.id = m.conversation_id
        ORDER BY c.id, m.seq
    """)
    by_conv = defaultdict(list)
    esp_of = {}
    for conv_id, esp, seq, role, content in cur.fetchall():
        by_conv[conv_id].append({'seq': seq, 'role': role, 'content': content})
        esp_of[conv_id] = esp
    conn.close()
    questions = []
    for conv_id, messages in by_conv.items():
        for i, m in enumerate(messages):
            if m['role'] != 'user':
                continue
            questions.append({
                'id': f"real-{str(conv_id)[:8]}-{m['seq']}",
                'text': m['content'],
                'product': UNTAGGED,
                'esps': [esp_of[conv_id]],
                'history': [{'role': h['role'], 'content': h['content']} for h in messages[:i]][-20:],
            })
    out = os.path.join(EVAL, 'questions_real.json')
    with open(out, 'w') as f:
        json.dump({'_how_to_tag': (
            "Set each product to 'loyalty', 'reviews', or null when the question names "
            "no product. Questions left as '?' are skipped. This file holds real user "
            "questions and is gitignored."), 'questions': questions}, f, indent=1)
    print(f"wrote {len(questions)} questions from {len(by_conv)} conversations to {out}")


def _setup(args):
    labels = Labels(args.labels_db, provisional=args.provisional_labels)
    vectorizer = _vectorizer()
    indexed, chunk_meta = _indexed_documents(vectorizer)
    coverage = labels.reviews_coverage(indexed or set(labels.by_key))
    cells, untagged = load_questions(args.questions or QUESTION_FILES, labels.esps)
    if args.limit:
        random.Random(0).shuffle(cells)
        cells = cells[:args.limit]
    return labels, vectorizer, chunk_meta, coverage, cells, untagged


def _report_labels(labels, arms):
    print(f"labels: {dict(labels.provenance)} from {labels.source}")
    if labels.unlabelled and set(arms) & ARMS_NEEDING_LABELS:
        print(f"\n{len(labels.unlabelled)} documents are unlabelled, and arms {sorted(set(arms) & ARMS_NEEDING_LABELS)} "
              "need labels. Label them in the admin screen, or pass --provisional-labels "
              "to fill gaps from the Yotpo header and URL (fine for a dry run, not for a decision).")
        return False
    return True


def cmd_screen(args):
    labels, vectorizer, _, coverage, cells, untagged = _setup(args)
    _report_labels(labels, [])
    print(f"cells: {len(cells)} ({untagged} untagged questions skipped)")
    kept = screen(vectorizer, cells, labels, coverage)
    print(f"kept after screening: {len(kept)}\n")
    for c in kept:
        print(f"  {c['cell']:<45} {str(c['product']):<8} {c['keep_reason']}")
    unl = sum(c['unlabelled_retrieved'] for c in kept)
    if unl:
        print(f"\nnote: {unl} retrieved chunks had no label; screening treats them as neither product.")


def _generate(client, cell, context, product=None, retries=3):
    for attempt in range(retries):
        try:
            return client.generate_response(cell['text'], context, cell['history'], product=product)
        except Exception as e:
            if attempt == retries - 1:
                return f"[generation failed: {e}]"
            time.sleep(2 ** attempt * 2)


def _score_rows(rows, vocab):
    for r in rows:
        s = score_answer(r['answer'], r['product'], vocab, context=r.get('context', ''),
                         reviews_coverage=r['reviews_coverage'])
        r.update(outcome=s.outcome, mentions=s.mentions, declined=s.declined,
                 asks=s.asks, ungrounded_properties=s.ungrounded_properties)
    return rows


def _summarise(rows, out_dir):
    named = [r for r in rows if r['product'] is not None]
    counts = defaultdict(Counter)
    for r in named:
        counts[r['arm']][r['outcome']] += 1
    screened = len({r['cell'] for r in named})
    decision = decide({a: dict(c) for a, c in counts.items()}, screened)
    unnamed = defaultdict(Counter)
    for r in rows:
        if r['product'] is None:
            unnamed[r['arm']][r['outcome']] += 1
    summary = {'screened_named_cells': screened, 'named': {a: dict(c) for a, c in counts.items()},
               'no_product_questions': {a: dict(c) for a, c in unnamed.items()}, 'decision': decision}
    with open(os.path.join(out_dir, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=1)

    print(f"\nnamed-product cells: {screened}")
    outcomes = ['correct', 'wrong_product', 'answered_without_docs', 'hedged', 'no_answer']
    print(f"{'arm':<5}" + "".join(f"{o:>23}" for o in outcomes))
    for arm in ARMS:
        if arm in counts:
            print(f"{arm:<5}" + "".join(f"{counts[arm][o]:>23}" for o in outcomes))
    if unnamed:
        print("\nquestions naming no product (A, C1, C2 only):")
        for arm in ('A', 'C1', 'C2'):
            if arm in unnamed:
                print(f"  {arm:<4}{dict(unnamed[arm])}")
    print(f"\nDECISION: ship {decision['ship']}. {decision['reason']}")
    if 'D' in counts and 'B' in counts:
        d, b = decision['arms']['D']['wrong'], decision['arms']['B']['wrong']
        print(f"D vs B (does the filter add anything over being told the product?): wrong {d} vs {b}")
    return summary


def _write_csm_sample(rows, out_dir, n=20):
    """Shuffled, arm-blind answers for a CSM, stratified across arms and outcomes."""
    rng = random.Random(0)
    strata = defaultdict(list)
    for r in rows:
        strata[(r['arm'], r['outcome'])].append(r)
    picked = []
    while len(picked) < n and any(strata.values()):
        for key in list(strata):
            if strata[key] and len(picked) < n:
                picked.append(strata[key].pop(rng.randrange(len(strata[key]))))
    rng.shuffle(picked)
    key = {}
    with open(os.path.join(out_dir, 'csm_sample.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['id', 'esp', 'question', 'question_is_about', 'answer', 'verdict',
                    'verdict options: correct / wrong_product / hedged / no_answer (for a question about no product: correct / picked_one / unclear)'])
        for i, r in enumerate(picked, 1):
            sid = f"s{i:02d}"
            key[sid] = {'arm': r['arm'], 'cell': r['cell'], 'mechanical': r['outcome']}
            w.writerow([sid, r['esp'], r['text'], r['product'] or 'no product named', r['answer'], '', ''])
    with open(os.path.join(out_dir, 'csm_key.json'), 'w') as f:
        json.dump(key, f, indent=1)


def cmd_run(args):
    labels, vectorizer, chunk_meta, coverage, cells, untagged = _setup(args)
    arms = args.arms.split(',')
    if not _report_labels(labels, arms):
        sys.exit(1)

    config = _production_config()
    model = args.model or config.get('ai_model', {}).get('model_name', 'gemini-flash-latest')
    provider = config.get('ai_model', {}).get('provider', 'gemini')
    if args.prompt:
        with open(args.prompt) as f:
            prompt, prompt_source = f.read(), args.prompt
    else:
        prompt, prompt_source = config.get('system_prompt', ''), 'production'
    if '[[' not in prompt:
        print("WARNING: the prompt has no [[product]] placeholders, so every arm gets the same "
              "prompt and D cannot differ from C2 by what the prompt says. Add them in the admin "
              "prompt editor (or pass --prompt) for a result you act on.")
    if 'latest' in model:
        print(f"WARNING: '{model}' is an alias that moves between versions. Pin one with --model.")

    kept = screen(vectorizer, cells, labels, coverage)
    plan = [(c, arm) for c in kept for arm in arms
            if not (arm in ARMS_NEEDING_PRODUCT and c['product'] is None)]
    print(f"\n{len(cells)} cells, {len(kept)} kept after screening, {len(plan)} model calls "
          f"({provider}/{model}), prompt: {prompt_source}; {untagged} untagged questions skipped")
    if not plan:
        print("Nothing to run.")
        return
    if not args.yes and input("Run? [y/N] ").strip().lower() != 'y':
        return

    os.environ['AI_TEMPERATURE'] = '0'   # this process only
    from ai_client import AIClient
    with contextlib.redirect_stdout(io.StringIO()):
        client = AIClient(provider=provider, model_name=model, system_prompt=prompt)

    out_dir = os.path.join(EVAL, 'results', datetime.now().strftime('%Y%m%d-%H%M%S'))
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    with open(os.path.join(out_dir, 'answers.jsonl'), 'w') as f:
        for i, (cell, arm) in enumerate(plan, 1):
            rag = _build(vectorizer, cell, arm, labels, coverage)
            answer = _generate(client, cell, rag.context, _arm_product(cell, arm))
            row = {**{k: cell[k] for k in ('cell', 'question_id', 'esp', 'text', 'product', 'keep_reason')},
                   'arm': arm, 'reviews_coverage': coverage.get(cell['esp'], False),
                   'sources': [{'file': m.get('filename'), 'product': labels.product_of(m)} for m in rag.metadatas],
                   'context': rag.context, 'answer': answer}
            rows.append(row)
            f.write(json.dumps(row) + '\n')
            print(f"  [{i}/{len(plan)}] {arm:<3} {cell['cell']}")

    vocab = Vocabulary.from_chunks((labels.product_of(m), m.get('text', '')) for m in chunk_meta)
    _score_rows(rows, vocab)
    with open(os.path.join(out_dir, 'scored.jsonl'), 'w') as f:
        for r in rows:
            f.write(json.dumps({k: v for k, v in r.items() if k != 'context'}) + '\n')
    with open(os.path.join(out_dir, 'config.json'), 'w') as f:
        json.dump({'provider': provider, 'model': model, 'prompt_source': prompt_source,
                   'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                   'labels': dict(labels.provenance), 'labels_source': labels.source,
                   'arms': arms, 'cells': len(cells), 'kept': len(kept)}, f, indent=1)
    _summarise(rows, out_dir)
    _write_csm_sample(rows, out_dir)
    print(f"\nresults: {out_dir}\nCSM sample to fill in: {os.path.join(out_dir, 'csm_sample.csv')}")


def cmd_rescore(args):
    rows = [json.loads(l) for l in open(os.path.join(args.dir, 'answers.jsonl'))]
    labels = Labels(args.labels_db, provisional=args.provisional_labels)
    _, chunk_meta = _indexed_documents(_vectorizer())
    vocab = Vocabulary.from_chunks((labels.product_of(m), m.get('text', '')) for m in chunk_meta)
    _score_rows(rows, vocab)
    _summarise(rows, args.dir)


def cmd_csm_agreement(args):
    key = json.load(open(os.path.join(args.dir, 'csm_key.json')))
    agree = total = 0
    disagreements = []
    with open(os.path.join(args.dir, 'csm_sample.csv')) as f:
        for row in csv.DictReader(f):
            verdict = (row.get('verdict') or '').strip().lower()
            if not verdict:
                continue
            total += 1
            mech = key[row['id']]['mechanical']
            mech = 'wrong_product' if mech == 'answered_without_docs' else mech
            if verdict == mech:
                agree += 1
            else:
                disagreements.append((row['id'], key[row['id']]['arm'], mech, verdict))
    if not total:
        print("No verdicts filled in yet.")
        return
    print(f"scorer agrees with the CSM on {agree}/{total} ({100 * agree / total:.0f}%)")
    for sid, arm, mech, verdict in disagreements:
        print(f"  {sid} arm {arm}: scorer said {mech}, CSM said {verdict}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)

    def common(sp):
        sp.add_argument('--labels-db', help="read labels from a local SQLite file instead of production")
        sp.add_argument('--provisional-labels', action='store_true',
                        help="fill missing labels from the Yotpo header, else the URL (dry runs only)")
        sp.add_argument('--questions', nargs='+', help="question files (default: questions.json, questions_real.json)")
        sp.add_argument('--limit', type=int, help="run a random subset of this many cells")

    common(sub.add_parser('status'))
    sub.add_parser('export-questions')
    common(sub.add_parser('screen'))
    run = sub.add_parser('run')
    common(run)
    run.add_argument('--arms', default=','.join(ARMS))
    run.add_argument('--prompt', help="system prompt template file; default is production's stored prompt")
    run.add_argument('--model', help="pin a model version, e.g. gemini-2.5-flash")
    run.add_argument('--yes', action='store_true', help="don't ask before spending model calls")
    for name in ('rescore', 'csm-agreement'):
        sp = sub.add_parser(name)
        sp.add_argument('dir')
        if name == 'rescore':
            sp.add_argument('--labels-db')
            sp.add_argument('--provisional-labels', action='store_true')

    args = p.parse_args()
    {'status': cmd_status, 'export-questions': cmd_export_questions, 'screen': cmd_screen,
     'run': cmd_run, 'rescore': cmd_rescore, 'csm-agreement': cmd_csm_agreement}[args.cmd](args)


if __name__ == '__main__':
    main()
