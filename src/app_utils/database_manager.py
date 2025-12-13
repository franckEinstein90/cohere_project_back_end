################################################################################
# Database manager for document library uploads
################################################################################
import sqlite3
from contextlib import contextmanager
################################################################################
from .database_utils import BaseDB, ToolsDB, DocumentsDB
################################################################################


class DocumentLibraryDB:
    """Main database manager that provides access to tools and documents."""
    
    def __init__(self, db_path: str = "document_library.db"):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.tools = ToolsDB(db_path)
        self.documents = DocumentsDB(db_path)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def create_database(self):
        """Create the database schema if it doesn't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tools table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tools (
                    tool_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    system_prompt TEXT CHECK(length(system_prompt) <= 500),
                    has_document_library BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'  -- active, archived, deleted
                )
            """)
            
            # Main documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_size INTEGER,
                    file_type TEXT,
                    uploaded_by TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Core metadata
                    title TEXT,
                    description TEXT,
                    
                    -- Categorization
                    topic TEXT,
                    keywords TEXT,  -- Stored as JSON array
                    category TEXT,
                    
                    -- Authorship and versioning
                    author TEXT,
                    organization TEXT,
                    version TEXT,
                    
                    -- Dates
                    document_date TIMESTAMP,
                    last_updated TIMESTAMP,
                    
                    -- Additional context
                    language TEXT DEFAULT 'en',
                    source_url TEXT,
                    notes TEXT,
                    
                    -- Access and visibility
                    visibility TEXT DEFAULT 'internal',
                    department TEXT,
                    
                    -- Processing info
                    chunk_count INTEGER,
                    chunk_size INTEGER,
                    chunk_overlap INTEGER,
                    vectorstore_path TEXT,
                    
                    -- Status
                    status TEXT DEFAULT 'active',  -- active, archived, deleted
                    
                    UNIQUE(tool_id, filename),
                    FOREIGN KEY (tool_id) REFERENCES tools(tool_id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for tools table
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tools_status 
                ON tools(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tools_created_at 
                ON tools(created_at)
            """)
            
            # Create indexes for documents table
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tool_id 
                ON documents(tool_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_category 
                ON documents(category)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_uploaded_at 
                ON documents(uploaded_at)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON documents(status)
            """)
            
            print(f"✓ Database created successfully at: {self.db_path}")
