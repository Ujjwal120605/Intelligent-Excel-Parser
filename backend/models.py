from pydantic import BaseModel, Field
from typing import List, Optional, Any

class MappingResult(BaseModel):
    original_header: str = Field(description="The original 'messy' header from the Excel file.")
    mapped_parameter: str = Field(description="The matching parameter name from the Canonical Registry.")
    confidence: float = Field(description="A confidence score between 0.0 and 1.0 indicating how certain the mapping is.")
    detected_asset: Optional[str] = Field(None, description="The asset extracted from the header, if any (e.g., 'Boiler 1').")

class MappingResponse(BaseModel):
    mappings: List[MappingResult] = Field(description="List of all mappings for the provided headers.")

class ParsedData(BaseModel):
    row: int
    col: int
    param_name: str
    asset_name: Optional[str] = None
    raw_value: Any
    parsed_value: Optional[float] = None
    confidence: str

class UnmappedColumn(BaseModel):
    col: int
    header: str
    reason: str

class APIResponse(BaseModel):
    status: str
    header_row: int
    parsed_data: List[ParsedData]
    unmapped_columns: List[UnmappedColumn]
    warnings: List[str]
