from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import plotly.graph_objects as go
import streamlit as st

# MARS GUARDIAN — an educational mission-planning prototype.
# The terrain, dust field, and rover telemetry in this MVP are synthetic.
# Do not present the outputs as operational forecasts or validated NASA models.

st.set_page_config(page_title="MARS GUARDIAN | Mission Systems", page_icon="🔴", layout="wide")

# ---------- Visual system ----------
BG = "#090D12"
PANEL = "#111821"
LINE = "#263342"
TEXT = "#E8EEF4"
MUTED = "#91A0B2"
CYAN = "#59D8E8"
AMBER = "#F3B65D"
RED = "#FF6B61"
GREEN = "#83D6A3"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');
:root {{ color-scheme: dark; }}
html, body, [class*="css"] {{ font-family: Inter, sans-serif; }}
.stApp {{ background: radial-gradient(ellipse at 78% 0%, #1d2024 0%, {BG} 48%); color: {TEXT}; }}
[data-testid="stSidebar"] {{ background: #0d131b; border-right: 1px solid {LINE}; }}
.block-container {{ padding-top: 1.2rem; max-width: 1600px; }}
.eyebrow {{ color: {CYAN}; letter-spacing: .22em; font-size: .72rem; font-weight: 700; }}
.hero {{ font-family: 'Barlow Condensed', sans-serif; font-weight: 700; letter-spacing: .035em; font-size: clamp(2.6rem, 5vw, 4.4rem); line-height: .95; margin: .15rem 0 .4rem 0; }}
.subtitle {{ color: {MUTED}; font-size: .96rem; }}
.panel {{ background: linear-gradient(145deg, #141d27, #0e151d); border: 1px solid {LINE}; border-radius: 12px; padding: 16px 18px; }}
.panel-label {{ color: {MUTED}; font-size: .73rem; letter-spacing: .13em; font-weight: 700; }}
.metric-value {{ font-family: 'Barlow Condensed', sans-serif; font-size: 2rem; font-weight: 600; margin-top: .2rem; }}
.metric-note {{ color: {MUTED}; font-size: .76rem; }}
.section-title {{ font-family: 'Barlow Condensed', sans-serif; letter-spacing: .07em; font-size: 1.45rem; font-weight: 600; }}
.status {{ display:inline-block; border:1px solid #3a4b5c; border-radius:999px; padding:4px 9px; color:{CYAN}; font-size:.72rem; letter-spacing:.08em; }}
.small {{ color: {MUTED}; font-size: .8rem; }}
hr {{ border-color: {LINE}; }}
button[kind="primary"] {{ background: {CYAN}; color: #071015; border: none; font-weight: 700; }}
</style>
""", unsafe_allow_html=True)

# ---------- Synthetic Mars-like test environment ----------
N = 62
GRID = np.linspace(-1, 1, N)
X, Y = np.meshgrid(GRID, GRID)

def make_terrain() -> np.ndarray:
    # Procedural, intentionally synthetic terrain: ridges, crater bowls, and small-scale roughness.
    z = (0.20*np.sin(3.0*X + 0.6)*np.cos(2.6*Y)
         + 0.12*np.sin(5.4*X + 1.4*Y)
         + 0.10*np.cos(4.7*Y - 0.8*X))
    craters = [(-0.40, 0.22, 0.19, 0.22), (0.38, -0.31, 0.25, 0.16), (0.10, 0.47, 0.12, 0.12)]
    for cx, cy, r, depth in craters:
        d = np.sqrt((X-cx)**2 + (Y-cy)**2)
        z -= depth*np.exp(-((d/r)**2)*2.2)
        z += depth*0.20*np.exp(-(((d-r*1.18)/(r*.20))**2))
    z += 0.025*np.sin(17*X + 4*Y)*np.cos(14*Y)
    return z

Z = make_terrain()
# A deterministic risk field, not a measured Mars hazard map.
slope_y, slope_x = np.gradient(Z, GRID[1]-GRID[0])
SLOPE = np.sqrt(slope_x**2 + slope_y**2)
rocks = (np.sin(8.7*X + 2.2*Y) * np.cos(7.2*Y - 1.8*X))
ROCK_RISK = np.clip((rocks - 0.22) / 0.75, 0, 1)
DUST_BASE = np.clip(0.50 + 0.24*np.sin(2.8*X + 0.5)*np.cos(2.1*Y) + 0.17*X, 0, 1)

START = (5, 7)
GOAL = (N-7, N-8)


def normalize(a: np.ndarray) -> np.ndarray:
    lo, hi = float(np.nanmin(a)), float(np.nanmax(a))
    return (a - lo) / (hi - lo + 1e-9)

SLOPE_N = normalize(SLOPE)


def build_risk(storm: float, slope_weight: float, dust_weight: float) -> np.ndarray:
    # Storm intensity increases the dust-related planning penalty; slope/rock penalties are terrain-derived.
    dust = np.clip(DUST_BASE * (0.45 + 0.85*storm), 0, 1)
    risk = 0.48*SLOPE_N + 0.30*ROCK_RISK + dust_weight*dust + slope_weight*SLOPE_N
    return np.clip(risk / (0.78 + dust_weight + slope_weight), 0, 1)


def astar(cost: np.ndarray, start: Tuple[int, int], goal: Tuple[int, int], risk_weight: float = 1.0) -> List[Tuple[int, int]]:
    h, w = cost.shape
    pq = [(0.0, start)]
    came: Dict[Tuple[int, int], Tuple[int, int]] = {}
    gscore = {start: 0.0}
    dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    while pq:
        _, cur = heapq.heappop(pq)
        if cur == goal:
            path = [cur]
            while cur in came:
                cur = came[cur]
                path.append(cur)
            return path[::-1]
        for di, dj in dirs:
            ni, nj = cur[0]+di, cur[1]+dj
            if not (0 <= ni < h and 0 <= nj < w):
                continue
            dist = math.sqrt(2) if di and dj else 1.0
            # Risk penalty is integrated into the traversal cost; no hard safety guarantee is implied.
            step = dist * (1.0 + risk_weight * float(cost[ni, nj])**2 * 5.0)
            tentative = gscore[cur] + step
            nxt = (ni, nj)
            if tentative < gscore.get(nxt, float('inf')):
                came[nxt] = cur
                gscore[nxt] = tentative
                heuristic = math.hypot(goal[0]-ni, goal[1]-nj)
                heapq.heappush(pq, (tentative + heuristic, nxt))
    return []


def path_metrics(path: List[Tuple[int, int]], risk: np.ndarray, storm: float, dust_factor: float) -> dict:
    if not path:
        return {"distance": 0, "risk": 1, "energy": 0, "duration": 0}
    distances = [math.hypot(path[i+1][0]-path[i][0], path[i+1][1]-path[i][1]) for i in range(len(path)-1)]
    distance = float(sum(distances)) * 18.0  # illustrative metres per grid unit
    avg_risk = float(np.mean([risk[p] for p in path]))
    # Simplified illustrative energy model. Parameters are not fitted to a specific rover.
    terrain_factor = 1.0 + 0.60*float(np.mean([SLOPE_N[p] for p in path]))
    energy = (distance/100.0) * 18.0 * terrain_factor * (1 + 0.50*storm) / max(0.35, dust_factor)
    duration = distance / max(8.0, 22.0*(1 - 0.35*storm)*(1 - 0.25*avg_risk))
    return {"distance": distance, "risk": avg_risk, "energy": energy, "duration": duration}



def path_xyz(path: List[Tuple[int, int]]):
    xs, ys, zs = [], [], []
    for i, j in path:
        xs.append(float(GRID[j])); ys.append(float(GRID[i])); zs.append(float(Z[i, j]) + 0.012)
    return xs, ys, zs

# ---------- Sidebar controls ----------
st.sidebar.markdown('<div class="eyebrow">MISSION CONFIGURATION</div>', unsafe_allow_html=True)
st.sidebar.markdown("## Scenario controls")
st.sidebar.caption("Adjust assumptions, then compare route strategies.")
storm = st.sidebar.slider("Dust event intensity", 0.0, 1.0, 0.45, 0.05, help="Scenario parameter; not a live forecast.")
dust_factor = st.sidebar.slider("Solar array cleanliness", 0.25, 1.0, 0.72, 0.01, help="1.0 means clean in this simplified model.")
risk_weight = st.sidebar.slider("Hazard aversion", 0.2, 3.0, 1.7, 0.1)
energy_capacity = st.sidebar.slider("Available energy budget (Wh)", 100, 1200, 620, 20)
show_risk = st.sidebar.toggle("Show risk field", value=True)
show_rover = st.sidebar.toggle("Show rover marker", value=True)
st.sidebar.markdown("---")
st.sidebar.markdown("**DATA INTEGRITY**")
st.sidebar.caption("Terrain, dust field and rover telemetry are synthetic demo inputs. NASA references inform the design principles; this prototype is not a NASA model or live mission forecast.")

risk = build_risk(storm, 0.28, 0.30)
short_path = astar(np.zeros_like(risk), START, GOAL, risk_weight=0.0)
safe_path = astar(risk, START, GOAL, risk_weight=risk_weight)
short = path_metrics(short_path, risk, storm, dust_factor)
safe = path_metrics(safe_path, risk, storm, dust_factor)

# ---------- Header ----------
left, right = st.columns([0.75, 0.25], vertical_alignment="center")
with left:
    st.markdown('<div class="eyebrow">PLANETARY EXPLORATION INTELLIGENCE / PROTOTYPE 01</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero">MARS GUARDIAN</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">See the storm before it strikes. Find the safer path. Make every watt count.</div>', unsafe_allow_html=True)
with right:
    st.markdown('<div style="text-align:right"><span class="status">SIMULATION MODE</span><br><br><span class="small">MISSION SECTOR · MG-01<br>ENVIRONMENT · SYNTHETIC TEST SITE</span></div>', unsafe_allow_html=True)
st.markdown("")

# KPI strip
k1,k2,k3,k4 = st.columns(4)
with k1:
    st.markdown(f'<div class="panel"><div class="panel-label">DUST EVENT</div><div class="metric-value" style="color:{AMBER if storm < .7 else RED}">{storm*100:.0f}<span style="font-size:1rem"> / 100</span></div><div class="metric-note">Scenario intensity · not probability</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="panel"><div class="panel-label">ROUTE DISTANCE</div><div class="metric-value">{safe["distance"]:.0f}<span style="font-size:1rem"> m</span></div><div class="metric-note">Risk-aware candidate</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="panel"><div class="panel-label">ESTIMATED ENERGY</div><div class="metric-value" style="color:{RED if safe["energy"] > energy_capacity else GREEN}">{safe["energy"]:.0f}<span style="font-size:1rem"> Wh</span></div><div class="metric-note">Simplified model output</div></div>', unsafe_allow_html=True)
with k4:
    margin = energy_capacity - safe["energy"]
    st.markdown(f'<div class="panel"><div class="panel-label">ENERGY MARGIN</div><div class="metric-value" style="color:{GREEN if margin >= 0 else RED}">{margin:+.0f}<span style="font-size:1rem"> Wh</span></div><div class="metric-note">Budget minus estimate</div></div>', unsafe_allow_html=True)
st.markdown("")

# ---------- Main experience ----------
tab_twin, tab_route, tab_energy, tab_method = st.tabs(["01  /  MARS DIGITAL TWIN", "02  /  ROUTE INTELLIGENCE", "03  /  ENERGY SURVIVAL LAB", "04  /  SCIENCE & LIMITATIONS"])

with tab_twin:
    c1, c2 = st.columns([0.74, 0.26], gap="large")
    with c1:
        st.markdown('<div class="section-title">TERRAIN RECONNAISSANCE</div>', unsafe_allow_html=True)
        st.caption("Procedural Mars-like test terrain · elevation and risk are illustrative, not a mapped real landing site.")
        surf = go.Surface(x=GRID, y=GRID, z=Z, surfacecolor=risk if show_risk else Z,
                          colorscale=[[0,"#171e25"],[0.25,"#6d4334"],[0.55,"#c46a43"],[0.78,"#e5a06a"],[1,"#f2d1a0"]] if not show_risk else [[0,"#183b43"],[0.35,"#4c7b73"],[0.62,"#d9a04e"],[0.82,"#e36d4d"],[1,"#ff5147"]],
                          showscale=True, colorbar=dict(title="Risk" if show_risk else "Elevation", tickfont=dict(color=TEXT), titlefont=dict(color=TEXT)),
                          lighting=dict(ambient=0.42, diffuse=0.82, roughness=0.9, specular=0.12),
                          contours=dict(z=dict(show=False)))
        fig = go.Figure(data=[surf])
        if safe_path:
            px, py, pz = path_xyz(safe_path)
            fig.add_trace(go.Scatter3d(x=px,y=py,z=pz,mode="lines",name="Risk-aware route",line=dict(color=CYAN,width=6)))
        if short_path:
            px, py, pz = path_xyz(short_path)
            fig.add_trace(go.Scatter3d(x=px,y=py,z=pz,mode="lines",name="Shortest route",line=dict(color="#F4E7D0",width=3,dash="dash")))
        for p, label, color in [(START,"ROVER",CYAN),(GOAL,"TARGET",AMBER)]:
            i,j=p
            fig.add_trace(go.Scatter3d(x=[GRID[j]],y=[GRID[i]],z=[Z[i,j]+.025],mode="markers+text",text=[label],textposition="top center",name=label,marker=dict(size=7,color=color,line=dict(color="#ffffff",width=1))))
        if show_rover and safe_path:
            p=safe_path[min(len(safe_path)-1, max(0, int(len(safe_path)*0.22)))]
            i,j=p
            fig.add_trace(go.Scatter3d(x=[GRID[j]],y=[GRID[i]],z=[Z[i,j]+.035],mode="markers",name="Rover position (simulated)",marker=dict(size=9,color="#ffffff",symbol="diamond",line=dict(color=CYAN,width=3))))
        fig.update_layout(height=570, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT), legend=dict(bgcolor="rgba(8,12,17,.72)",bordercolor=LINE,borderwidth=1), scene=dict(bgcolor="rgba(0,0,0,0)", xaxis=dict(title="East / West",showbackground=False,gridcolor="#27323d",zerolinecolor=LINE), yaxis=dict(title="North / South",showbackground=False,gridcolor="#27323d",zerolinecolor=LINE), zaxis=dict(title="Relative elevation",showbackground=False,gridcolor="#27323d",zerolinecolor=LINE), camera=dict(eye=dict(x=1.55,y=1.55,z=1.0))))
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "scrollZoom": True})
    with c2:
        st.markdown('<div class="section-title">MISSION TELEMETRY</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="panel"><div class="panel-label">TARGET ACQUISITION</div><div style="font-size:1.15rem;font-weight:700;margin-top:7px">SCIENCE SITE / B-07</div><div class="small">Synthetic waypoint · sector MG-01</div><hr><div class="panel-label">TERRAIN STATE</div><div style="margin-top:8px">Slope index <b>{np.mean(SLOPE_N):.2f}</b></div><div style="margin-top:8px">Dust scenario <b>{storm*100:.0f}/100</b></div><div style="margin-top:8px">Array cleanliness <b>{dust_factor*100:.0f}%</b></div></div>', unsafe_allow_html=True)
        st.markdown("")
        if safe["energy"] > energy_capacity:
            st.error("ENERGY BUDGET EXCEEDED — shorten the traverse, reduce activities, or choose a lower-cost route.")
        elif safe["energy"] > energy_capacity*0.8:
            st.warning("LOW ENERGY MARGIN — consider a conservative plan and preserve contingency reserve.")
        else:
            st.success("ENERGY MARGIN AVAILABLE — reserve remains under this model's assumptions.")
        st.markdown('<div class="panel"><div class="panel-label">OPERATOR NOTE</div><p style="margin:.5rem 0 0 0">A visually attractive route is not automatically the safest. Review the risk field, energy estimate, and assumptions before accepting a plan.</p></div>', unsafe_allow_html=True)

with tab_route:
    st.markdown('<div class="section-title">TWO ROUTES. TWO DIFFERENT TRADE-OFFS.</div>', unsafe_allow_html=True)
    st.write("The planner compares a distance-focused route with a route that penalizes terrain and dust-related risk. Neither route is certified safe; the weights are adjustable planning assumptions.")
    a,b = st.columns(2, gap="large")
    with a:
        st.markdown("#### SHORTEST-PATH CANDIDATE")
        st.metric("Estimated distance", f"{short['distance']:.0f} m")
        st.metric("Mean path risk index", f"{short['risk']:.2f} / 1.00")
        st.metric("Estimated energy", f"{short['energy']:.0f} Wh")
        st.caption("Prioritizes distance. May cross terrain with a higher risk score.")
    with b:
        st.markdown("#### RISK-AWARE CANDIDATE")
        st.metric("Estimated distance", f"{safe['distance']:.0f} m", delta=f"{safe['distance']-short['distance']:+.0f} m vs shortest", delta_color="inverse")
        st.metric("Mean path risk index", f"{safe['risk']:.2f} / 1.00", delta=f"{safe['risk']-short['risk']:+.2f} vs shortest", delta_color="inverse")
        st.metric("Estimated energy", f"{safe['energy']:.0f} Wh", delta=f"{safe['energy']-short['energy']:+.0f} Wh vs shortest", delta_color="inverse")
        st.caption("Trades distance for lower modeled risk when the cost field makes that worthwhile.")
    st.markdown("---")
    st.markdown("#### Operator decision")
    decision = st.radio("What should the mission prioritize?", ["Reduce modeled hazard exposure", "Minimize distance", "Preserve energy reserve"], horizontal=True, label_visibility="collapsed")
    if decision == "Reduce modeled hazard exposure":
        st.info("Recommended experiment: raise Hazard aversion in the sidebar, then observe how the route and energy estimate change.")
    elif decision == "Minimize distance":
        st.info("Recommended experiment: compare the dashed shortest route against the cyan risk-aware route, then inspect the risk-index difference.")
    else:
        st.info("Recommended experiment: increase the energy reserve requirement by lowering the available energy budget, then test a lower-intensity dust scenario or cleaner-array assumption.")

with tab_energy:
    st.markdown('<div class="section-title">ENERGY IS A MISSION RESOURCE</div>', unsafe_allow_html=True)
    st.write("This demonstrator uses a transparent, deliberately simplified model. It illustrates how route length, terrain, dust scenario, and assumed array cleanliness can interact; it is not fitted to a flight rover.")
    col1,col2 = st.columns([0.6,0.4], gap="large")
    with col1:
        labels = ["Shortest-path candidate", "Risk-aware candidate"]
        energies = [short["energy"], safe["energy"]]
        fig2 = go.Figure(go.Bar(x=labels, y=energies, marker_color=["#A5B2C0", CYAN], text=[f"{v:.0f} Wh" for v in energies], textposition="outside"))
        fig2.add_hline(y=energy_capacity, line_dash="dash", line_color=RED, annotation_text="Energy budget", annotation_font_color=RED)
        fig2.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color=TEXT),yaxis=dict(title="Illustrative energy (Wh)",gridcolor=LINE,zerolinecolor=LINE),xaxis=dict(gridcolor=LINE),margin=dict(l=10,r=10,t=30,b=10),showlegend=False)
        st.plotly_chart(fig2,use_container_width=True,config={"displaylogo":False})
    with col2:
        st.markdown("#### What changes the estimate?")
        st.markdown(f"- **Route distance:** {safe['distance']:.0f} m for the risk-aware candidate")
        st.markdown(f"- **Dust-event intensity:** {storm:.2f} (user-set scenario)")
        st.markdown(f"- **Array cleanliness:** {dust_factor:.0%} (user-set assumption)")
        st.markdown(f"- **Terrain multiplier:** {1 + .60*np.mean([SLOPE_N[p] for p in safe_path]):.2f} on the selected route")
        st.markdown("---")
        if margin < 0:
            st.error(f"Estimated shortfall: {-margin:.0f} Wh. The mission plan needs revision under these assumptions.")
        else:
            st.success(f"Estimated remaining budget: {margin:.0f} Wh. This is not a guaranteed operational reserve.")
    st.markdown("#### Scenario challenge")
    st.write("Try a high dust event with lower array cleanliness. Then compare the same route under a calmer scenario. Ask: does the safest route remain feasible within the energy budget?")

with tab_method:
    st.markdown('<div class="section-title">SCIENCE TRACEABILITY</div>', unsafe_allow_html=True)
    st.write("The design follows published NASA/JPL concepts, but the present demo data and equations are illustrative. References below are starting points for a defensible student research project.")
    st.markdown("**Navigation and hazard-aware planning**")
    st.markdown("- NASA/JPL describes rover navigation using stereo vision, terrain assessment, obstacle avoidance, and global path planning. [MER Surface Navigation](https://robotics.jpl.nasa.gov/what-we-do/flight-projects/mars-exploration-rovers/surface-navigation/)")
    st.markdown("- NASA Technical Reports Server: *Improved Path Planning Onboard the Mars Exploration Rovers* discusses combining local hazard avoidance with global path planning. [Read the technical brief](https://ntrs.nasa.gov/citations/20100010963)")
    st.markdown("- JPL's next-generation AutoNav concept explicitly combines terrain classification with risk-aware path planning. [JPL research task](https://www-robotics.jpl.nasa.gov/what-we-do/research-tasks/next-gen-autonav-concept/)")
    st.markdown("**Dust and power**")
    st.markdown("- NASA NTRS documents how MER solar-array output was used to estimate dust deposition and cleaning events. [Power Operations of the Mars Exploration Rovers](https://ntrs.nasa.gov/citations/20230007029)")
    st.markdown("- NASA NTRS describes multiple factors affecting solar-array performance, including solar angle, rover tilt, atmospheric opacity, and dust accumulation. [Dust Accumulation and Solar Panel Array Performance](https://ntrs.nasa.gov/citations/20050186821)")
    st.markdown("**Terrain datasets for a future evidence-based version**")
    st.markdown("- NASA's public HiRISE DTM dataset includes derived Digital Terrain Models and corresponding orthoimages. [NASA Open Data Portal](https://data.nasa.gov/dataset/mro-mars-high-resolution-imaging-science-experiment-dtm-v1-0)")
    st.markdown("- NASA's API portal describes available APIs; verify current availability and mission scope before building a dependency. [NASA APIs](https://api.nasa.gov/)")
    st.markdown("---")
    st.markdown("#### Current limitations — disclose these in the competition demo")
    st.markdown("1. The 3D terrain and dust field are generated procedurally; they are not a georeferenced Mars site.\n2. Dust intensity is a scenario control, not a probability or forecast.\n3. The energy equation is a transparent placeholder, not a validated rover power model.\n4. The A* planner optimizes a designed cost field; its output is not a guarantee of safety.\n5. No live NASA telemetry is fetched by this version.\n6. The interface should be validated against selected published datasets and baselines before claiming predictive accuracy.")
    st.markdown("#### Recommended validation plan")
    st.markdown("- Replace synthetic terrain with a documented DEM/DTM and record its product ID, resolution, coordinate system, and license.\n- Compare route results with shortest-path and risk-blind baselines.\n- Run fixed, repeatable scenarios and report distance, mean risk index, energy estimate, runtime, and failure cases.\n- If a real dataset cannot support a variable, mark it as a modeled assumption rather than a measured input.")

st.markdown("---")
st.markdown('<div class="small">MARS GUARDIAN · Student research prototype · Not an official NASA product · Synthetic scenario outputs must not be interpreted as real mission guidance.</div>', unsafe_allow_html=True)
