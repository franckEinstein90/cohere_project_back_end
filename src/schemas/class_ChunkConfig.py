################################################################################
from pydantic import BaseModel, Field, ValidationError, field_validator
################################################################################

class ChunkConfig(BaseModel):
    chunk_size: int = Field(default=1000, ge=1, le=10000)
    chunk_overlap: int = Field(default=200, ge=0)
    
    @field_validator('chunk_overlap')
    @classmethod
    def validate_overlap(cls, v, info):
        chunk_size = info.data.get('chunk_size', 1000)
        if v >= chunk_size:
            raise ValueError('chunk_overlap must be less than chunk_size')
        return v
