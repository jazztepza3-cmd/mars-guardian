# MARS GUARDIAN — research notes

## Source-derived design principles

### Rover navigation
NASA/JPL material on Mars Exploration Rover surface navigation describes stereo-vision-based terrain assessment, hazard detection/avoidance, and path planning. NASA's technical brief on improved onboard path planning describes combining local terrain/hazard costs with global path planning. JPL's Next-Gen AutoNav concept describes terrain classification paired with risk-aware path planning.

**Design implication:** keep the route planner explainable. Show a route, the cost field it responds to, and the trade-off between distance and modeled risk.

### Dust and energy
NASA NTRS material on MER power operations describes using solar-array output to infer dust accumulation and cleaning events. Another NASA technical report describes the multiple factors that influence array output, including solar geometry, rover tilt, atmospheric opacity, and dust deposition.

**Design implication:** do not treat “dust storm” as a single magic switch that perfectly predicts energy. In the prototype, dust intensity and array cleanliness are user-set scenario assumptions and must be labeled as such. A future model should identify the exact dataset, variables, calibration method, and uncertainty.

### Terrain data
NASA's public HiRISE DTM dataset catalog describes derived Digital Terrain Models and corresponding orthoimages.

**Design implication:** a future evidence-based digital twin should document the selected product, spatial resolution, coordinate system, map projection, no-data handling, and any resampling. A visually realistic synthetic terrain is useful for interface testing but must not be represented as a real Mars location.

## References

1. JPL, MER Surface Navigation: https://robotics.jpl.nasa.gov/what-we-do/flight-projects/mars-exploration-rovers/surface-navigation/
2. NASA NTRS, Improved Path Planning Onboard the Mars Exploration Rovers: https://ntrs.nasa.gov/citations/20100010963
3. JPL, Next-Gen AutoNav Concept: https://www-robotics.jpl.nasa.gov/what-we-do/research-tasks/next-gen-autonav-concept/
4. NASA NTRS, Power Operations of the Mars Exploration Rovers: https://ntrs.nasa.gov/citations/20230007029
5. NASA NTRS, Dust Accumulation and Solar Panel Array Performance on the Mars Exploration Rover Project: https://ntrs.nasa.gov/citations/20050186821
6. NASA Open Data Portal, MRO HiRISE DTM V1.0: https://data.nasa.gov/dataset/mro-mars-high-resolution-imaging-science-experiment-dtm-v1-0

## Important scope distinction
The references above support the overall research direction, not the accuracy of this code's synthetic terrain, risk scores, A* cost function, or energy equation. Those must be independently tested and validated before scientific performance claims are made.
