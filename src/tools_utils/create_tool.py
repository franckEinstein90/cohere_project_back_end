import uuid
import json
from datetime import datetime
from pathlib import Path
from flask import current_app
################################################################################
from src.app_utils import DocumentLibraryDB
from src.schemas import ToolConfig

def _clean_up_partial_tool(tool_id: str) -> None:
    pass

def create_tool(tool_config: ToolConfig) -> dict:
    """
    Create a new tool with a unique tool_id and initialize its library directory.
    
    Args:
        tool_config: ToolConfig object with tool details.
        
    Returns:
        Dictionary with tool metadata.
        
    Raises:
        OSError: If directory creation fails.
        Exception: For other unexpected errors.
    """
    # Generate unique tool_id
    tool_id = str(uuid.uuid4())
    # add tool_id to tool_config as system_id
    tool_config.system_id = tool_id
    

    try:
        # Create library directory structure
        root_path = Path(current_app.root_path)
        library_path = root_path / "libraries" / tool_config.name / "documents"
        library_path.mkdir(parents=True, exist_ok=False)
        tool_config.local_path_to_document_library = str(library_path)

        vector_store_path = root_path / "libraries" / tool_config.name / "vector_store"
        vector_store_path.mkdir(parents=True, exist_ok=False)
        tool_config.local_path_to_vector_store = str(vector_store_path)

    except FileExistsError:
        raise FileExistsError(f"Tool directory already exists: {tool_id}")
    except PermissionError as e:
        raise PermissionError(f"Permission denied creating tool directory: {str(e)}")
    except OSError as e:
        raise OSError(f"OS error creating tool directory: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error creating tool directory: {str(e)}")

    try:
        db = DocumentLibraryDB()
        db.tools.add(tool_config=tool_config)
    except Exception as e:
        raise Exception(f"Failed to add tool to database: {str(e)}")

    tool_config.created_at = datetime.utcnow().isoformat() + "Z"
    current_app.logger.info(f"Created new tool: {tool_id} - {tool_config.name}")
    
    return {
        "status": "success",
        "tool_id": tool_id,
        "name": tool_config.name,
        "description": tool_config.description,
        "library_path": str(library_path),
        "created_at": tool_config.created_at
    }
