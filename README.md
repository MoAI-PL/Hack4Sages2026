ExoStress Twin: A High-Fidelity Digital Twin for TRAPPIST-1e Habitability Exploration
Interactive real‑time simulation of tidally locked exoplanet climate, hydrology, and biosignatures.
Developed for the International Digital Twins in Astrobiology Hackathon (HACK‑4‑SAGES 2026).

Version: 1.0.0 (Hackathon release)
Date: March 12, 2026
Authors: Jan Domański, Sandra Zaremba, Kamila Bąk


📋 Table of Contents
Scientific Framework
1.1 Atmospheric Dynamics
1.2 Hydrological Cycle
1.3 Stellar‑Planet Interaction
1.4 Validation

Biosignature Logic

Technology Stack & XAI
3.1 Explainable AI Copilot
3.2 Numerical Stability
3.3 Data Integrity

Assumptions & Known Limitations

Project Structure

Installation & Usage

Credits & Transparency



🔬 1. Scientific Framework & Physics Engine
Research Question:
How do stellar flares impact the stability of the terminator habitable zone on tidally locked exoplanets, and can methane-based biosignatures persist under such dynamic conditions?

Project Context:
This project is a direct implementation of the "Tidally Locked Planet" challenge proposed in the HACK‑4‑SAGES materials (Section 3.2, pp. 6‑7). We extend the base requirements with a flare simulation module and an XAI Copilot.

What Makes This a Digital Twin:
ExoStress Twin functions as a true digital twin by maintaining a consistent virtual representation of TRAPPIST‑1e that evolves in real time based on user inputs, while preserving mass and energy conservation laws. This allows researchers to experiment with "what‑if" scenarios in a physically coherent framework.

The core of ExoStress Twin is a custom‑built 2D Energy Balance Model (EBM). It bridges the gap between simple 1D models and complex 3D simulations, delivering immediate feedback for parametric exploration.

1.1. Atmospheric Dynamics (Zonal Advection)
TRAPPIST‑1e is tidally locked, creating permanent day and night hemispheres.

Super‑rotation simulation: We implement a numerical “equatorial jet” parameterization. Heat is actively transported eastward using np.roll shifts, recreating the asymmetric terminator and “hot‑spot shift” described in modern astrophysical literature (Showman & Polvani, 2011).

Thermal diffusion: Atmospheric heat redistribution follows a 2D diffusion equation. Users can manipulate the diffusion coefficient ($D$) to simulate atmospheres ranging from thin, Mars‑like envelopes to thick, Venus‑style insulation.

1.2. Hydrological Cycle (Mass Conservation)
Water is treated as a closed‑loop system – a critical requirement for physical validity.

Bulk transport closure: We mathematically guarantee 100% water mass conservation. Water evaporates on the dayside, is transported via parameterized winds, and precipitates on the nightside.

Phase inventory tracking:

Liquid: Maintained within the “habitable zone” ($0,^\circ\mathrm{C} < T < 100,^\circ\mathrm{C}$).

Ice (ice‑albedo feedback): When temperature drops below freezing and water is present, local albedo increases to 0.75. This triggers a cooling loop that can lead to a permanent “Snowball Earth” state.

Gas: High temperatures trigger evaporation. Increased water vapour acts as a greenhouse gas, allowing users to observe the onset of a runaway greenhouse effect.

1.3. Stellar‑Planet Interaction (Flare Events)
M‑dwarfs like TRAPPIST‑1 are notoriously active. Our engine phenomenologically simulates:

Atmospheric stripping: High‑energy flare particles erode the atmosphere. This is modelled as a temporary reduction in greenhouse efficiency and heat diffusion, scaled by the planet’s relative gravity ($g_{\text{rel}}$).

UV photolysis: Stellar flares trigger rapid destruction of atmospheric methane (CH₄), demonstrating the transient nature of biosignatures on planets around active stars.

1.4. Validation
Terminator temperature: The baseline Earth‑like scenario (albedo = 0.3, diffusion = 0.05) produces a terminator temperature of ~15 °C, consistent with 1D energy balance estimates for TRAPPIST‑1e (see Turbet et al. 2016).

Snowball transition: The ice‑albedo runaway occurs at albedo > 0.6, matching theoretical expectations for global glaciation thresholds.

Flare response: Post‑flare methane collapse follows first‑order kinetics, qualitatively reproducing the photolytic destruction expected under enhanced UV flux.


🧪 2. Biosignature Logic: The Methane Proxy
ExoStress Twin uses biogenic methane as a primary proxy for biological activity.

The “sweet spot” heuristic: CH₄ production is tied to surface habitability, specifically focusing on the terminator zone where liquid water is stable.

Sub‑glacial methanogenesis: Inspired by Rugheimer et al. (2015), the model accounts for methanogenic activity under global ice sheets. This justifies why a planet in a “Snowball” state might still exhibit detectable biosignatures.

Methane decay: A first‑order photolysis term removes CH₄, with a loss rate that increases during flare events.


🤖 3. Technology Stack & XAI Integration
3.1. Explainable AI (XAI) Copilot
We integrated a deterministic XAI Copilot to assist researchers. Unlike generic LLMs, this tool:

Reads live telemetry: habitability fractions, phase shifts, energy flux.

Generates insights: provides human‑readable explanations of complex climate feedbacks (e.g., why a planet entered a stable equilibrium or a drifting state).

Guarantees stability: rule‑based responses avoid the unpredictability of external APIs during live demonstrations. The frontend is ready to swap in a true LLM endpoint with one line of code.

3.2. Numerical Stability (CFL Condition)
To keep the simulation robust under extreme user interactions (e.g., 15× flares), we implement the Courant‑Friedrichs‑Lewy (CFL) condition. A dynamic time‑stepping mechanism subdivides each main step to prevent numerical divergence in the diffusion calculations.

3.3. Data Integrity
NASA Exoplanet Archive: Core parameters (mass, radius, luminosity) are dynamically read from the archive (local cache included).

Primary reference: Our baseline parameters for the TRAPPIST‑1 system follow the refined transit‑timing and physical data from Agol et al. (2021).

Fallback: If CSV files are missing, the code falls back to hard‑coded Agol et al. values, ensuring the simulation always runs.


⚠️ 4. Assumptions & Known Limitations
The project was built in 48 hours for a hackathon. Below are the conscious engineering and scientific trade‑offs.

4.1. Atmospheric Model: 2D EBM vs. 3D GCM
Assumption: A 2D Energy Balance Model with advection parameterization is used instead of a full General Circulation Model (GCM).

Why: GCMs require supercomputers and hours of simulation time. Our goal is real‑time interactivity and parametric exploration.

Consequences: No vertical atmosphere profile, clouds, or realistic 3D circulation. Results are sufficient for conceptual habitability studies but not for precise forecasting.

4.2. Water Transport: “Teleportation” Instead of Full Dynamics
Assumption: Water is transported from the dayside to the nightside using np.roll (a 180° longitudinal shift).

Why: A 2D model lacks a vertical dimension to simulate moisture advection. np.roll guarantees mass conservation (100% of water stays in the system) and mimics the net effect – transport to the opposite hemisphere.

Consequences: No clouds, no gradual transport, idealised path. Water condenses only upon arrival, which is an acceptable approximation for studying bulk phase balances.

4.3. Methane Biosignature: Heuristic Instead of Chemistry
Assumption: CH₄ production scales with the area of the “sweet spot” (0–50°C, liquid water present). Additional sub‑glacial production occurs in Snowball states. Decay follows first‑order photolysis.

Why: A full biogeochemical model would require data that do not exist for extraterrestrial life. The heuristic allows us to explore conditions favourable to biosignatures without pretending to know alien biochemistry.

Consequences: Methane values (scaled to 2500 ppm in the UI) are abstract. They should be interpreted as a proxy for biological activity, not as real concentrations.

4.4. Flare Events: Parameterized Atmospheric Loss
Assumption: A flare reduces the effective diffusion and greenhouse coefficients, simulating atmospheric erosion.

Why: The 2D model has no vertical axis, so we cannot directly model atmospheric escape. Reducing diff_coeff and greenhouse parameterises the loss of column density.

Consequences: Atmospheric loss is simulated indirectly, but scaling by the planet’s gravity ($g_{\text{rel}}$) adds physical consistency.

4.5. Numerical Stability: Simplified CFL
Assumption: A constant grid_spacing = 2.0 (dimensionless) is used in the CFL condition.

Why: In a model without physical length units, this constant is sufficient to maintain stability across the range of diffusion coefficients.

Consequences: The time step is not physically calibrated, but numerically it guarantees that the solution never blows up.

4.6. Ice Albedo: Fixed Value
Assumption: Ice albedo is fixed at 0.75 wherever temperature < 0°C and water is present.

Why: In reality, ice albedo depends on temperature, thickness, and impurities. A fixed value is a simplification that still captures the essential ice‑albedo feedback.

Consequences: Subtle variations are lost, but the main positive‑feedback mechanism is preserved.

4.7. XAI Copilot: Rule‑Based Instead of LLM
Assumption: Deterministic rules are used instead of an external LLM API.

Why: To guarantee 100% stability during live demos and avoid timeouts or rate limits. The frontend is designed to accept a true LLM endpoint in the future.

Consequences: Responses are less “creative”, but they are fully explainable – hence the “XAI” label.


📂 5. Project Structure
exostress-twin/
├── main.py                 # FastAPI backend with the 2D‑EBM physics engine
├── script.js               # Frontend logic for real‑time Plotly.js visualisations
├── index.html              # Dashboard UI with scientific glassmorphism styling
├── style.css               # All styling (SpaceX‑inspired, dark theme)
├── star_parameters/        # Local cache of stellar data (TRAPPIST‑1)
├── planet_parameters/      # Local cache of planetary data (TRAPPIST‑1e)
└── requirements.txt        # Python dependencies
Key dependencies (requirements.txt):

fastapi==0.115.0
uvicorn==0.30.1
numpy==1.26.0
pandas==2.1.0
python-multipart==0.0.6


🛠️ 6. Installation & Usage
bash
# Clone the repository
git clone https://github.com/your-username/exostress-twin.git
cd exostress-twin

# Install Python dependencies
pip install -r requirements.txt

# Run the server (development mode with auto‑reload)
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
Then open your browser at http://localhost:8000.

Requirements: Python 3.9+, a modern browser (Chrome, Firefox, Edge).


🎬 7. Credits & Transparency
In compliance with HACK‑4‑SAGES 2026 guidelines:

Visuals: Intro and outro cinematic sequences were generated using Vidu AI.

Voiceover: Narrative audio was generated via ElevenLabs AI.

Data sources:

NASA Exoplanet Archive (https://exoplanetarchive.ipac.caltech.edu)

Agol, E. et al. (2021) – Refining the Transit‑timing and Photometric Analysis of TRAPPIST‑1: Masses, Radii, Densities, Dynamics, and Ephemerides – The Planetary Science Journal.

Mentors & organisers: We thank the HACK‑4‑SAGES team and our assigned mentor for invaluable guidance.



ExoStress Twin – Because habitability is not just about location, it’s about resilience.
