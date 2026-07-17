"""
ESP Manager - Database-backed ESP management

Manages ESPs and their documentation URLs in PostgreSQL.
Replaces filesystem-based ESP storage (docs/ folders + CSV).
"""

import uuid
import hashlib
from typing import List, Dict, Optional
from adapters.database.db_manager import get_database_adapter


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

        # Check if exists
        if self.get_esp_by_name(name):
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
                'created_at': row[5].isoformat() if row[5] else None
            }
        return None

    def get_esp_by_name(self, name: str) -> Optional[Dict]:
        """Get ESP by name."""
        query = """
            SELECT id, name, display_name, description, status, created_at, updated_at
            FROM esps
            WHERE name = %s AND status = 'active'
        """
        result = self.db.execute_query(query, (name,), fetch=True)
        if result:
            row = result[0]
            return {
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'description': row[3],
                'status': row[4],
                'created_at': row[5].isoformat() if row[5] else None,
                'updated_at': row[6].isoformat() if row[6] else None
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
                'created_at': row[5].isoformat() if row[5] else None,
                'updated_at': row[6].isoformat() if row[6] else None
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
                'created_at': row[5].isoformat() if row[5] else None,
                'updated_at': row[6].isoformat() if row[6] else None,
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

        # Check if URL already exists
        existing = self.get_document_by_url(esp['id'], url)
        if existing:
            raise ValueError(f"URL already exists for ESP '{esp_name}'")

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
                'created_at': row[4].isoformat() if row[4] else None
            }
        return None

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
                'last_crawled_at': row[6].isoformat() if row[6] else None,
                'error_message': row[7],
                'vector_ids': row[8],
                'created_at': row[9].isoformat() if row[9] else None,
                'updated_at': row[10].isoformat() if row[10] else None
            }
        return None

    def list_documents(self, esp_name: str) -> List[Dict]:
        """List all documents for an ESP."""
        esp = self.get_esp_by_name(esp_name)
        if not esp:
            return []

        query = """
            SELECT id, url, filename, content_hash, crawl_status,
                   last_crawled_at, error_message, created_at, updated_at
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
                'last_crawled_at': row[5].isoformat() if row[5] else None,
                'error_message': row[6],
                'created_at': row[7].isoformat() if row[7] else None,
                'updated_at': row[8].isoformat() if row[8] else None
            })
        return docs

    def update_document_crawl_status(self, doc_id: str, status: str,
                                      content_hash: str = None,
                                      error_message: str = None,
                                      vector_ids: List[str] = None) -> bool:
        """
        Update document after crawl attempt.

        Args:
            doc_id: Document UUID
            status: 'completed' or 'failed'
            content_hash: SHA-256 hash of content (if successful)
            error_message: Error message (if failed)
            vector_ids: List of vector DB chunk IDs (if successful)
        """
        query = """
            UPDATE esp_documents
            SET crawl_status = %s,
                last_crawled_at = CURRENT_TIMESTAMP,
                content_hash = %s,
                error_message = %s,
                vector_ids = %s
            WHERE id = %s
        """
        # Convert vector_ids list to JSON string
        import json
        vector_ids_json = json.dumps(vector_ids) if vector_ids else None

        params = (status, content_hash, error_message, vector_ids_json, doc_id)
        self.db.execute_query(query, params)
        return True

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
                'last_crawl': row[4].isoformat() if row[4] else None
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
