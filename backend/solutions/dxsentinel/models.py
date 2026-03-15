from pydantic import BaseModel, Field
from typing import Optional


class UploadResponse(BaseModel):
    success: bool
    message: str
    file_id: Optional[str] = None
    filename: Optional[str] = None


class LanguagesResponse(BaseModel):
    success: bool
    languages: list[str] = []


class CountriesResponse(BaseModel):
    success: bool
    countries: list[str] = []


class EntitiesResponse(BaseModel):
    success: bool
    entities: list[str] = []


class ProcessRequest(BaseModel):
    main_file_id: str
    csf_file_id: Optional[str] = None
    language_code: str = Field(default="en-US", pattern=r"^[a-zA-Z]{2}(-[a-zA-Z]{2,})?$")
    country_codes: Optional[list[str]] = None
    excluded_entities: Optional[list[str]] = None
    # Versionado
    instance_number: str = Field(..., min_length=1, max_length=50)
    client_name: str = Field(..., min_length=1, max_length=100)


class ProcessResponse(BaseModel):
    success: bool
    message: str
    field_count: int = 0
    processing_time: float = 0
    download_id: Optional[str] = None
    countries_processed: Optional[list[str]] = None
    version_number: Optional[int] = None
    instance_number: Optional[str] = None
    client_name: Optional[str] = None


class ValidateRequest(BaseModel):
    version_id: str
    csv_file_id: str


class ValidationIssue(BaseModel):
    severity: str
    code: str
    message: str
    element_id: Optional[str] = None
    field_id: Optional[str] = None
    country_code: Optional[str] = None
    validator: Optional[str] = None
    row_index: Optional[int] = None
    column_name: Optional[str] = None
    person_id: Optional[str] = None
    value: Optional[str] = None


class ValidateResponse(BaseModel):
    success: bool
    message: str
    can_split: bool = False
    summary: dict = {}
    issues: list[ValidationIssue] = []


class SplitRequest(BaseModel):
    version_id: str
    csv_file_id: str


class SplitResponse(BaseModel):
    success: bool
    message: str
    template_count: int = 0
    processing_time: float = 0
    download_id: Optional[str] = None
