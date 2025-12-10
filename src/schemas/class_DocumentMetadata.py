from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class DocumentMetadata(BaseModel):
    """Metadata for reference documents, manuals, and organizational materials.
    
    This model captures information about files stored in the library to enable
    search, categorization, and proper attribution.
    """
    
    # Core identification
    title: Optional[str] = Field(None, description="Document title", min_length=1, max_length=500)
    description: Optional[str] = Field(None, description="Brief description of the document content")
    
    # Categorization
    topic: Optional[str] = Field(None, description="Primary topic or subject area", max_length=200)
    keywords: Optional[List[str]] = Field(default_factory=list, description="Keywords/tags for search and filtering")
    category: Optional[str] = Field(None, description="Document category (e.g., manual, policy, guide, reference)")
    
    # Authorship and versioning
    author: Optional[str] = Field(None, description="Document author or creator", max_length=200)
    organization: Optional[str] = Field(None, description="Organization or department", max_length=200)
    version: Optional[str] = Field(None, description="Document version (e.g., 1.0, v2.3)", max_length=50)
    
    # Dates
    document_date: Optional[datetime] = Field(None, description="Document creation or publication date")
    last_updated: Optional[datetime] = Field(None, description="Last modification date of the source document")
    
    # Additional context
    language: Optional[str] = Field("en", description="Document language code (ISO 639-1)", max_length=10)
    source_url: Optional[str] = Field(None, description="Original source URL if applicable")
    notes: Optional[str] = Field(None, description="Additional notes or context")
    
    # Access and visibility
    visibility: Optional[str] = Field("internal", description="Visibility level (e.g., public, internal, restricted)")
    department: Optional[str] = Field(None, description="Relevant department or team", max_length=200)
    
    class Config:
        # Allow extra fields to be ignored for forward compatibility
        extra = "ignore"
