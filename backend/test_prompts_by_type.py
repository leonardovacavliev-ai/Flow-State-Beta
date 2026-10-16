"""
System prompts by platform type, and the integration facts block (C1.7).

    python3 backend/test_prompts_by_type.py        # (or pytest)
    python3 backend/test_prompts_by_type.py --write-rag-fixture
        # rewrites fixtures/prompts/rag_context_default.json from whichever
        # rag_context.py is importable; run it on the code *before* a change
        # to build_rag_context, never after (see test_rag_context_defaults_unchanged)

Runs on a throwaway SQLite file, a temp config folder and a fake vector
store. No model is called and nothing touches production.
"""
import json
import os
import shutil
import sys
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TMP = tempfile.mkdtemp(prefix='prompts-by-type-')
# Before anything reads them (app.py's load_dotenv does not override)
os.environ['DATABASE_PROVIDER'] = 'sqlite'
os.environ['SQLITE_DB_PATH'] = os.path.join(TMP, 'test.db')
os.environ['SESSION_PROVIDER'] = 'memory'
os.environ['USE_ASYNC_CRAWL'] = 'false'
os.environ['VECTOR_DB_PROVIDER'] = 'chromadb'   # belt and braces; app_client() stubs the factory
os.environ.pop('ADMIN_OWNER_EMAILS', None)
os.environ.pop('RETRIEVAL_DEBUG', None)
sys.path.insert(0, HERE)

RAG_FIXTURE = os.path.join(HERE, 'fixtures', 'prompts', 'rag_context_default.json')
TODAYS_TEMPLATE = os.path.join(REPO, 'eval', 'prompts', 'system_prompt_template.txt')
OTHER_TYPES = ('storefront', 'service', 'data', 'content')


# ---------- helpers ----------

def raises(exc, fn):
    try:
        fn()
    except exc as e:
        return e
    raise AssertionError(f"expected {exc.__name__}")


def todays_template():
    with open(TODAYS_TEMPLATE, encoding='utf-8') as f:
        return f.read()


def fresh_config():
    """A ConfigManager on its own folder and a clean stored config: the
    fresh-install default, as config_manager writes it."""
    from adapters.database.db_manager import get_database_adapter
    from config_manager import ConfigManager
    db = get_database_adapter()
    db.execute_query("DELETE FROM app_settings WHERE key IN (%s, %s)",
                     (ConfigManager.CONFIG_KEY, ConfigManager.AUDIT_KEY))
    base = tempfile.mkdtemp(dir=TMP)
    os.makedirs(os.path.join(base, 'backend'))
    return ConfigManager(base)


class CapturingClient:
    """An AIClient whose provider call records the system prompt it got."""

    def __new__(cls, prompts):
        from ai_client import AIClient
        client = AIClient('none', 'test-model', prompts['messaging'], prompts=prompts)
        client.provider, client.configured = 'gemini', True
        client.sent = []
        client._generate_gemini = lambda message, context, history, system_prompt: (
            client.sent.append(system_prompt) or 'ok')
        return client


# ---------- 1. messaging is today's prompt, byte for byte (I2) ----------

def test_messaging_prompt_is_todays_rendered_template():
    from prompt_template import render
    cm = fresh_config()
    stored = cm.get_system_prompt()
    # The fresh-install default and the deploy template are the same text
    assert stored == todays_template() == cm.get_system_prompt('messaging')
    client = CapturingClient(cm.get_all_system_prompts())
    for product in (None, 'loyalty', 'reviews'):
        client.generate_response('q', 'ctx', [], product=product)                  # default type
        client.generate_response('q', 'ctx', [], product=product, platform_type='messaging')
        assert client.sent[-2] == client.sent[-1] == render(todays_template(), product)


def test_messaging_reads_the_stored_prompt_not_a_default():
    cm = fresh_config()
    cm.update_system_prompt('Custom messaging prompt for [[product]].', 'a@yotpo.com')
    assert cm.get_system_prompt() == 'Custom messaging prompt for [[product]].'
    assert cm.get_all_system_prompts()['messaging'] == 'Custom messaging prompt for [[product]].'


# ---------- 2. the shipped defaults ----------

def test_shipped_defaults_validate_and_carry_the_common_blocks():
    from prompt_blocks import CLOSING, COMMON_RULES, OTHER_TYPES as TYPES, shipped_default
    from prompt_template import product_warning, render, validate
    assert TYPES == OTHER_TYPES
    seen = set()
    for t in OTHER_TYPES:
        text = shipped_default(t)
        assert not text.startswith('#') and not text.startswith('\n') and not text.endswith('\n'), t
        assert 'DRAFT' not in text, t
        assert validate(text) == [], t
        assert product_warning(text) is None, t
        assert COMMON_RULES in text and CLOSING in text, t
        assert '<common rules block>' not in text and '<closing block>' not in text, t
        assert text not in seen and text != todays_template(), t
        seen.add(text)
        for product in ('loyalty', 'reviews'):
            assert '[[' not in render(text, product), (t, product)
    # The closing block ends with today's closing text, word for word
    assert todays_template().endswith(CLOSING.split('\n\n', 1)[1])
    raises(ValueError, lambda: shipped_default('messaging'))
    raises(ValueError, lambda: shipped_default('nope'))


def test_shipped_files_open_with_the_draft_line():
    for t in OTHER_TYPES:
        with open(os.path.join(HERE, 'prompts', f'system_prompt_{t}.txt'), encoding='utf-8') as f:
            assert f.readline() == f"# DRAFT — Leo rewrites this in the {t} wave\n", t


# ---------- 3. a type with nothing stored gets its default, never messaging ----------

def test_unstored_type_gets_its_default_not_messaging():
    from prompt_blocks import shipped_default
    from prompt_template import render
    cm = fresh_config()
    assert cm.get_config()['system_prompts'] == {}
    assert not cm.has_stored_prompt('storefront') and cm.has_stored_prompt('messaging')
    assert cm.get_system_prompt('storefront') == shipped_default('storefront')
    assert cm.get_system_prompt('storefront') != cm.get_system_prompt('messaging')
    raises(ValueError, lambda: cm.get_system_prompt('nope'))
    raises(ValueError, lambda: cm.update_system_prompt('x', 'a@yotpo.com', 'nope'))

    client = CapturingClient(cm.get_all_system_prompts())
    client.generate_response('q', 'ctx', [], product='reviews', platform_type='storefront')
    assert client.sent[-1] == render(shipped_default('storefront'), 'reviews')
    raises(ValueError, lambda: client.generate_response('q', 'ctx', [], platform_type='nope'))

    # An AIClient built without the other prompts (an eval script) still
    # never answers a storefront question with the messaging prompt
    from ai_client import AIClient
    bare = AIClient('none', 'm', 'MESSAGING ONLY')
    assert bare.prompts['storefront'] == shipped_default('storefront')
    assert bare.prompts['messaging'] == 'MESSAGING ONLY'


def test_storing_one_type_leaves_the_others():
    from prompt_blocks import shipped_default
    cm = fresh_config()
    messaging = cm.get_system_prompt()
    cm.update_system_prompt('Storefront v1 for [[product]].', 'a@yotpo.com', 'storefront')
    assert cm.get_system_prompt('storefront') == 'Storefront v1 for [[product]].'
    assert cm.get_system_prompt() == messaging
    assert cm.get_system_prompt('service') == shipped_default('service')
    entry = cm.get_audit_log()[-1]
    assert entry['platform_type'] == 'storefront'
    assert entry['backup']['system_prompts'] == {} and entry['backup']['system_prompt'] == messaging
    cm.update_system_prompt('Messaging v2.', 'a@yotpo.com')
    assert cm.get_audit_log()[-1]['platform_type'] == 'messaging'
    assert cm.get_system_prompt('storefront') == 'Storefront v1 for [[product]].'


# ---------- 4. an old-style audit entry restores as before ----------

def test_old_style_restore_leaves_system_prompts_intact():
    cm = fresh_config()
    original = cm.get_system_prompt()
    cm.update_model_config('openai', 'gpt-4o', 'a@yotpo.com')         # an entry with no type
    cm.update_system_prompt('Service v1.', 'a@yotpo.com', 'service')
    # An entry as the code before C1.7 wrote it: no platform_type, no
    # system_prompts in its backup
    old = {'timestamp': '2026-10-01T10:00:00', 'user_email': 'old@yotpo.com',
           'description': 'Updated system prompt',
           'backup': {'ai_model': {'provider': 'gemini', 'model_name': 'gemini-flash-latest'},
                      'system_prompt': 'Before [[product]].'},
           'changes': {'system_prompt': original}}
    cm._add_audit_entry(old)
    cm.restore_from_backup(-1, 'a@yotpo.com')
    config = cm.get_config()
    assert config['system_prompt'] == 'Before [[product]].'
    assert config['ai_model']['provider'] == 'gemini'                  # as today: model too
    assert config['system_prompts'] == {'service': 'Service v1.'}
    assert 'platform_type' not in cm.get_audit_log()[-1]
    # The model change entry (no type) also restores model + messaging only
    log = cm.get_audit_log()
    model_entry = next(i for i, e in enumerate(log) if e['description'].startswith('Changed AI model'))
    cm.restore_from_backup(model_entry, 'a@yotpo.com')
    assert cm.get_config()['system_prompts'] == {'service': 'Service v1.'}
    assert cm.get_config()['system_prompt'] == original


# ---------- 5. a per-type entry restores only that type ----------

def test_per_type_restore_restores_only_that_type():
    from prompt_blocks import shipped_default
    cm = fresh_config()
    cm.update_system_prompt('Storefront A.', 'a@yotpo.com', 'storefront')    # entry 0
    cm.update_system_prompt('Storefront B.', 'a@yotpo.com', 'storefront')    # entry 1
    cm.update_system_prompt('Data A.', 'a@yotpo.com', 'data')                # entry 2
    cm.update_system_prompt('Messaging M2.', 'a@yotpo.com')                  # entry 3
    cm.update_model_config('claude', 'claude-x', 'a@yotpo.com')              # entry 4

    cm.restore_from_backup(1, 'a@yotpo.com')            # undo "Storefront B"
    config = cm.get_config()
    assert config['system_prompts'] == {'storefront': 'Storefront A.', 'data': 'Data A.'}
    assert config['system_prompt'] == 'Messaging M2.'
    assert config['ai_model']['provider'] == 'claude'   # untouched: the entry didn't change it
    assert cm.get_audit_log()[-1]['platform_type'] == 'storefront'

    cm.restore_from_backup(0, 'a@yotpo.com')            # undo "Storefront A": nothing was stored
    assert 'storefront' not in cm.get_config()['system_prompts']
    assert cm.get_system_prompt('storefront') == shipped_default('storefront')
    assert cm.get_config()['system_prompts'] == {'data': 'Data A.'}

    cm.restore_from_backup(3, 'a@yotpo.com')            # undo "Messaging M2"
    config = cm.get_config()
    assert config['system_prompt'] == todays_template()
    assert config['ai_model']['provider'] == 'claude'
    assert config['system_prompts'] == {'data': 'Data A.'}

    # A broken backup is refused, as for messaging
    cm._add_audit_entry({'timestamp': 't', 'user_email': 'x', 'description': 'x',
                         'platform_type': 'content', 'changes': {},
                         'backup': {'system_prompts': {'content': '[[if loyalty]] never closed'}}})
    raises(ValueError, lambda: cm.restore_from_backup(-1, 'a@yotpo.com'))
    assert 'content' not in cm.get_config()['system_prompts']


def test_production_shaped_config():
    """A config stored before C1.7: no system_prompts, untyped audit entries.
    Reading writes nothing; a key update, a save and both kinds of undo keep
    every prompt."""
    from prompt_blocks import shipped_default
    cm = fresh_config()
    stored = cm.get_config()
    del stored['system_prompts']
    raw = json.dumps(stored)
    cm._db_set(cm.CONFIG_KEY, raw)
    cm._add_audit_entry({'timestamp': '2026-09-01T10:00:00', 'user_email': 'old@yotpo.com',
                         'description': 'Updated system prompt',
                         'backup': {'ai_model': stored['ai_model'], 'system_prompt': 'Old [[product]].'},
                         'changes': {'system_prompt': stored['system_prompt']}})
    assert cm.get_system_prompt('content') == shipped_default('content')
    cm.get_all_system_prompts()
    assert cm._db_get(cm.CONFIG_KEY) == raw                      # nothing written on read
    cm._update_env_file = lambda key, value: None                 # no .env writes in a test
    real = os.environ.get('GEMINI_API_KEY')
    try:
        cm.update_api_key('gemini', 'test-key-not-real', 'a@yotpo.com')
    finally:
        if real is None:
            os.environ.pop('GEMINI_API_KEY', None)
        else:
            os.environ['GEMINI_API_KEY'] = real
    assert cm.get_config()['system_prompts'] == {}
    cm.update_system_prompt('Content v1.', 'a@yotpo.com', 'content')
    cm.restore_from_backup(0, 'a@yotpo.com')                    # the old untyped entry
    assert cm.get_config()['system_prompt'] == 'Old [[product]].'
    assert cm.get_config()['system_prompts'] == {'content': 'Content v1.'}
    log = cm.get_audit_log()
    cm.restore_from_backup(next(i for i, e in enumerate(log) if e.get('platform_type') == 'content'),
                           'a@yotpo.com')
    assert cm.get_config()['system_prompts'] == {}
    assert cm.get_config()['system_prompt'] == 'Old [[product]].'


# ---------- 6. build_rag_context's defaults are unchanged (I3) ----------

def _chunk(esp, filename, index, total, words, url=None):
    meta = {'esp': esp, 'filename': filename, 'chunk_index': index, 'total_chunks': total,
            'source_url': url or f'https://help.{esp}.test/{filename}', 'product': 'loyalty'}
    text = f"{filename} part {index}: " + ' '.join(f"w{n}" for n in range(words))
    return f"{esp}_{filename}_{index}", text, meta


class FakeRagVectors:
    """Deterministic search results: Query B (mechanics) and Query A get
    different chunks, one of them in both; one task chunk is short, so its
    neighbour is appended. 'global' answers unless the query is nonsense;
    'empty' has nothing."""

    def __init__(self):
        rich = [_chunk('rich', 'triggers', 0, 2, 80), _chunk('rich', 'delays', 0, 1, 90)]
        task = [_chunk('rich', 'delays', 0, 1, 90), _chunk('rich', 'heading', 0, 2, 12),
                _chunk('rich', 'props', 0, 1, 70),
                _chunk('rich', 'guide', 0, 1, 75, url='https://support.yotpo.com/docs/rich'),
                _chunk('rich', 'pasted', 0, 1, 65, url='local://rich/notes')]
        self.chunks = {
            ('rich', 'mechanics'): rich,
            ('rich', 'task'): task,
            ('thin', 'task'): [_chunk('thin', 'only', 0, 1, 70)],
            ('global', 'task'): [_chunk('global', 'program', 0, 1, 66)],
        }
        self.neighbours = {cid: {'document': text} for cid, text, _ in
                           (_chunk('rich', 'heading', 1, 2, 40), _chunk('rich', 'triggers', 1, 2, 40))}

    def search(self, query, esp_filter=None, n_results=5, products=None):
        from rag_context import MECHANICS_QUERY
        kind = 'mechanics' if query == MECHANICS_QUERY else 'task'
        found = [] if 'zzqx' in query else self.chunks.get((esp_filter, kind), [])
        found = found[:n_results]
        return {'ids': [[c[0] for c in found]], 'documents': [[c[1] for c in found]],
                'metadatas': [[dict(c[2]) for c in found]]}

    def get_chunks(self, ids):
        return {i: self.neighbours[i] for i in ids if i in self.neighbours}


HISTORY = [{'role': 'user', 'content': 'How do I set it up?'},
           {'role': 'assistant', 'content': 'Open the integrations page first.'}]

RAG_CASES = [
    # (esp, message, history, keyword arguments other than the new ones)
    ('rich', 'How do I send a reminder?', [], {}),
    ('rich', 'Which properties are there?', HISTORY, {}),
    ('thin', 'Where do I start?', [], {}),
    ('empty', 'Anything?', [], {}),
    ('empty', 'zzqx', [], {}),
    ('rich', 'Reviews in an email?', [], {'product': 'reviews', 'reviews_coverage': False,
                                          'esp_display': 'Rich Mail'}),
    ('thin', 'Reviews?', [], {'product': None, 'reviews_coverage': False}),
]


def rag_contexts(**extra):
    import mechanics_cache
    from rag_context import build_rag_context
    out = []
    for esp, message, history, kwargs in RAG_CASES:
        mechanics_cache.clear_mechanics_cache()
        rag = build_rag_context(FakeRagVectors(), message, esp, list(history), **kwargs, **extra)
        out.append({'context': rag.context, 'metadatas': rag.metadatas})
    return out


def test_rag_context_defaults_unchanged():
    """Against contexts captured from the code before C1.7 (--write-rag-fixture
    on origin/main at 7b81ac8)."""
    with open(RAG_FIXTURE, encoding='utf-8') as f:
        golden = json.load(f)
    now = rag_contexts()
    assert len(golden) == len(now) == len(RAG_CASES)
    for case, g, n in zip(RAG_CASES, golden, now):
        assert g == n, f"context changed for {case[:2]}"
    # ...and passing the new arguments at their defaults changes nothing
    assert rag_contexts(integration_facts=None, source_style='esp', platform_type=None) == now
    # The cases cover what they should
    assert 'Platform Mechanics' in now[0]['context'] and 'w39' in now[0]['context']
    assert 'No specific documentation found' in now[4]['context']
    assert 'Limited documentation' in now[2]['context']


# ---------- 7. the facts block and the integration style ----------

def test_facts_block_only_when_passed():
    facts = "## Integration\nName: Rich\n\n"
    plain = rag_contexts()
    with_facts = rag_contexts(integration_facts=facts)
    for p, w in zip(plain, with_facts):
        assert facts not in p['context'] and '## Integration\n' not in p['context']
        assert w['context'] == facts + p['context']           # first, and nothing else changes
        assert w['metadatas'] == p['metadatas']


def test_integration_style_headers_and_notes():
    import mechanics_cache
    from rag_context import LIMITED_DOCS_BY_TYPE, build_rag_context
    def ctx(esp, message, **kw):
        mechanics_cache.clear_mechanics_cache()
        return build_rag_context(FakeRagVectors(), message, esp, [], source_style='integration',
                                 esp_display='Rich POS', **kw).context
    rich = ctx('rich', 'How do I redeem?', platform_type='storefront')
    assert 'ESP:' not in rich and 'ESP-Specific' not in rich
    # 2 mechanics chunks + 4 task chunks (the 5th is a mechanics chunk, shown once)
    assert rich.count('Integration: Rich POS\n') == 6
    assert 'Source: Yotpo guide\nURL: https://support.yotpo.com/docs/rich' in rich
    assert 'Source: text pasted by a Yotpo admin\nURL: local://rich/notes' in rich
    assert rich.count('Source: partner documentation\n') == 4
    assert '## Integration Documentation:' in rich
    assert 'Type: Global Knowledge Base' in rich                      # global sources keep theirs
    assert 'best practices' not in ctx('empty', 'zzqx', platform_type='storefront')
    assert "point the user to Rich POS's Yotpo guide" in ctx('empty', 'zzqx', platform_type='data')
    for t in OTHER_TYPES:
        thin = ctx('thin', 'Where do I start?', platform_type=t)
        assert LIMITED_DOCS_BY_TYPE[t].format(name='Rich POS') in thin, t
        assert 'Limited documentation found for this specific query' not in thin, t
    raises(ValueError, lambda: build_rag_context(FakeRagVectors(), 'x', 'rich', [], source_style='nope'))


def test_source_kind():
    from integration_facts import source_kind
    assert source_kind('https://support.yotpo.com/docs/x') == 'yotpo_support'
    assert source_kind('https://develop.yotpo.com/reference') == 'yotpo_developer'
    assert source_kind('https://help.gorgias.com/yotpo') == 'partner'
    assert source_kind('https://notyotpo.com/x') == 'partner'
    assert source_kind('local://gorgias/notes') == 'pasted'
    assert source_kind('https://help.gorgias.com/x', 'yotpo_support') == 'yotpo_support'
    assert source_kind(None) == 'partner'


GUIDE_TEXT = ("Products\n\nReviews\n\nLoyalty & Referrals\n\n####### Supported plans\n\n"
              "Premium, Enterprise\n\n####### eCommerce Platform\n\nShopify, Shopify Plus\n\n"
              "Change this text for SMS & Email\n\nThe guide's body.")


def test_facts_block():
    from integration_facts import facts_block
    row = {'name': 'gorgias', 'display_name': 'Gorgias', 'platform_type': 'service',
           'categories': ['help-desk-crm'], 'products': ['reviews']}
    docs = [
        {'url': 'https://support.yotpo.com/docs/gorgias', 'product': 'loyalty',
         'content_head': GUIDE_TEXT, 'crawl_status': 'completed', 'vector_count': 4},
        {'url': 'https://docs.gorgias.com/a', 'product': 'shared', 'crawl_status': 'completed',
         'vector_count': None},
        {'url': 'https://docs.gorgias.com/b', 'product': 'shared', 'crawl_status': 'completed',
         'vector_count': 2},
        # not counted: failed, indexed to nothing, retired
        {'url': 'https://docs.gorgias.com/c', 'product': 'shared', 'crawl_status': 'failed'},
        {'url': 'https://docs.gorgias.com/d', 'product': 'shared', 'crawl_status': 'completed',
         'vector_count': 0},
        {'url': 'https://support.yotpo.com/docs/old', 'product': 'loyalty', 'crawl_status': 'completed',
         'vector_count': 3, 'retired_at': '2026-10-01', 'supported_plans': ['Free']},
    ]
    assert facts_block(row, docs) == (
        "## Integration\n"
        "Name: Gorgias\n"
        "Type: Help Desk & CRM (platform type: service)\n"
        "Works with: Yotpo Loyalty & Referrals, Yotpo Reviews\n"
        "Yotpo plans: Premium, Enterprise\n"
        "Store platforms: Shopify, Shopify Plus\n"
        "Documentation: 1 Yotpo guide, 2 partner articles\n"
        "Yotpo guide: https://support.yotpo.com/docs/gorgias\n\n")
    # Stored header fields win over the text; lines with no data are left out
    docs[0].update(supported_plans=['Enterprise'], supported_platforms=['BigCommerce'])
    block = facts_block(row, docs)
    assert 'Yotpo plans: Enterprise\n' in block and 'Store platforms: BigCommerce\n' in block
    bare = facts_block({'name': 'x_pos', 'platform_type': 'storefront'}, [])
    assert bare == "## Integration\nName: x_pos\nType: Store & checkout (platform type: storefront)\n\n"


# ---------- routes and chat ----------

_app = None


class FakeIndex(FakeRagVectors):
    def url_exists(self, url, esp):
        return False


def app_client():
    """app.py on a fake vector store and a fresh stored config."""
    global _app
    if _app is None:
        os.chdir(HERE)
        import auth
        auth.current_user_is_admin = lambda: True
        auth.current_user = lambda: {'email': 'leo@yotpo.com'}
        from adapters.vector import vector_manager
        vector_manager.get_vector_adapter = lambda *a, **kw: FakeIndex()
        import app as app_module
        assert isinstance(app_module.vectorizer, FakeIndex)
        _app = app_module
    _app.config_manager = fresh_config()
    model = _app.config_manager.get_model_config()
    _app.ai_client = _app.build_ai_client(model['provider'], model['model_name'])
    return _app.app.test_client()


def integration(name, status, ptype, display=None, categories=(), products=()):
    from adapters.database.db_manager import get_database_adapter
    db = get_database_adapter()
    db.execute_query("DELETE FROM esps WHERE name = %s", (name,))
    esp_id = str(uuid.uuid4())
    db.execute_query(
        "INSERT INTO esps (id, name, display_name, status, platform_type, categories, products) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (esp_id, name, display or name.title(), status, ptype, json.dumps(list(categories)),
         json.dumps(list(products))))
    from esp_manager import get_esp_manager
    get_esp_manager()._active_names = None
    return esp_id


def test_prompt_routes():
    from prompt_blocks import COMMON_RULES, shipped_default
    c = app_client()
    r = c.get('/api/admin/settings/system-prompt')
    body = r.get_json()
    assert r.status_code == 200 and body['platform_type'] == 'messaging' and body['stored'] is True
    assert body['system_prompt'] == todays_template() and body['warnings'] == []
    assert [t['value'] for t in body['types']] == ['messaging', *OTHER_TYPES]
    body = c.get('/api/admin/settings/system-prompt?platform_type=storefront').get_json()
    assert body['system_prompt'] == shipped_default('storefront') and body['stored'] is False
    assert body['warnings'] == []                    # no storefront integration is in chat
    assert c.get('/api/admin/settings/system-prompt?platform_type=pos').status_code == 400

    # Saving without the common rules saves, with a warning
    r = c.post('/api/admin/settings/system-prompt?platform_type=storefront',
               json={'system_prompt': 'Short [[product]] prompt.', 'user_email': 'leo@yotpo.com'})
    body = r.get_json()
    assert r.status_code == 200 and body['platform_type'] == 'storefront'
    assert any('common rules' in w for w in body['warnings'])
    assert _app.ai_client.prompts['storefront'] == 'Short [[product]] prompt.'   # client reloaded
    assert _app.ai_client.prompts['messaging'] == todays_template()
    # The type can come in the body too; messaging is untouched by all this
    r = c.post('/api/admin/settings/system-prompt',
               json={'system_prompt': shipped_default('data') + ' Extra.', 'user_email': 'leo@yotpo.com',
                     'platform_type': 'data'})
    assert r.status_code == 200 and 'warnings' not in r.get_json()
    assert COMMON_RULES in _app.config_manager.get_system_prompt('data')
    assert _app.config_manager.get_system_prompt() == todays_template()
    r = c.post('/api/admin/settings/system-prompt?platform_type=content',
               json={'system_prompt': '[[if loyalty]]x', 'user_email': 'leo@yotpo.com'})
    assert r.status_code == 400 and 'placeholder' in r.get_json()['error']

    # An active type with nothing stored is pointed out
    integration('lightspeed_t', 'active', 'service')
    body = c.get('/api/admin/settings/system-prompt?platform_type=service').get_json()
    assert any('1 Customer service integration is in chat' in w for w in body['warnings'])

    # Undo the storefront save from the page: only storefront goes back
    log = c.get('/api/admin/settings/audit-log').get_json()['audit_log']
    index = next(i for i, e in enumerate(log) if e.get('platform_type') == 'storefront')
    r = c.post('/api/admin/settings/restore', json={'audit_index': index, 'user_email': 'leo@yotpo.com'})
    assert r.status_code == 200 and r.get_json()['platform_type'] == 'storefront'
    assert _app.ai_client.prompts['storefront'] == shipped_default('storefront')
    assert _app.config_manager.get_system_prompt('data') == shipped_default('data') + ' Extra.'


def test_undo_index_is_a_whole_log_position():
    c = app_client()
    for n in range(25):
        _app.config_manager.update_system_prompt(f'Data v{n}.', 'leo@yotpo.com', 'data')
    body = c.get('/api/admin/settings/audit-log?limit=20').get_json()
    assert body['total'] == 25 and body['offset'] == 5 and len(body['audit_log']) == 20
    # The page's newest row: offset + its position in the page
    newest = body['offset'] + len(body['audit_log']) - 1
    r = c.post('/api/admin/settings/restore', json={'audit_index': newest, 'user_email': 'leo@yotpo.com'})
    assert r.status_code == 200
    assert _app.config_manager.get_system_prompt('data') == 'Data v23.'


def test_settings_routes_are_owner_only():
    c = app_client()
    os.environ['ADMIN_OWNER_EMAILS'] = 'someone.else@yotpo.com'   # the test user is an editor
    try:
        assert c.post('/api/admin/settings/prompt-preview', json={'esp': 'x'}).status_code == 403
        assert c.get('/api/admin/settings/system-prompt?platform_type=data').status_code == 403
        r = c.post('/api/admin/settings/system-prompt',
                   json={'system_prompt': 'x', 'user_email': 'a@yotpo.com', 'platform_type': 'data'})
        assert r.status_code == 403
    finally:
        os.environ.pop('ADMIN_OWNER_EMAILS', None)


def test_prompt_preview_for_a_listed_storefront_integration():
    from prompt_blocks import shipped_default
    from prompt_template import render
    c = app_client()
    esp_id = integration('tapcart_t', 'listed', 'storefront', display='Tapcart',
                         categories=['mobile-app-builder'], products=['loyalty'])
    from adapters.database.db_manager import get_database_adapter
    get_database_adapter().execute_query(
        "INSERT INTO esp_documents (id, esp_id, url, filename, crawl_status, product, vector_count, content) "
        "VALUES (%s, %s, %s, %s, 'completed', 'loyalty', 3, %s)",
        (str(uuid.uuid4()), esp_id, 'https://support.yotpo.com/docs/tapcart', 'tapcart', GUIDE_TEXT))
    r = c.post('/api/admin/settings/prompt-preview', json={'esp': 'tapcart_t', 'product': 'reviews'})
    body = r.get_json()
    assert r.status_code == 200, body
    assert body['platform_type'] == 'storefront' and body['status'] == 'listed'
    assert body['system_prompt'] == render(shipped_default('storefront'), 'reviews')
    assert body['facts_block'].startswith('## Integration\nName: Tapcart\nType: Mobile App Builder')
    assert 'Yotpo plans: Premium, Enterprise' in body['facts_block']

    body = c.post('/api/admin/settings/prompt-preview', json={'esp': 'klaviyo_t'}).get_json()
    assert body['error'] == 'No such integration'
    integration('klaviyo_t', 'active', 'messaging', display='Klaviyo')
    body = c.post('/api/admin/settings/prompt-preview', json={'esp': 'klaviyo_t'}).get_json()
    assert body['platform_type'] == 'messaging' and body['facts_block'] is None
    assert body['product'] == 'loyalty' and body['system_prompt'] == render(todays_template(), 'loyalty')
    integration('untyped_t', 'listed', None)
    r = c.post('/api/admin/settings/prompt-preview', json={'esp': 'untyped_t'})
    assert r.status_code == 400 and 'category' in r.get_json()['error']


def test_chat_picks_the_prompt_by_type():
    import integration_facts
    c = app_client()
    calls = []

    def stub(message, context, conversation_history=None, product=None, platform_type='messaging'):
        calls.append({'context': context, 'platform_type': platform_type, 'product': product})
        return 'answer'
    _app.ai_client.generate_response = stub

    integration('rich', 'active', 'messaging', display='Rich Mail')
    r = c.post('/api/chat', json={'message': 'How do I send a reminder?', 'esp': 'rich',
                                  'session_id': 's1', 'product': 'loyalty'})
    assert r.status_code == 200, r.get_json()
    assert calls[-1]['platform_type'] == 'messaging'
    assert not calls[-1]['context'].startswith('## Integration') and 'ESP: rich' in calls[-1]['context']
    # A key with stray spaces is the same integration for every check
    integration('rich', 'active', 'storefront', display='Rich POS', categories=['in-store-pos'])
    r = c.post('/api/chat', json={'message': 'Hi', 'esp': ' Rich ', 'session_id': 's1'})
    assert r.status_code == 200 and calls[-1]['platform_type'] == 'storefront'
    integration('rich', 'active', 'messaging', display='Rich Mail')

    # The same documents under an active storefront integration (C1.7 builds
    # the path; the admin still refuses to make one active until its wave)
    integration('rich', 'active', 'storefront', display='Rich POS', categories=['in-store-pos'])
    integration_facts._cache.clear()
    r = c.post('/api/chat', json={'message': 'How do I send a reminder?', 'esp': 'rich',
                                  'session_id': 's1', 'product': 'reviews'})
    assert r.status_code == 200, r.get_json()
    call = calls[-1]
    assert call['platform_type'] == 'storefront' and call['product'] == 'reviews'
    assert call['context'].startswith('## Integration\nName: Rich POS\nType: In-store & POS (platform type: storefront)\n')
    assert 'Integration: Rich POS' in call['context'] and 'ESP: rich' not in call['context']

    # A database failure falls back to messaging, as the key check does
    from esp_manager import get_esp_manager
    mgr = get_esp_manager()
    real = mgr.active_platform_type
    mgr.active_platform_type = lambda name: (_ for _ in ()).throw(RuntimeError('db down'))
    try:
        assert _app._chat_platform_type('rich') == 'messaging'
    finally:
        mgr.active_platform_type = real
    assert _app._chat_platform_type('rich') == 'storefront'
    assert _app._chat_platform_type('nope') == 'messaging'


def write_rag_fixture():
    os.makedirs(os.path.dirname(RAG_FIXTURE), exist_ok=True)
    with open(RAG_FIXTURE, 'w', encoding='utf-8') as f:
        json.dump(rag_contexts(), f, indent=1, ensure_ascii=False)
        f.write('\n')
    print(f"wrote {RAG_FIXTURE}")


if __name__ == '__main__':
    if sys.argv[1:] == ['--write-rag-fixture']:
        write_rag_fixture()
        shutil.rmtree(TMP, ignore_errors=True)
        sys.exit(0)
    tests = [v for k, v in dict(globals()).items() if k.startswith('test_')]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL {t.__name__}: {type(e).__name__} {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    shutil.rmtree(TMP, ignore_errors=True)
    sys.exit(1 if failed else 0)
