"""
One-time data seeds run from both adapters' initialize().

SQL here is the subset Postgres and SQLite share, with no parameters, so the
same function serves both cursors.
"""

PLATFORM_TYPE_SEED_KEY = 'seed:platform_type_messaging'


def seed_platform_types(cursor):
    """Give every integration that existed before platform types the type
    `messaging`: until v2 every one of them was an email/SMS platform on the
    email prompt, Other/Webhook included (it moves to `data` in C2.4).
    `global` is knowledge for every integration and keeps NULL.

    Runs once, recorded in app_settings, not on every boot: catalog rows
    imported later may have no type yet and must not become messaging.
    ON CONFLICT covers two replicas booting at the same time.
    """
    cursor.execute(f"SELECT 1 FROM app_settings WHERE key = '{PLATFORM_TYPE_SEED_KEY}'")
    if cursor.fetchone():
        return
    cursor.execute("""
        UPDATE esps SET platform_type = 'messaging'
        WHERE platform_type IS NULL AND name <> 'global'
    """)
    cursor.execute(f"""
        INSERT INTO app_settings (key, value) VALUES ('{PLATFORM_TYPE_SEED_KEY}', 'done')
        ON CONFLICT (key) DO NOTHING
    """)
