"""
ESP Manager - Database-backed ESP management

Manages ESPs and their documentation URLs in PostgreSQL.
Replaces filesystem-based ESP storage (docs/ folders + CSV).
"""

import uuid
import hashlib
from typing import List, Dict, Optional
from adapters.database.db_manager import get_database_adapter


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


class ESPManager:
    """Manages ESPs and their documentation in the database."""

    def __init__(self):
        """Initialize with database adapter."""
        self.db = get_database_adapter()

    # ==================== ESP Operations ====================

    def create_esp(self, name: str, display_name: str, description: str = "") -> Dict:
        """
        Create a new ESP.

        Args:
            name: URL-safe identifier (e.g., 'klaviyo', 'mailchimp')
            display_name: Human-readable name (e.g., 'Klaviyo', 'Mailchimp')
            description: Optional description

        Returns:
            Dict with esp_id and details

        Raises:
            ValueError: If ESP with same name already exists
        """
        # Normalize name (lowercase, replace spaces with underscores)
        name = name.lower().replace(' ', '_').replace('/', '_')

        # Check if exists — including archived rows, since the name column
        # is UNIQUE regardless of status and the INSERT would fail anyway
        existing = self.get_esp_by_name(name, include_archived=True)
        if existing:
            if existing.get('status') != 'active':
                raise ValueError(f"ESP '{name}' already exists but is archived — restore it instead")
            raise ValueError(f"ESP '{name}' already exists")

        query = """
            INSERT INTO esps (id, name, display_name, description, status)
            VALUES (%s, %s, %s, %s, 'active')
            RETURNING id, name, display_name, description, status, created_at
        """
        esp_id = str(uuid.uuid4())
        params = (esp_id, name, display_name, description)

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
        Get ESP by name.

        include_archived matters when the row must be found even if soft
        deleted: esps.name is UNIQUE regardless of status, so code that does
        "look up, create if missing" would hit a duplicate-key error on an
        archived row it couldn't see.
        """
        query = """
            SELECT id, name, display_name, description, status, created_at, updated_at
            FROM esps
            WHERE name = %s AND (status = 'active' OR %s = true)
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
            LEFT JOIN esp_documents d ON e.id = d.esp_id
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

    def add_document(self, esp_name: str, url: str, filename: str = None) -> Dict:
        """
        Add a document URL to an ESP.

        Args:
            esp_name: ESP name
            url: Document URL to crawl
            filename: Optional saved filename

        Returns:
            Dict with document details

        Raises:
            ValueError: If ESP doesn't exist or URL already exists
        """
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
            INSERT INTO esp_documents (id, esp_id, url, filename, crawl_status)
            VALUES (%s, %s, %s, %s, 'pending')
            RETURNING id, url, filename, crawl_status, created_at
        """
        doc_id = str(uuid.uuid4())
        params = (doc_id, esp['id'], url, filename)

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
                'created_at': _iso(row[4])
            }
        return None

    def find_documents_by_url(self, url: str) -> List[Dict]:
        """
        Every document whose URL matches `url` exactly (1:1, no
        normalisation), across all ESPs including global knowledge.

        Returns a list of {'esp_name', 'display_name', 'filename',
        'crawl_status'}; empty if the URL is new.
        """
        query = """
            SELECT e.name, e.display_name, d.filename, d.crawl_status
            FROM esp_documents d
            JOIN esps e ON e.id = d.esp_id
            WHERE d.url = %s AND e.status = 'active'
            ORDER BY e.name
        """
        rows = self.db.execute_query(query, (url,), fetch=True) or []
        return [{
            'esp_name': r[0],
            'display_name': r[1] or r[0],
            'filename': r[2],
            'crawl_status': r[3],
        } for r in rows]

    def get_document_by_url(self, esp_id: str, url: str) -> Optional[Dict]:
        """Get document by ESP ID and URL."""
        query = """
            SELECT id, esp_id, url, filename, content_hash, crawl_status,
                   last_crawled_at, error_message, vector_ids, created_at, updated_at
            FROM esp_documents
            WHERE esp_id = %s AND url = %s
        """
        result = self.db.execute_query(query, (esp_id, url), fetch=True)
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
                'updated_at': _iso(row[10])
            }
        return None

    def list_documents(self, esp_name: str) -> List[Dict]:
        """List all documents for an ESP."""
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
            WHERE esp_id = %s
            ORDER BY created_at DESC
        """
        results = self.db.execute_query(query, (esp['id'],), fetch=True)

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
        """Set (or clear, with None) the product label on an ESP's documents.

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
            WHERE d.product = 'reviews'
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
        filesystem.
        """
        esp = self.get_esp_by_name(esp_name)
        if not esp:
            return []

        query = """
            SELECT id, url, filename, content, content_hash, crawl_status
            FROM esp_documents
            WHERE esp_id = %s
            ORDER BY created_at ASC
        """
        results = self.db.execute_query(query, (esp['id'],), fetch=True)

        return [{
            'id': row[0],
            'url': row[1],
            'filename': row[2],
            'content': row[3],
            'content_hash': row[4],
            'crawl_status': row[5]
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
            WHERE esp_id = %s
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
