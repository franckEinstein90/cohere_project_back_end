"""Database manager for documents operations."""
import json
from typing import Optional, Dict, Any, List
from .base_db import BaseDB


class DocumentsDB(BaseDB):
    """Database manager for documents operations."""
    
    def add(
        self,
        tool_id: str,
        filename: str,
        metadata_obj: Optional[Any],  # DocumentMetadata
        chunk_count: int,
        chunk_size: int,
        chunk_overlap: int,
        vectorstore_path: str,
        uploaded_by: Optional[str] = None,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None
    ) -> int:
        """Add a document record to the database.
        
        Args:
            tool_id: Tool/library identifier
            filename: Name of uploaded file
            metadata_obj: DocumentMetadata object (can be None)
            chunk_count: Number of chunks created
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
            vectorstore_path: Path to vectorstore
            uploaded_by: Username of uploader
            file_size: Size of file in bytes
            file_type: MIME type or file extension
            
        Returns:
            int: ID of inserted document
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Extract metadata fields
            if metadata_obj:
                title = metadata_obj.title
                description = metadata_obj.description
                topic = metadata_obj.topic
                keywords = json.dumps(metadata_obj.keywords) if metadata_obj.keywords else None
                category = metadata_obj.category
                author = metadata_obj.author
                organization = metadata_obj.organization
                version = metadata_obj.version
                document_date = metadata_obj.document_date.isoformat() if metadata_obj.document_date else None
                last_updated = metadata_obj.last_updated.isoformat() if metadata_obj.last_updated else None
                language = metadata_obj.language
                source_url = metadata_obj.source_url
                notes = metadata_obj.notes
                visibility = metadata_obj.visibility
                department = metadata_obj.department
            else:
                # Use defaults if no metadata provided
                title = filename
                description = None
                topic = None
                keywords = None
                category = None
                author = None
                organization = None
                version = None
                document_date = None
                last_updated = None
                language = 'en'
                source_url = None
                notes = None
                visibility = 'internal'
                department = None
            
            cursor.execute("""
                INSERT INTO documents (
                    tool_id, filename, file_size, file_type, uploaded_by,
                    title, description, topic, keywords, category,
                    author, organization, version, document_date, last_updated,
                    language, source_url, notes, visibility, department,
                    chunk_count, chunk_size, chunk_overlap, vectorstore_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tool_id, filename, file_size, file_type, uploaded_by,
                title, description, topic, keywords, category,
                author, organization, version, document_date, last_updated,
                language, source_url, notes, visibility, department,
                chunk_count, chunk_size, chunk_overlap, vectorstore_path
            ))
            
            return cursor.lastrowid
    
    def get(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Dictionary of document data or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            
            if row:
                doc = dict(row)
                # Parse JSON keywords back to list
                if doc['keywords']:
                    doc['keywords'] = json.loads(doc['keywords'])
                return doc
            return None
    
    def get_by_tool(
        self,
        tool_id: str,
        status: str = 'active'
    ) -> List[Dict[str, Any]]:
        """Get all documents for a specific tool.
        
        Args:
            tool_id: Tool identifier
            status: Document status filter (default: 'active')
            
        Returns:
            List of document dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM documents WHERE tool_id = ? AND status = ? ORDER BY uploaded_at DESC",
                (tool_id, status)
            )
            
            documents = []
            for row in cursor.fetchall():
                doc = dict(row)
                if doc['keywords']:
                    doc['keywords'] = json.loads(doc['keywords'])
                documents.append(doc)
            
            return documents
    
    def search(
        self,
        tool_id: Optional[str] = None,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        author: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search documents with various filters.
        
        Args:
            tool_id: Filter by tool ID
            category: Filter by category
            keyword: Search in keywords
            author: Filter by author
            
        Returns:
            List of matching documents
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM documents WHERE status = 'active'"
            params = []
            
            if tool_id:
                query += " AND tool_id = ?"
                params.append(tool_id)
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if keyword:
                query += " AND keywords LIKE ?"
                params.append(f'%{keyword}%')
            
            if author:
                query += " AND author = ?"
                params.append(author)
            
            query += " ORDER BY uploaded_at DESC"
            
            cursor.execute(query, params)
            
            documents = []
            for row in cursor.fetchall():
                doc = dict(row)
                if doc['keywords']:
                    doc['keywords'] = json.loads(doc['keywords'])
                documents.append(doc)
            
            return documents
    
    def update_status(self, doc_id: int, status: str):
        """Update document status (e.g., archive or soft delete).
        
        Args:
            doc_id: Document ID
            status: New status ('active', 'archived', 'deleted')
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE documents SET status = ? WHERE id = ?",
                (status, doc_id)
            )
    
    def delete(self, doc_id: int):
        """Hard delete a document.
        
        Args:
            doc_id: Document ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
