"""Schema for updating an existing tool."""
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class ToolUpdate(BaseModel):
    """Payload for updating a tool's metadata."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=12,
        pattern=r"^[a-zA-Z]([a-zA-Z_]*[a-zA-Z])?$",
        description="Updated tool name (1-12 characters, only letters and underscores, must start and end with a letter)",
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Updated tool description",
    )

    @model_validator(mode="after")
    def validate_fields_present(self):
        """Ensure at least one field is provided for update."""
        if self.name is None and self.description is None:
            raise ValueError("At least one of 'name' or 'description' must be provided.")
        return self
