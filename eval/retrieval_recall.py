#!/usr/bin/env python3
"""
Does the context the model reads contain the facts a question needs?

    python3 eval/retrieval_recall.py                 # every case
    python3 eval/retrieval_recall.py tier-onboarding  # some cases, by id
    python3 eval/retrieval_recall.py --json out.json
    python3 eval/retrieval_recall.py --no-neighbours  # as before neighbour expansion
    python3 eval/retrieval_recall.py --index memory   # the working tree's chunker

--index memory chunks the documents stored in Postgres with the chunker in
the working tree and searches them in memory (eval/memory_index.py), so a
chunking change is measured before production is re-indexed.

Runs build_rag_context() -- the code chat runs -- against the live vector
index for each case in eval/retrieval_cases.json, and checks the context for
each case's facts. No model calls: a wrong answer is either a retrieval
failure or a reasoning failure, and this tells them apart for the price of a
few vector reads.

Per case it prints:
    PASS/FAIL   every fact is in the context, or not
    raw rank    where the best chunk holding all the facts ranks for the
                retrieval query in a plain search of the ESP (None: no single
                chunk holds them all). Query A keeps the top 10.
    words       context size, to see what a retrieval change costs

Exit status 1 when a case fails. Vector and database reads only.
"""
import argparse
import contextlib
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'backend'))
sys.path.insert(0, os.path.join(BASE, 'eval'))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(BASE, '.env'))
os.environ.pop('RETRIEVAL_DEBUG', None)

CASES_PATH = os.path.join(BASE, 'eval', 'retrieval_cases.json')

# How deep the diagnostic search looks for the chunk holding the facts.
RAW_DEPTH = 200


def normalize(text):
    # \s matches the non-breaking spaces the crawler keeps from the HTML.
    return re.sub(r'\s+', ' ', text).strip()


def raw_rank(vectorizer, query, esp, facts):
    """1-based rank of the best chunk holding every fact, or None."""
    results = vectorizer.search(query, esp_filter=esp, n_results=RAW_DEPTH)
    for i, doc in enumerate((results.get('documents') or [[]])[0]):
        text = normalize(doc)
        if all(fact in text for fact in facts):
            return i + 1
    return None


def run_case(vectorizer, case, expand_neighbours=True):
    from rag_context import build_rag_context, chat_search_products
    esp = case['esp']
    with contextlib.redirect_stdout(io.StringIO()):   # filter_by_relevance logs every call
        rag = build_rag_context(vectorizer, case['text'], esp, case.get('history', []),
                                product=case.get('product'),
                                expand_neighbours=expand_neighbours,
                                search_products=chat_search_products(case.get('product')))
    context = normalize(rag.context)
    facts = [normalize(f) for f in case['must_contain']]
    missing = [f for f in facts if f not in context]
    return {
        'id': case['id'],
        'control': bool(case.get('control')),
        'passed': not missing,
        'missing': missing,
        'raw_rank': raw_rank(vectorizer, rag.enhanced_query, rag.esp_normalized, facts),
        'sources': len(rag.metadatas),
        'words': len(rag.context.split()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('ids', nargs='*', help='case ids to run (default: all)')
    parser.add_argument('--json', help='also write the results here')
    parser.add_argument('--index', choices=('live', 'memory'), default='live',
                        help='live: the production index; memory: rebuilt from Postgres '
                             'with the working tree chunker')
    parser.add_argument('--no-neighbours', action='store_true',
                        help='build contexts without neighbour expansion')
    args = parser.parse_args()

    with open(CASES_PATH) as f:
        cases = json.load(f)['cases']
    if args.ids:
        unknown = set(args.ids) - {c['id'] for c in cases}
        if unknown:
            sys.exit(f"Unknown case id(s): {', '.join(sorted(unknown))}")
        cases = [c for c in cases if c['id'] in args.ids]

    if args.index == 'memory':
        from memory_index import MemoryIndex
        with contextlib.redirect_stdout(io.StringIO()):   # database adapter start-up logs
            vectorizer = MemoryIndex()
        print(f"memory index: {vectorizer.stats()}\n")
    else:
        from adapters.vector.vector_manager import get_vector_adapter
        vectorizer = get_vector_adapter()

    results = []
    print(f"{'case':<24} {'result':<6} {'raw rank':>8} {'sources':>7} {'words':>6}")
    for case in cases:
        r = run_case(vectorizer, case, expand_neighbours=not args.no_neighbours)
        results.append(r)
        label = r['id'] + (' (ctl)' if r['control'] else '')
        print(f"{label:<24} {'PASS' if r['passed'] else 'FAIL':<6} "
              f"{str(r['raw_rank']):>8} {r['sources']:>7} {r['words']:>6}")
        for fact in r['missing']:
            print(f"    missing: {fact!r}")

    passed = sum(r['passed'] for r in results)
    print(f"\n{passed}/{len(results)} passed; "
          f"mean context {sum(r['words'] for r in results) / max(len(results), 1):.0f} words")

    if args.json:
        with open(args.json, 'w') as f:
            json.dump(results, f, indent=2)

    sys.exit(0 if passed == len(results) else 1)


if __name__ == '__main__':
    main()
