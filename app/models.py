from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union

class SummaryRequest(BaseModel):
    """Request model for text summarization."""
    text: str = Field(..., description="The text to summarize")
    length: Optional[str] = Field("medium", description="Length of summary: 'short', 'medium', or 'long'")
    format: Optional[str] = Field("paragraph", description="Format of summary: 'paragraph' or 'bullets'")
    extractiveness: Optional[str] = Field("low", description="Extractiveness: 'low' or 'high'")
    
    @validator('length')
    def validate_length(cls, v):
        if v not in ['short', 'medium', 'long']:
            raise ValueError("Length must be one of: 'short', 'medium', 'long'")
        return v
        
    @validator('format')
    def validate_format(cls, v):
        if v not in ['paragraph', 'bullets']:
            raise ValueError("Format must be one of: 'paragraph', 'bullets'")
        return v
        
    @validator('extractiveness')
    def validate_extractiveness(cls, v):
        if v not in ['low', 'high']:
            raise ValueError("Extractiveness must be one of: 'low', 'high'")
        return v

class TaskResponse(BaseModel):
    """Response model for task creation."""
    task_id: str = Field(..., description="The ID of the created task")
    status: str = Field("pending", description="The status of the task")

class ResultResponse(BaseModel):
    """Response model for task results."""
    result: str = Field(..., description="The result of the task")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about the result")

class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class HealthResponse(BaseModel):
    """Response model for health checks."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    components: Dict[str, Dict[str, str]] = Field(..., description="Status of individual components")
