#!/usr/bin/env python3
"""
Prove a refactor of chat()'s retrieval did not change what the model is sent.

    python3 eval/check_context_unchanged.py capture /path/golden.json   # before
    python3 eval/check_context_unchanged.py check   /path/golden.json   # after

Drives POST /api/chat through Flask's test client against the live vector
index, with the model call replaced by a stub that records the exact
(message, context, history) it would have been given. Analytics go to a
throwaway SQLite file and sessions stay in memory, so nothing is written to
production Postgres. Vector reads only.

Only valid while the index is unchanged between capture and check: run them
back to back.
"""
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Must be set before app.py loads .env (load_dotenv does not override).
os.environ['DATABASE_PROVIDER'] = 'sqlite'
os.environ['SQLITE_DB_PATH'] = os.path.join(tempfile.mkdtemp(), 'golden.db')
os.environ['SESSION_PROVIDER'] = 'memory'
os.environ['USE_ASYNC_CRAWL'] = 'false'
os.environ.pop('RETRIEVAL_DEBUG', None)

sys.path.insert(0, os.path.join(BASE, 'backend'))
os.chdir(os.path.join(BASE, 'backend'))

import app as app_module  # noqa: E402

ANSWER = ("To set this up, open your Yotpo Loyalty admin and go to Integrations Center, "
          "then pick the ESP and map the loyalty properties.")

CASES = [
    # (esp as the frontend sends it, message, history)
    ('klaviyo', 'How do I send a points expiration reminder?', []),
    ('klaviyo', 'What loyalty customer properties are available for segmentation?', []),
    ('attentive', 'Where in the Yotpo admin do I start the integration?', []),
    ('attentive', 'How do I trigger a journey when a review is submitted?', []),
    ('dotdigital', 'How do I add review content to an email?', []),
    ('omnisend', 'How do I connect Yotpo to my ESP?', []),
    ('listrak', 'How do I connect Yotpo Reviews to my ESP?', []),
    ('ometria', 'Which loyalty events sync to my ESP?', []),
    ('postscript', 'How do I show a point balance in an SMS?', []),
    ('emarsys', 'Which attributes does Yotpo send?', []),
    ('other_webhook', 'How do I subscribe to app events?', []),
    ('klaviyo', 'zzqx', []),  # nothing clears the threshold
    # follow-up: the previous answer is appended to the retrieval query
    ('klaviyo', 'And what about tiers?', [
        {'role': 'user', 'content': 'How do I set up the integration?'},
        {'role': 'assistant', 'content': ANSWER},
    ]),
]


def run():
    captured = []

    def stub(message, context, conversation_history=None, product=None):
        # product is not recorded: golden files from before the product
        # picker have none, and the check is about the context.
        captured.append({'message': message, 'context': context,
                         'history': conversation_history})
        return 'STUB'

    app_module.ai_client.generate_response = stub
    client = app_module.app.test_client()
    out = []
    # Each case twice: as an old browser tab sends it (no product) and as the
    # current one does for Loyalty. Code from before the product picker
    # ignores the field, so both must match a golden captured on it.
    for sends_product in (False, True):
        for esp, message, history in CASES:
            captured.clear()
            body = {'message': message, 'esp': esp, 'session_id': 'golden-session',
                    'history': history}
            if sends_product:
                body['product'] = 'loyalty'
            r = client.post('/api/chat', json=body)
            data = r.get_json()
            out.append({
                'esp': esp, 'message': message, 'status': r.status_code,
                'sources': data.get('sources'),
                'model_input': captured[0] if captured else None,
            })
    return out


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ('capture', 'check'):
        print(__doc__)
        sys.exit(2)
    mode, path = sys.argv[1], sys.argv[2]
    result = run()
    if mode == 'capture':
        with open(path, 'w') as f:
            json.dump(result, f, indent=1)
        print(f"captured {len(result)} cases -> {path}")
        return
    with open(path) as f:
        golden = json.load(f)
    bad = 0
    for g, r in zip(golden, result):
        if g != r:
            bad += 1
            print(f"DIFF: {g['esp']} / {g['message']!r}")
            for key in ('status', 'sources', 'model_input'):
                if g.get(key) != r.get(key):
                    print(f"   differs in {key}")
    if len(golden) != len(result):
        bad += 1
        print(f"case count differs: {len(golden)} vs {len(result)}")
    print(f"{len(result) - bad}/{len(result)} cases identical")
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
