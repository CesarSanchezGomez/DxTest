from pydantic import BaseModel, Field
from typing import Optional, List


class ProcesamientoRequest(BaseModel):
    xml_content: str = Field(..., description="Contenido del archivo XML")
    paises: Optional[List[str]] = Field(default=None, description="Codigos de paises")
    idiomas: Optional[List[str]] = Field(default=None, description="Codigos de idiomas")


class ProcesamientoResponse(BaseModel):
    success: bool
    resultado: str
    message: str


class ProcesamientoCompletoRequest(BaseModel):
    cdm_xml: Optional[str] = None
    csf_cdm_xml: Optional[str] = None
    sdm_xml: Optional[str] = None
    csf_sdm_xml: Optional[str] = None
    paises: List[str] = Field(default_factory=list)
    idiomas: List[str] = Field(default_factory=list)
