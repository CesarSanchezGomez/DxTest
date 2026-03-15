from backend.hub.registry import register_solution

register_solution({
    "name": "DxSentinel",
    "slug": "dxsentinel",
    "description": "SAP SuccessFactors · Golden Record Generator",
    "icon": "solutions/dxsentinel.png",
    "pages": [
        {"name": "Golden Record", "path": "upload"},
        {"name": "Split", "path": "split"},
    ],
})
