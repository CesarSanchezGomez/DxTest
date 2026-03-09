from backend.hub.registry import register_solution

register_solution({
    "name": "DxModels",
    "slug": "dxmodels",
    "description": "SAP SuccessFactors · Data Models",
    "icon": "solutions/dxmodels.png",
    "pages": [
        {"name": "CDM", "path": "cdm"},
        {"name": "CSF CDM", "path": "csf-cdm"},
        {"name": "SDM", "path": "sdm"},
        {"name": "CSF SDM", "path": "csf-sdm"},
        {"name": "Completo", "path": "full"},
    ],
})
