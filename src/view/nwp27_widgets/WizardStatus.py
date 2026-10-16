STEP_INCOMPLETE = 0
STEP_UNKNOWN = 1
STEP_COMPLETE = 2

PRODUCTS = [
    {"name": "Vicinity Map", "description": "Overview of the project location", "machine_code": "nwp_project_vicinity", "is_layout": True},
    {"name": "Project Elements Layout", "description": "Project extent, catchment area and vicinity map", "machine_code": "nwp_project_overview", "is_layout": True},
    {"name": "Reaches Layout", "description": "Zoomed in layout for each reach", "machine_code": "nwp_reaches", "is_layout": True},
    # {"name": "Habitat Zones & Conditions", "description": "Description for Layout 2", "machine_code": "machine2", "is_layout": True},
    # {"name": "Project Summary", "description": "Description for Layout 3", "machine_code": "machine3", "is_layout": True},
    # {"name": "Reach Elements & Expected Outcomes Layout", "description": "Focus maps on each reach", "machine_code": "machine4", "is_layout": True},
    {"name": "JSON Export", "description": "Description for JSON Export", "machine_code": "json_export", "is_layout": False},
    {"name": "HTML Export", "description": "HTML rendering of the project data", "machine_code": "html_export", "is_layout": False},
]
