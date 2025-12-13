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
        db = DocumentLibraryDB()
        db.tools.add(tool_config=tool_config)
    except Exception as e:
        raise Exception(f"Failed to add tool to database: {str(e)}")

    try:
        # Create library directory structure
        root_path = Path(current_app.root_path)
        library_path = root_path / "libraries" / tool_id
        library_path.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        raise FileExistsError(f"Tool directory already exists: {tool_id}")
    except PermissionError as e:
        raise PermissionError(f"Permission denied creating tool directory: {str(e)}")
    except OSError as e:
        raise OSError(f"OS error creating tool directory: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error creating tool directory: {str(e)}")

    try: 
        # Create subdirectories for organization
        (library_path / "documents").mkdir(exist_ok=True)
        (library_path / "metadata").mkdir(exist_ok=True)
        (library_path / "embeddings").mkdir(exist_ok=True)
    except OSError as e:
        raise OSError(f"Failed to create library subdirectories: {str(e)}")


        # Create tool metadata file
        tool_metadata = {
            "tool_id": tool_id,
            "name": tool_config.name,
            "description": tool_config.description,
            "created_at": datetime.utcnow().isoformat(),
            "document_count": 0
        }
        
        metadata_file = library_path / "tool_metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as mf:
            json.dump(tool_metadata, mf, ensure_ascii=False, indent=2)
        
        return tool_metadata
    
    except OSError as e:
        raise OSError(f"Failed to create library directories: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error during tool creation: {str(e)}")