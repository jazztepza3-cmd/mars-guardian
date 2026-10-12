# MARS GUARDIAN

**Predictive Planetary Exploration Intelligence**

A student-built Mars mission-planning prototype that combines an interactive 3D Mars-like terrain, risk-aware route planning, dust scenario controls, and an illustrative energy budget.

> **Scientific integrity:** the current terrain, dust field, and rover telemetry are synthetic. The energy equation is illustrative and not fitted to a specific flight rover. NASA/JPL references inform the system design, but this project is not a NASA product and does not provide real mission forecasts.

## Run locally

Requires Python 3.10 or newer.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

If using GitHub Codespaces, open this repository in a Codespace, run the install command in its terminal, then run `streamlit run app.py`. Open the forwarded port shown by Codespaces (usually 8501).

## What is included

- **Mars Digital Twin:** interactive 3D procedural terrain, two route candidates, start/target markers, risk coloring, simulated rover marker.
- **Route Intelligence:** shortest-distance and risk-aware A* candidates with explicit trade-offs.
- **Energy Survival Lab:** transparent illustrative estimate influenced by distance, terrain, dust scenario, and array-cleanliness assumption.
- **Science & Limitations:** NASA/JPL references, data-integrity statement, limitations, and validation plan.

## Project structure

```text
mars-guardian/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── docs/
    └── research-notes.md
```

## Scientific roadmap

1. Select a real study region and a documented terrain product (for example, a HiRISE DTM where suitable).
2. Preserve metadata: product ID, spatial resolution, coordinate system, acquisition date, source URL, and processing steps.
3. Replace the procedural terrain with the real elevation raster and derive slope/roughness from it.
4. Keep measured data, model outputs, and user-set assumptions visually distinct.
5. Validate route planning against baselines and document failure cases before making accuracy claims.
6. Only add dust forecasting when a defensible dataset/model and evaluation method are available.

## Competition demo flow (3–4 minutes)

1. Start in **Mars Digital Twin** and rotate the terrain to show the route context.
2. Explain that the current site is a synthetic test environment, not a real mapped location.
3. Increase **Dust event intensity** and lower **Solar array cleanliness**.
4. Compare the shortest route with the risk-aware candidate.
5. Show whether the energy budget is exceeded and explain the trade-off.
6. Finish in **Science & Limitations** to demonstrate traceability and a credible path to validation.

## NASA/JPL starting references

- JPL, [MER Surface Navigation](https://robotics.jpl.nasa.gov/what-we-do/flight-projects/mars-exploration-rovers/surface-navigation/)
- NASA NTRS, [Improved Path Planning Onboard the Mars Exploration Rovers](https://ntrs.nasa.gov/citations/20100010963)
- JPL, [Next-Gen AutoNav Concept](https://www-robotics.jpl.nasa.gov/what-we-do/research-tasks/next-gen-autonav-concept/)
- NASA NTRS, [Power Operations of the Mars Exploration Rovers](https://ntrs.nasa.gov/citations/20230007029)
- NASA NTRS, [Dust Accumulation and Solar Panel Array Performance](https://ntrs.nasa.gov/citations/20050186821)
- NASA Open Data Portal, [HiRISE Digital Terrain Models](https://data.nasa.gov/dataset/mro-mars-high-resolution-imaging-science-experiment-dtm-v1-0)

## Suggested GitHub repository description

Interactive Mars mission-planning prototype for dust-aware route comparison, terrain risk visualization, and energy-budget scenario analysis.
