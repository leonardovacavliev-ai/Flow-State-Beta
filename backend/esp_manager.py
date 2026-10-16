"""
ESP Manager - Database-backed ESP management

Manages ESPs and their documentation URLs in PostgreSQL.
Replaces filesystem-based ESP storage (docs/ folders + CSV).
"""

import json
import time
import uuid
import hashlib
from typing import Iterable, List, Dict, Optional
from adapters.database.db_manager import get_database_adapter
from urls import normalize_url

# How long is_active_integration trusts its answer. Every chat request asks,
# so it is cached; a newly activated integration is accepted within a minute.
ACTIVE_CACHE_SECONDS = 60


def _json_list(value):
    """A JSON list column: JSONB arrives parsed from Postgres, TEXT from SQLite."""
    if value is None:
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return []
    return value if isinstance(value, list) else []


def _iso(value):
    """Format a timestamp column that may be a datetime (Postgres) or a
    string (SQLite)."""
    if value is None:
        return None
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)


def describe_owners(owners: List[Dict]) -> str:
    """'Klaviyo' / 'Klaviyo and Global Knowledge' / 'A, B and C' for a duplicate-URL message."""
    names = [o['display_name'] for o in owners]
    if len(names) <= 1:
        return ''.join(names)
    return ', '.join(names[:-1]) + ' and ' + names[-1]


class DuplicateURLError(ValueError):
    """The URL is already in the knowledge base. A ValueError so existing
    handlers still turn it into a 400; `owners` says where it lives."""

    def __init__(self, url: str, owners: List[Dict], esp_name: str = None):
        self.url = url
        self.owners = owners
        self.notice = f"This link already exists in {describe_owners(owners)}."
        super().__init__(
            f"{self.notice} It was not added: a link is only crawled once, "
            f"so the same page is never indexed twice."
        )


def require_platform_type(name: str, platform_type: Optional[str]) -> None:
    """Every integration is added with its category (Leo, 2026-10-16):
    the kind decides which system prompt answers for it, so one without a
    kind would be answered by a guess. Only the hidden 'global' row has
    none. Raises ValueError otherwise."""
    from integration_types import PLATFORM_TYPES, TYPE_LABELS
    if name == 'global':
        if platform_type is not None:
            raise ValueError("The global knowledge row has no category")
        return
    if platform_type not in PLATFORM_TYPES:
        kinds = ', '.join(f"{TYPE_LABELS[t]} ({t})" for t in PLATFORM_TYPES)
        if platform_type is None or platform_type == '':
            raise ValueError(f"Choose the category first. An integration can't be added "
                             f"without one: {kinds}")
        raise ValueError(f"Unknown category '{platform_type}': use one of {kinds}")


class ESPManager:
    """Manages ESPs and their documentation in the database."""

    def __init__(self):
        """Initialize with database adapter."""
        self.db = get_database_adapter()
        self._active_names = None
        self._active_loaded_at = 0.0

    # ==================== ESP Operations ====================

    def create_esp(self, name: str, display_name: str, description: str = "", *,
                   platform_type: Optional[str], status: str = 'active') -> Dict:
        """
        Create a new ESP.

        Args:
            name: URL-safe identifier (e.g., 'klaviyo', 'mailchimp')
            display_name: Human-readable name (e.g., 'Klaviyo', 'Mailchimp')
            description: Optional description
            platform_type: integration_types.PLATFORM_TYPES, required: no
                integration is added without its category (Leo,
                2026-10-16), since the kind decides which prompt answers
                for it. None only for the hidden 'global' row, which serves
                every type.
            status: 'active' (in chat) or 'listed' (not in chat yet)

        Returns:
            Dict with esp_id and details

        Raises:
            ValueError: If ESP with same name already exists, or the
                platform type is missing or unknown
        """
        # Normalize name (lowercase, replace spaces with underscores)
        name = name.lower().replace(' ', '_').replace('/', '_')
        require_platform_type(name, platform_type)
        if status not in ('active', 'listed'):
            raise ValueError(f"Unknown status '{status}'")

        # Check if exists — including archived rows, since the name column
        # is UNIQUE regardless of status and the INSERT would fail anyway
        existing = self.get_esp_by_name(name, include_archived=True)
        if existing:
            if existing.get('status') == 'listed':
                raise ValueError(f"'{name}' already exists as a listed integration: open it in "
                                 f"the Integrations list")
            if existing.get('status') != 'active':
                raise ValueError(f"ESP '{name}' already exists but is archived — restore it instead")
            raise ValueError(f"ESP '{name}' already exists")

        query = """
            INSERT INTO esps (id, name, display_name, description, status, platform_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, name, display_name, description, status, created_at
        """
        esp_id = str(uuid.uuid4())
        params = (esp_id, name, display_name, description, status, platform_type)

        result = self.db.execute_query(query, params, fetch=True)
        if result:
            row = result[0]
            return {
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'description': row[3],
                'status': row[4],
                'created_at': _iso(row[5])
            }
        return None

    def get_esp_by_name(self, name: str, include_archived: bool = False) -> Optional[Dict]:
        """
        Get ESP by name: an `active` or `listed` integration.

        Listed rows are found because an admin documents an integration
        before it goes into chat: proposals are approved, labelled and
        crawled while it is listed (C1.4, C1.9). This is a lookup by name,
        used by admin and document paths only. Chat checks
        is_active_integration and older code lists through list_esps, both
        `active` only (I4).

        include_archived matters when the row must be found even if soft
        deleted: esps.name is UNIQUE regardless of status, so code that does
        "look up, create if missing" would hit a duplicate-key error on an
        archived row it couldn't see.
        """
        query = """
            SELECT id, name, display_name, description, status, created_at, updated_at
            FROM esps
            WHERE name = %s AND (status IN ('active', 'listed') OR %s = true)
        """
        result = self.db.execute_query(query, (name, include_archived), fetch=True)
        if result:
            row = result[0]
            return {
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'description': row[3],
                'status': row[4],
                'created_at': _iso(row[5]),
                'updated_at': _iso(row[6])
            }
        return None

    def get_esp_by_id(self, esp_id: str) -> Optional[Dict]:
        """Get ESP by UUID."""
        query = """
            SELECT id, name, display_name, description, status, created_at, updated_at
            FROM esps
            WHERE id = %s
        """
        result = self.db.execute_query(query, (esp_id,), fetch=True)
        if result:
            row = result[0]
            return {
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'description': row[3],
                'status': row[4],
                'created_at': _iso(row[5]),
                'updated_at': _iso(row[6])
            }
        return None

    def list_esps(self, include_archived: bool = False) -> List[Dict]:
        """
        List all ESPs.

        Args:
            include_archived: Include archived ESPs

        Returns:
            List of ESP dictionaries with document counts
        """
        query = """
            SELECT
                e.id, e.name, e.display_name, e.description, e.status,
                e.created_at, e.updated_at,
                COUNT(d.id) as doc_count
            FROM esps e
            LEFT JOIN esp_documents d ON e.id = d.esp_id AND d.retired_at IS NULL
            WHERE e.status = 'active' OR %s = true
            GROUP BY e.id, e.name, e.display_name, e.description, e.status,
                     e.created_at, e.updated_at
            ORDER BY e.name
        """
        results = self.db.execute_query(query, (include_archived,), fetch=True)

        esps = []
        for row in results:
            esps.append({
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'description': row[3],
                'status': row[4],
                'created_at': _iso(row[5]),
                'updated_at': _iso(row[6]),
                'doc_count': row[7]
            })
        return esps

    def list_integrations(self, statuses: Iterable[str] = ('active',)) -> List[Dict]:
        """Integrations with the given statuses, with the v2 fields.

        list_esps stays as it was, listing `active` rows only, so callers
        that predate the `listed` status never see those rows (I4).
        """
        statuses = tuple(statuses)
        if not statuses:
            return []
        placeholders = ','.join(['%s'] * len(statuses))
        query = f"""
            SELECT
                e.id, e.name, e.display_name, e.description, e.status,
                e.platform_type, e.catalog_slugs, e.categories, e.products,
                e.catalog_description, COUNT(d.id) as doc_count
            FROM esps e
            LEFT JOIN esp_documents d ON e.id = d.esp_id AND d.retired_at IS NULL
            WHERE e.status IN ({placeholders})
            GROUP BY e.id, e.name, e.display_name, e.description, e.status,
                     e.platform_type, e.catalog_slugs, e.categories, e.products,
                     e.catalog_description
            ORDER BY e.name
        """
        rows = self.db.execute_query(query, statuses, fetch=True) or []
        return [{
            'id': row[0],
            'name': row[1],
            'display_name': row[2],
            'description': row[3],
            'status': row[4],
            'platform_type': row[5],
            'catalog_slugs': _json_list(row[6]),
            'categories': _json_list(row[7]),
            'products': _json_list(row[8]),
            'catalog_description': row[9],
            'doc_count': row[10],
        } for row in rows]

    def _active(self) -> Dict[str, Optional[str]]:
        """Active integrations' keys -> platform_type.

        Cached for ACTIVE_CACHE_SECONDS: chat asks on every message. Setting
        _active_names to None makes the next call reload.
        """
        now = time.monotonic()
        # One read of the attribute: an admin PATCH may set it to None from
        # another thread at any moment
        active = self._active_names
        if active is None or now - self._active_loaded_at > ACTIVE_CACHE_SECONDS:
            rows = self.db.execute_query(
                "SELECT name, platform_type FROM esps WHERE status = 'active'", fetch=True) or []
            active = {row[0]: row[1] for row in rows}
            self._active_names = active
            self._active_loaded_at = now
        return active

    def is_active_integration(self, name: str) -> bool:
        """True when `name` is the key of an active integration."""
        return name in self._active()

    def active_platform_type(self, name: str) -> Optional[str]:
        """The platform type of an active integration; None when it is not
        active or has no type (the hidden 'global' row)."""
        return self._active().get(name)

    def update_esp(self, esp_id: str, display_name: str = None,
                   description: str = None) -> bool:
        """Update ESP details."""
        updates = []
        params = []

        if display_name is not None:
            updates.append("display_name = %s")
            params.append(display_name)

        if description is not None:
            updates.append("description = %s")
            params.append(description)

        if not updates:
            return True  # Nothing to update

        params.append(esp_id)
        query = f"""
            UPDATE esps
            SET {', '.join(updates)}
            WHERE id = %s
        """
        self.db.execute_query(query, tuple(params))
        return True

    def archive_esp(self, esp_id: str) -> bool:
        """Archive an ESP (soft delete)."""
        query = "UPDATE esps SET status = 'archived' WHERE id = %s"
        self.db.execute_query(query, (esp_id,))
        return True

    def restore_esp(self, esp_id: str) -> bool:
        """Reactivate an archived ESP."""
        query = "UPDATE esps SET status = 'active' WHERE id = %s"
        self.db.execute_query(query, (esp_id,))
        return True

    # ==================== Document Operations ====================

    def add_document(self, esp_name: str, url: str, *, product: str, filename: str = None) -> Dict:
        """
        Add a document URL to an ESP.

        Args:
            esp_name: ESP name
            url: Document URL to crawl
            product: Yotpo product line, 'loyalty' | 'reviews' | 'shared'.
                Required and keyword-only: this is the one place rows are
                created, so every write path has to say which product a
                document covers. (Keyword-only so an old positional
                `filename` can't land here and pass the check.)
            filename: Optional saved filename

        Returns:
            Dict with document details

        Raises:
            ValueError: If ESP doesn't exist, the product is missing or
                unknown, or the URL already exists
        """
        from product_labels import require_product
        product = require_product(product)
        url = normalize_url(url)

        # Get ESP
        esp = self.get_esp_by_name(esp_name)
        if not esp:
            raise ValueError(f"ESP '{esp_name}' not found")

        # Refuse a URL that already exists anywhere (any ESP, or global
        # knowledge): a second copy would be crawled and indexed twice
        owners = self.find_documents_by_url(url)
        if owners:
            raise DuplicateURLError(url, owners, esp_name)

        # Generate filename if not provided
        if not filename:
            filename = url.split('/')[-1] or 'document'

        query = """
            INSERT INTO esp_documents (id, esp_id, url, filename, crawl_status, product)
            VALUES (%s, %s, %s, %s, 'pending', %s)
            RETURNING id, url, filename, crawl_status, created_at
        """
        doc_id = str(uuid.uuid4())
        params = (doc_id, esp['id'], url, filename, product)

        result = self.db.execute_query(query, params, fetch=True)
        if result:
            row = result[0]
            return {
                'id': row[0],
                'esp_id': esp['id'],
                'esp_name': esp_name,
                'url': row[1],
                'filename': row[2],
                'crawl_status': row[3],
                'created_at': _iso(row[4]),
                'product': product
            }
        return None

    def find_documents_by_url(self, url: str) -> List[Dict]:
        """
        Every document whose URL is `url` once normalised (urls.py), across
        all ESPs including global knowledge, active or listed (a listed
        integration's documents are crawled before it goes into chat).

        Returns a list of {'esp_name', 'display_name', 'filename',
        'crawl_status'}; empty if the URL is new.
        """
        query = """
            SELECT e.name, e.display_name, d.filename, d.crawl_status
            FROM esp_documents d
            JOIN esps e ON e.id = d.esp_id
            WHERE d.url = %s AND e.status IN ('active', 'listed')
            ORDER BY e.name
        """
        rows = self.db.execute_query(query, (normalize_url(url),), fetch=True) or []
        return [{
            'esp_name': r[0],
            'display_name': r[1] or r[0],
            'filename': r[2],
            'crawl_status': r[3],
        } for r in rows]

    def get_document_by_url(self, esp_id: str, url: str) -> Optional[Dict]:
        """Get document by ESP ID and URL (normalised, see urls.py)."""
        query = """
            SELECT id, esp_id, url, filename, content_hash, crawl_status,
                   last_crawled_at, error_message, vector_ids, created_at, updated_at,
                   product
            FROM esp_documents
            WHERE esp_id = %s AND url = %s
        """
        result = self.db.execute_query(query, (esp_id, normalize_url(url)), fetch=True)
        if result:
            row = result[0]
            return {
                'id': row[0],
                'esp_id': row[1],
                'url': row[2],
                'filename': row[3],
                'content_hash': row[4],
                'crawl_status': row[5],
                'last_crawled_at': _iso(row[6]),
                'error_message': row[7],
                'vector_ids': row[8],
                'created_at': _iso(row[9]),
                'updated_at': _iso(row[10]),
                'product': row[11]
            }
        return None

    def list_documents(self, esp_name: str, include_retired: bool = False) -> List[Dict]:
        """List an ESP's documents; retired ones (C1.3) only when asked.
        Refresh All and the global knowledge list read this."""
        esp = self.get_esp_by_name(esp_name)
        if not esp:
            return []

        # has_content: boolean expression instead of selecting the (large)
        # content column itself; works in both SQLite (0/1) and Postgres
        query = """
            SELECT id, url, filename, content_hash, crawl_status,
                   last_crawled_at, error_message, created_at, updated_at,
                   content IS NOT NULL AS has_content
            FROM esp_documents
            WHERE esp_id = %s AND (retired_at IS NULL OR %s = true)
            ORDER BY created_at DESC
        """
        results = self.db.execute_query(query, (esp['id'], include_retired), fetch=True)

        docs = []
        for row in results:
            docs.append({
                'id': row[0],
                'url': row[1],
                'filename': row[2],
                'content_hash': row[3],
                'crawl_status': row[4],
                'last_crawled_at': _iso(row[5]),
                'error_message': row[6],
                'created_at': _iso(row[7]),
                'updated_at': _iso(row[8]),
                'has_content': bool(row[9])
            })
        return docs

    # ==================== Product labels ====================

    def get_product_labels(self, esp_name: str) -> Dict[str, Dict]:
        """{url: {'product', 'suggested_product'}} for every document of an ESP.

        suggested_product comes from the Yotpo header in the stored content,
        read from its first few hundred characters only.
        """
        from product_labels import header_label, HEADER_SCAN_CHARS

        esp = self.get_esp_by_name(esp_name)
        if not esp:
            return {}
        # substr() works in both SQLite and Postgres
        query = f"""
            SELECT url, product, substr(content, 1, {HEADER_SCAN_CHARS})
            FROM esp_documents
            WHERE esp_id = %s
        """
        rows = self.db.execute_query(query, (esp['id'],), fetch=True) or []
        return {row[0]: {'product': row[1], 'suggested_product': header_label(row[2])}
                for row in rows}

    def set_document_product(self, esp_name: str, urls: List[str], product: Optional[str]):
        """Set the product label on an ESP's documents (the route refuses None:
        every document needs one, and its vectors carry it).

        Returns (updated_urls, missing_urls). Missing means no row for that
        URL under this ESP; nothing is created.
        """
        esp = self.get_esp_by_name(esp_name)
        if not esp:
            raise ValueError(f"ESP '{esp_name}' not found")

        placeholders = ','.join(['%s'] * len(urls))
        existing = self.db.execute_query(
            f"SELECT url FROM esp_documents WHERE esp_id = %s AND url IN ({placeholders})",
            (esp['id'],) + tuple(urls), fetch=True) or []
        found = [row[0] for row in existing]
        if found:
            found_placeholders = ','.join(['%s'] * len(found))
            self.db.execute_query(
                f"UPDATE esp_documents SET product = %s "
                f"WHERE esp_id = %s AND url IN ({found_placeholders})",
                (product, esp['id']) + tuple(found))
        found_set = set(found)
        return found, [u for u in urls if u not in found_set]

    def get_document_product(self, esp_name: str, url: str) -> Optional[str]:
        """The product label of one document, or None (no row, or unlabelled).

        Looked up by (esp, url), the key esp_documents enforces and vectors
        carry -- not by filename, which a rebuild can rewrite.
        """
        rows = self.db.execute_query("""
            SELECT d.product
            FROM esp_documents d
            JOIN esps e ON e.id = d.esp_id
            WHERE e.name = %s AND d.url = %s
        """, (esp_name.lower(), url), fetch=True) or []
        return rows[0][0] if rows else None

    def set_vector_count(self, esp_name: str, url: str, count: int) -> None:
        """Record how many chunks the last index of a document wrote."""
        self.db.execute_query("""
            UPDATE esp_documents SET vector_count = %s
            WHERE url = %s AND esp_id IN (SELECT id FROM esps WHERE name = %s)
        """, (count, url, esp_name.lower()))

    def reviews_documents(self) -> List[tuple]:
        """(esp, url) of every Reviews-labelled document.

        Deliberately no crawl_status or content condition: a failed re-crawl
        marks a row failed but keeps its previous vectors, and a row can say
        completed with nothing indexed. product_labels asks the index.
        """
        rows = self.db.execute_query("""
            SELECT e.name, d.url
            FROM esp_documents d
            JOIN esps e ON e.id = d.esp_id
            WHERE d.product = 'reviews' AND d.retired_at IS NULL
        """, fetch=True) or []
        return [(r[0], r[1]) for r in rows]

    def list_all_product_labels(self) -> List[Dict]:
        """Every document with its ESP, URL, label and whether it has content."""
        rows = self.db.execute_query("""
            SELECT e.name, d.url, d.filename, d.product, d.content IS NOT NULL
            FROM esp_documents d
            JOIN esps e ON e.id = d.esp_id
            ORDER BY e.name, d.url
        """, fetch=True) or []
        return [{'esp': r[0], 'url': r[1], 'filename': r[2], 'product': r[3],
                 'has_content': bool(r[4])} for r in rows]

    def update_document_crawl_status(self, doc_id: str, status: str,
                                      content_hash: str = None,
                                      error_message: str = None,
                                      vector_ids: List[str] = None,
                                      content: str = None,
                                      filename: str = None) -> bool:
        """
        Update document after crawl attempt.

        Args:
            doc_id: Document UUID
            status: 'completed' or 'failed'
            content_hash: SHA-256 hash of content (if successful)
            error_message: Error message (if failed)
            vector_ids: List of vector DB chunk IDs (if successful)
            content: Crawled/pasted text — stored so the knowledge base can be
                rebuilt after the ephemeral container filesystem is wiped
            filename: Saved filename (keeps the DB record accurate)
        """
        # Only overwrite columns that were actually provided — a failed
        # re-crawl must not NULL out the previously good content_hash or
        # vector_ids (they're needed for change detection and cleanup).
        import json
        sets = ["crawl_status = %s", "last_crawled_at = CURRENT_TIMESTAMP"]
        params = [status]

        if content_hash is not None:
            sets.append("content_hash = %s")
            params.append(content_hash)

        if error_message is not None:
            sets.append("error_message = %s")
            params.append(error_message)
        elif status == 'completed':
            sets.append("error_message = NULL")

        if vector_ids is not None:
            sets.append("vector_ids = %s")
            params.append(json.dumps(vector_ids))

        if content is not None:
            sets.append("content = %s")
            params.append(content)

        if filename is not None:
            sets.append("filename = %s")
            params.append(filename)

        params.append(doc_id)
        query = f"""
            UPDATE esp_documents
            SET {', '.join(sets)}
            WHERE id = %s
        """
        self.db.execute_query(query, tuple(params))
        return True

    def get_documents_with_content(self, esp_name: str) -> List[Dict]:
        """
        List an ESP's documents including their stored content.

        Used to rebuild files/vectors after a redeploy wipes the container
        filesystem. Retired documents are left out: their vectors were
        deleted on purpose.
        """
        esp = self.get_esp_by_name(esp_name)
        if not esp:
            return []

        query = """
            SELECT id, url, filename, content, content_hash, crawl_status, product
            FROM esp_documents
            WHERE esp_id = %s AND retired_at IS NULL
            ORDER BY created_at ASC
        """
        results = self.db.execute_query(query, (esp['id'],), fetch=True)

        return [{
            'id': row[0],
            'url': row[1],
            'filename': row[2],
            'content': row[3],
            'content_hash': row[4],
            'crawl_status': row[5],
            'product': row[6]
        } for row in results]

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document."""
        query = "DELETE FROM esp_documents WHERE id = %s"
        self.db.execute_query(query, (doc_id,))
        return True

    def delete_documents_by_urls(self, esp_name: str, urls: List[str]) -> int:
        """
        Delete multiple documents by URLs.

        Returns:
            Number of documents deleted
        """
        esp = self.get_esp_by_name(esp_name)
        if not esp:
            return 0

        if not urls:
            return 0

        # Use IN clause for batch delete
        placeholders = ','.join(['%s'] * len(urls))
        query = f"""
            DELETE FROM esp_documents
            WHERE esp_id = %s AND url IN ({placeholders})
        """
        params = (esp['id'],) + tuple(urls)
        self.db.execute_query(query, params)
        return len(urls)

    # ==================== Utility Methods ====================

    def get_esp_stats(self, esp_name: str) -> Dict:
        """Get statistics for an ESP."""
        esp = self.get_esp_by_name(esp_name)
        if not esp:
            return None

        query = """
            SELECT
                COUNT(*) as total_docs,
                SUM(CASE WHEN crawl_status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN crawl_status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN crawl_status = 'failed' THEN 1 ELSE 0 END) as failed,
                MAX(last_crawled_at) as last_crawl
            FROM esp_documents
            WHERE esp_id = %s AND retired_at IS NULL
        """
        result = self.db.execute_query(query, (esp['id'],), fetch=True)
        if result:
            row = result[0]
            return {
                'esp_name': esp_name,
                'total_docs': row[0],
                'completed': row[1],
                'pending': row[2],
                'failed': row[3],
                'last_crawl': _iso(row[4])
            }
        return None

    @staticmethod
    def calculate_content_hash(content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


# Singleton instance
_esp_manager = None

def get_esp_manager() -> ESPManager:
    """Get ESP manager singleton instance."""
    global _esp_manager
    if _esp_manager is None:
        _esp_manager = ESPManager()
    return _esp_manager
