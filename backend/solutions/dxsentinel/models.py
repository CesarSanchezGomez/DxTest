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


class ProcessResponse(BaseModel):
    success: bool
    message: str
    field_count: int = 0
    processing_time: float = 0
    download_id: Optional[str] = None
    countries_processed: Optional[list[str]] = None
