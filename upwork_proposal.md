# Upwork Proposal - Martinique Weather Data Visualization

---

I have been building complex data pipelines and visualization systems for my work for years and thought I would offer my services on Upwork. Rather than telling you I could do this project, I wanted to show you that I have already done it.

Below is a visualization I built this evening using the Météo France API for Martinique - a 48-hour hourly forecast dashboard for Fort-de-France showing temperature, precipitation probability, and wind data:

[ATTACH: hourly_dashboard_screenshot.png]

The system also generates vigilance maps, multi-city temperature forecasts, and automated updates.

**Technical approach:**
- Python with meteofrance-api and meteole libraries for API access
- Folium for interactive maps (supports multiple tile layers)
- Plotly for responsive charts
- pandas for data processing
- schedule for automation
- Clean modular architecture (easy to add new maps or data sources)

**Deliverables I can provide:**
- All source code with documentation
- Docker deployment option if needed
- Easy extension for additional visualizations
- Integration with your existing vigilance map work

The code is already working. Happy to share the repository and discuss how to integrate with your existing project.

---

## Technical Notes for Discussion

**API Libraries Used:**
- `meteofrance-api` - Python wrapper for Météo France mobile app API
- `meteole` - MAIF's library for official Météo France data portal (AROME/ARPEGE models)

**Martinique Coverage:**
- Department code: 972
- Vigilance alerts fully supported
- All 10 major cities mapped with coordinates

**Output Formats:**
- Interactive HTML maps (Folium)
- Interactive HTML charts (Plotly)
- CSV data exports
- JSON alert data

Let me know if you would like to see the code or discuss the implementation.
