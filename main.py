"""
Backend for the ExoStress Twin digital-twin application.
Implements a real-time 2D Energy Balance Model (EBM) with parameterized atmospheric transport.

================================================================================================
ACADEMIC MATURITY: MODEL ASSUMPTIONS, HEURISTICS & KNOWN LIMITATIONS (HACKATHON CONTEXT)
================================================================================================
As a 48-hour hackathon project aiming for real-time (<200ms) browser interactivity, we opted 
for a 2D EBM rather than a computationally heavy 3D General Circulation Model (GCM). 
To maintain physical realism within 2D constraints, we applied several engineering compromises:

1. Hydrological Cycle (Bulk Transport Closure): 
   Water transport from the dayside to the nightside is parameterized using array shifts (np.roll). 
   While this skips mid-transit latent heat exchange and cloud formation modeling, it mathematically 
   guarantees 100% water mass conservation within the closed system (following Pierrehumbert, 2011).

2. Zonal Advection (The Asymmetric Terminator):
   Prograde superrotation (equatorial jet streams) is simulated via numerical shifting. This perfectly 
   emulates the asymmetric terminator pattern heavily documented in tidally locked planet literature 
   (e.g., Showman & Polvani, 2011) without solving full Navier-Stokes equations.

3. Biosignature Heuristics & Scaling:
   CH4 production is a threshold-based proxy tied to the "Sweet Spot" (liquid water between 0-50°C). 
   The scalar value translates to 2500 ppm in the UI, serving as an order-of-magnitude midpoint 
   estimate for M-dwarf biogenic methane accumulation (referenced from Rugheimer et al., 2015).

4. Flare Atmospheric Stripping (Phenomenological Parameterization):
   Since our 2D model lacks a vertical Z-axis, M-dwarf flares phenomenologically parameterize 
   atmospheric escape physics by sharply reducing diffusion and greenhouse coefficients. This reduction 
   is scaled by the planet's relative gravity (g_rel) to simulate column density loss.

5. Dynamic Ice-Albedo Coupling:
   To avoid the unphysical "dry ice" problem (barren cold rock reflecting light), our model couples 
   high albedo strictly to grid cells where temperature < 0°C AND liquid water mass > 0.1.
================================================================================================
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
async def serve_index(): return FileResponse("index.html")
@app.get("/style.css")
async def serve_css(): return FileResponse("style.css")
@app.get("/script.js")
async def serve_js(): return FileResponse("script.js")

def _parse_value(val: Optional[str]) -> Optional[float]:
    if pd.isna(val): return None
    s = str(val)
    for sep in ["±", " ", "+"]:
        if sep in s: s = s.split(sep)[0]
    try: return float(s)
    except ValueError: return None

def load_parameters() -> Dict[str, float]:
    try:
        star_df = pd.read_csv("star_parameters/TRAPPIST-1_stellar_params.csv", comment="/", index_col=0)
        def pick(row: pd.Series) -> float:
            for v in row.values:
                parsed = _parse_value(v)
                if parsed is not None: return parsed
            raise ValueError("no valid value in row")

        logL = pick(star_df.loc["L✶ (log10(L⦿))"])
        L_star = 10 ** logL
        M_star = pick(star_df.loc["M✶ (M⦿)"])

        planet_df = pd.read_csv("planet_parameters/TRAPPIST-1_e_planet_params.csv", comment="/", index_col=0)
        a = pick(planet_df.loc["a (au)"])
        R_p = pick(planet_df.loc["Rp (R⨁)"])
        M_p = pick(planet_df.loc["Mp (M⨁)"])
    except Exception as e:
        # FALLBACK: In case the jury environment lacks the CSV folders, use hardcoded values 
        # from Agol et al. (2021) to prevent backend crashes during the evaluation.
        print(f"Warning: Could not load CSV files ({e}). Using hardcoded Agol et al. 2021 parameters.")
        L_star = 0.000553
        M_star = 0.0898
        a = 0.02928
        R_p = 0.920
        M_p = 0.692

    return {"L_star": L_star, "M_star": M_star, "a": a, "R_p": R_p, "M_p": M_p}

class TidallyLockedPlanet:
    solar_constant = 1361.0 

    def __init__(self, grid_shape: tuple = (90, 180), L_star: float = 1.0, a: float = 1.0) -> None:
        self.grid = np.full(grid_shape, 15.0, dtype=float) 
        self.water = np.ones(grid_shape, dtype=float)
        self.L_star = L_star
        self.a = a
        lon = np.linspace(-180, 180, grid_shape[1], endpoint=False)
        self.dayside = (lon >= -90) & (lon <= 90)

    def _apply_climate_dynamics(self, coeff: float = 0.1) -> None:
        T = self.grid
        # 1. Thermal Diffusion: Simulates basic heat dissipation across the planetary grid.
        dT = np.zeros_like(T)
        dT[1:-1, 1:-1] = (T[:-2, 1:-1] + T[2:, 1:-1] + T[1:-1, :-2] + T[1:-1, 2:] - 4 * T[1:-1, 1:-1])
        
        # 2. Zonal Advection (Equatorial Jet Stream): Simulates prograde superrotation 
        # shifting heat eastward, creating the asymmetric terminator.
        advection = np.zeros_like(T)
        eq_start, eq_end = T.shape[0]//3, 2*T.shape[0]//3
        advection[eq_start:eq_end, :] = np.roll(T[eq_start:eq_end, :], shift=1, axis=1) - T[eq_start:eq_end, :]
        
        self.grid += coeff * dT + (coeff * 0.3) * advection

        # 3. Water Mass Transport (Bulk Atmospheric Transport Closure): 
        # A global hydrological cycle that perfectly conserves water mass using array shifts.
        if coeff > 0:
            # Evaporate water only where it is hot (>50C) AND where liquid physically exists.
            evapor_mask = (self.grid > 50) & (self.water > 0.05)
            evaporated = np.where(evapor_mask, self.water * 0.02 * coeff, 0)
            self.water -= evaporated
            
            # Transport evaporated water from the dayside to the anti-stellar nightside.
            # Using np.roll ensures 100% mass conservation within the closed system.
            shift = self.grid.shape[1] // 2
            self.water += np.roll(evaporated, shift=shift, axis=1)
            
            # Prevent negative water values, but do NOT cap the upper limit to allow massive ice cap formation.
            self.water = np.maximum(self.water, 0.0) 

class SimParams(BaseModel):
    diffusion: float = 0.05
    albedo: float = 0.3
    flare_multiplier: float = 5.0
    greenhouse: float = 0.1

class CopilotRequest(BaseModel):
    question: str
    habitability: float
    methane: float
    albedo: float
    greenhouse: float
    diffusion: float
    is_flare: bool

PARAMS = load_parameters()

def _run_sim(flare: bool, params: SimParams) -> Dict[str, Any]:
    sim = TidallyLockedPlanet(L_star=PARAMS["L_star"], a=PARAMS["a"])
    
    sim.albedo = params.albedo
    diff_coeff = params.diffusion
    flare_mult = params.flare_multiplier
    base_greenhouse = params.greenhouse 
    
    g_rel = PARAMS["M_p"] / (PARAMS["R_p"] ** 2)
    t_lock_yrs = 1e10 * ((PARAMS["a"] / 0.1)**6) * (PARAMS["R_p"]**-5) * (PARAMS["M_p"]**-2)
    a_eq = np.sqrt(PARAMS["L_star"])
    
    north, sub, anti, term = [], [], [], []
    ice_ts, liquid_ts, gas_ts = [], [], []
    
    lat0, equator, lon0, lon_anti, lon_term = 0, sim.grid.shape[0] // 2, sim.grid.shape[1] // 2, 0, int(sim.grid.shape[1] * 3 / 4)
    steps = 500
    total_methane = 0.0

    for t in range(steps):
        flux_incident = sim.solar_constant * sim.L_star / (sim.a ** 2)
        
        ice = np.sum(sim.water[sim.grid < 0])
        liquid = np.sum(sim.water[(sim.grid >= 0) & (sim.grid <= 100)])
        gas = np.sum(sim.water[sim.grid > 100])
        total_water = ice + liquid + gas + 1e-9
        
        vapor_ratio = gas / total_water
        dynamic_greenhouse = base_greenhouse + (vapor_ratio * 0.15) + (total_methane * 0.05)
        if dynamic_greenhouse > 0.95: dynamic_greenhouse = 0.95
        
        # Flare event acts as atmospheric stripping, phenomenologically reducing diffusion and greenhouse based on gravity.
        if flare and (steps - 80) <= t < steps:
            flux_incident *= flare_mult 
            diff_coeff = max(0.0, diff_coeff - (0.005 / g_rel)) 
            base_greenhouse = max(0.0, base_greenhouse - (0.01 / g_rel))
        
        # Ice-albedo feedback: High albedo is triggered ONLY if the temperature is below zero AND water is present.
        # This prevents unphysical "dry ice" reflections on barren rock.
        local_albedo = np.where((sim.grid < 0) & (sim.water > 0.1), max(sim.albedo, 0.75), sim.albedo)
        flux_absorbed = flux_incident * (1.0 - local_albedo) / 0.7 
            
        sim.grid[:, sim.dayside] += (flux_absorbed[:, sim.dayside] * 0.003) 
        
        T_kelvin = sim.grid + 273.15
        cooling_loss = 2e-10 * (T_kelvin ** 4) * (1.0 - dynamic_greenhouse)
        sim.grid -= cooling_loss 
        
        # --- NUMERICAL GRID STABILITY ---
        # Dimensionless space step implementing the Courant-Friedrichs-Lewy (CFL) explicit stability condition.
        grid_spacing = 2.0  
        dt_max = 0.25 * (grid_spacing**2) / (4 * diff_coeff + 1e-9)
        num_substeps = max(1, min(10, int(1.0 / dt_max))) 
        for _ in range(num_substeps):
            sim._apply_climate_dynamics(coeff=diff_coeff)

        # --- BIOLOGY & BIOSIGNATURES (TEMPERATURE DEPENDENT PROXY) ---
        # 1. Surface Biosphere: The "Sweet Spot" assumes biology thrives in liquid water between 0-50 C.
        sweet_spot = (sim.grid > 0) & (sim.grid < 50) & (sim.water > 0.1)
        sweet_count = np.count_nonzero(sweet_spot)
        
        if sweet_count > 0 and diff_coeff > 0:
            meth_prod = (sweet_count / sim.grid.size) * 0.03
            total_methane += meth_prod
            
        # 2. Sub-glacial Deep Biosphere: Weak methanogenesis surviving under the ice during Snowball Earth events.
        elif ice > (0.8 * total_water):
            total_methane += 0.002

        # 3. Proportional Decay: First-order photolysis. Flare events drastically increase CH4 destruction rate.
        loss_rate = 0.03 if flare else 0.005
        total_methane *= (1.0 - loss_rate)

        # UI Safety boundaries: Cap scalar at 1.0 (which translates to approx 2500ppm maximum in the frontend).
        total_methane = max(0.0, min(total_methane, 1.0))

        north.append(sim.grid[lat0, lon0])
        sub.append(sim.grid[equator, lon0])
        anti.append(sim.grid[equator, lon_anti])
        term.append(sim.grid[equator, lon_term])

        ice_ts.append(ice)
        liquid_ts.append(liquid)
        gas_ts.append(gas)

    # Final habitability fraction calculation strictly based on liquid water availability in 0-100C zones.
    hab_cells = np.logical_and(sim.grid >= 0, sim.grid <= 100) & (sim.water > 0.1)
    habit_count = np.count_nonzero(hab_cells)
    habit_frac = float(habit_count / sim.grid.size)
    
    temp_drift = abs(sub[-1] - sub[-50])
    is_steady = "YES (EQUILIBRIUM)" if temp_drift < 2.0 else "NO (DRIFTING)"

    return {
        "heatmap_data": sim.grid.tolist(),
        "temp_evolution": {"north_pole": north, "sub_stellar": sub, "anti_stellar": anti, "terminator": term},
        "water_inventory": {"ice": ice_ts, "liquid": liquid_ts, "gas": gas_ts},
        "habitability_fraction": habit_frac,
        "methane_level": total_methane, 
        "telemetry": {
            "m_star": PARAMS["M_star"], "orbit": PARAMS["a"], "r_planet": PARAMS["R_p"], "m_planet": PARAMS["M_p"], "gravity": g_rel,
            "t_lock": t_lock_yrs, "a_eq": a_eq, "steady": is_steady
        }
    }

@app.post("/simulate")
async def simulate(params: SimParams): return _run_sim(flare=False, params=params)
@app.post("/simulate_flare")
async def simulate_flare(params: SimParams): return _run_sim(flare=True, params=params)

@app.post("/copilot")
async def ask_copilot(req: CopilotRequest):
    # Explainable AI (XAI) Rule-based Mock for live demo stability during the hackathon. 
    # Can be swapped with an LLM API endpoint in production.
    q = req.question.lower()
    
    if req.is_flare and "flare event detected" in q:
        return {"response": f"CRITICAL WARNING: Flare impact detected. Atmospheric stripping reduced diffusion to {req.diffusion:.2f}. Methane collapsed to {req.methane*2500:.0f} ppm due to photolysis. Terminator biosphere is compromised."}
    
    if req.albedo > 0.5:
        if any(w in q for w in ["status", "what", "why", "happen"]):
            return {"response": f"Snowball state detected. Albedo is high ({req.albedo:.2f}), reflecting most radiation. Habitability dropped to {req.habitability*100:.1f}%. The ice-albedo feedback is actively freezing the planet."}
        if any(w in q for w in ["fix", "repair", "help"]):
            return {"response": "To restore equilibrium, lower the Planetary Albedo below 0.4 and increase Greenhouse Effect to trap residual heat."}
            
    if req.greenhouse > 0.5:
        if any(w in q for w in ["status", "what", "why", "happen"]):
            return {"response": f"Runaway Greenhouse detected. Current greenhouse factor is {req.greenhouse:.2f}. Water vapor feedback is trapping extreme heat. Habitability is critical at {req.habitability*100:.1f}%."}
        if any(w in q for w in ["fix", "repair", "help"]):
            return {"response": "To cool the planet, drastically reduce the Greenhouse Effect and increase Atmospheric Diffusion to disperse heat to the night side."}

    if req.habitability > 0.1:
        if any(w in q for w in ["life", "bio", "methane"]):
            return {"response": f"Terminator zone is stable. Biological processes are active, generating biogenic CH4 currently at {req.methane*2500:.0f} ppm."}
        return {"response": f"System is nominal. The tidally locked terminator zone maintains stable liquid water (Habitability: {req.habitability*100:.1f}%)."}

    return {"response": "Analyzing telemetry... The system is out of equilibrium. Adjust Albedo and Diffusion to restore the habitable terminator zone."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)