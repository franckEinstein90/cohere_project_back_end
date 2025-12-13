"""Database manager for tools operations."""
from typing import Optional, Dict, Any, List
from .base_db import BaseDB
from src.schemas import ToolConfig

class ToolsDB(BaseDB):
    """Database manager for tools operations."""
    
    def add(
        self,
        tool_config: ToolConfig
    ) -> str:
        """Add a new tool to the database.
        
        Args:
            tool_id: Unique tool identifier (UUID)
            tool_config: ToolConfig object with name, description, system_id, system_prompt, and has_document_library
            
        Returns:
            str: tool_id of inserted tool
        """
        
        # Throw an error if tool_config doesn't have system_id set
        if not tool_config.system_id:
            raise ValueError("tool_config.system_id must be set before adding to database.")

        check_existing = self.get_by_name(tool_config.name)
        if check_existing:
            raise ValueError(f"Tool with name '{tool_config.name}' already exists.")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tools (tool_id, name, description, system_prompt, has_document_library)
                VALUES (?, ?, ?, ?, ?)
            """, (tool_config.system_id, tool_config.name, tool_config.description, 
                  tool_config.system_prompt, tool_config.has_document_library))
            
            return tool_config.system_id 

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Dictionary of tool data or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tools WHERE name = ?", (name,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None 

    def get(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a tool by ID.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            Dictionary of tool data or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tools WHERE tool_id = ?", (tool_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_all(self, status: str = 'active') -> List[Dict[str, Any]]:
        """Get all tools.
        
        Args:
            status: Tool status filter (default: 'active')
            
        Returns:
            List of tool dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tools WHERE status = ? ORDER BY created_at DESC",
                (status,)
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update(
        self,
        tool_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ):
        """Update tool information.
        
        Args:
            tool_id: Tool identifier
            name: New tool name (optional)
            description: New description (optional)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            if updates:
                query = f"UPDATE tools SET {', '.join(updates)} WHERE tool_id = ?"
                params.append(tool_id)
                cursor.execute(query, params)
    
    def update_status(self, tool_id: str, status: str):
        """Update tool status.
        
        Args:
            tool_id: Tool identifier
            status: New status ('active', 'archived', 'deleted')
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tools SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE tool_id = ?",
                (status, tool_id)
            )
    
    def delete(self, tool_id: str):
        """Hard delete a tool and all its documents (CASCADE).
        
        Args:
            tool_id: Tool identifier
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tools WHERE tool_id = ?", (tool_id,))
    
    def get_statistics(self, tool_id: str) -> Dict[str, Any]:
        """Get statistics for a tool.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            Dictionary with document count and other stats
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get document count
            cursor.execute(
                "SELECT COUNT(*) as doc_count FROM documents WHERE tool_id = ? AND status = 'active'",
                (tool_id,)
            )
            doc_count = cursor.fetchone()['doc_count']
            
            # Get total file size
            cursor.execute(
                "SELECT SUM(file_size) as total_size FROM documents WHERE tool_id = ? AND status = 'active'",
                (tool_id,)
            )
            total_size = cursor.fetchone()['total_size'] or 0
            
            # Get latest upload
            cursor.execute(
                "SELECT MAX(uploaded_at) as latest_upload FROM documents WHERE tool_id = ? AND status = 'active'",
                (tool_id,)
            )
            latest_upload = cursor.fetchone()['latest_upload']
            
            return {
                'document_count': doc_count,
                'total_size_bytes': total_size,
                'latest_upload': latest_upload
            }
