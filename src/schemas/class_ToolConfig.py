"""Handler for creating tools."""
################################################################################
from flask import request, jsonify, current_app
from pydantic import BaseModel, Field, ValidationError
from typing import Optional
from pathlib import Path
################################################################################

class ToolConfig(BaseModel):
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=12, 
        pattern=r"^[a-zA-Z]([a-zA-Z_]*[a-zA-Z])?$",
        description="Tool name (1-12 characters, only letters and underscores, must start and end with a letter)"
    )
    created_at: Optional[str] = Field(
        None, 
        description="Timestamp of tool creation in ISO 8601 format"
    )
    description: Optional[str] = Field(None, max_length=500, description="Tool description")
    system_id: Optional[str] = Field(None, description="Associated system ID (set at creation time)")
    system_prompt: Optional[str] = Field(
        "You are a helpful assistant", 
        max_length=500, 
        description="System prompt for the tool"
    )
    has_document_library: bool = Field(
        True,
        description="Whether this tool has an associated document library"
    )
    document_count: Optional[int] = Field(
        None,
        description="Number of documents in the tool's library"
    )
    local_path_to_vector_store: Optional[str] = Field(
        None,
        description="Local path to the vector store for this tool"
    )
    local_path_to_document_library: Optional[str] = Field(
        None,
        description="Local path to the document library for this tool"
    )
