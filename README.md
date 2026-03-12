
# ExoStress Twin: A High-Fidelity Digital Twin for TRAPPIST-1e Habitability Exploration

**Interactive real-time simulation of tidally locked exoplanet climate, hydrology, and biosignatures.**  
Developed for the *International Digital Twins in Astrobiology Hackathon (HACK-4-SAGES 2026)*.

**Version:** 1.0.0 (Hackathon release)  
**Date:** March 12, 2026  
**Authors:** [Jan Domański](https://github.com/jaaneeczek), [Sandra Zaremba](https://github.com/saska005), [Kamila Bąk](https://github.com/sehunek)

[![Hackathon](https://img.shields.io/badge/HACK--4--SAGES-2026-blueviolet)](https://hack-4-sages.org)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-backend-green)](https://fastapi.tiangolo.com)
[![Plotly](https://img.shields.io/badge/Plotly.js-visualization-3f4f75)](https://plotly.com)
<img width="2335" height="1300" alt="image" src="https://github.com/user-attachments/assets/6ef319a7-fae7-4fbd-96eb-3371c9937a5d" />

---

# 📋 Table of Contents

1. [Scientific Framework](#-1-scientific-framework--physics-engine)  
   1.1 [Atmospheric Dynamics](#11-atmospheric-dynamics-zonal-advection)  
   1.2 [Hydrological Cycle](#12-hydrological-cycle-mass-conservation)  
   1.3 [Stellar-Planet Interaction](#13-stellar-planet-interaction-flare-events)  
   1.4 [Validation](#14-validation)  

2. [Biosignature Logic](#-2-biosignature-logic-the-methane-proxy)  

3. [Technology Stack & XAI](#-3-technology-stack--xai-integration)  
   3.1 [Explainable AI Copilot](#31-explainable-ai-xai-copilot)  
   3.2 [Numerical Stability](#32-numerical-stability-cfl-condition)  
   3.3 [Data Integrity](#33-data-integrity)  

4. [Assumptions & Known Limitations](#-4-assumptions--known-limitations)  

5. [Project Structure](#-5-project-structure)  

6. [Installation & Usage](#-6-installation--usage)  

7. [Credits & Transparency](#-7-credits--transparency)  

8. [License](#-8-license)

---

# 🔬 1. Scientific Framework & Physics Engine

**Research Question:**  
*How do stellar flares impact the stability of the terminator habitable zone on tidally locked exoplanets, and can methane-based biosignatures persist under such dynamic conditions?*

**Project Context:**  
This project is a direct implementation of the **"Tidally Locked Planet"** challenge proposed in the HACK-4-SAGES materials (Section 3.2, pp. 6-7). We extend the base requirements with a flare simulation module and an XAI Copilot.

**What Makes This a Digital Twin:**  
ExoStress Twin functions as a true digital twin by maintaining a consistent virtual representation of TRAPPIST-1e that evolves in real time based on user inputs, while preserving mass and energy conservation laws. This allows researchers to experiment with "what-if" scenarios in a physically coherent framework.

The core of ExoStress Twin is a custom-built **2D Energy Balance Model (EBM)**. It bridges the gap between simple 1D models and complex 3D simulations, delivering immediate feedback for parametric exploration.

---

## 1.1 Atmospheric Dynamics (Zonal Advection)

TRAPPIST-1e is tidally locked, creating permanent day and night hemispheres.

- **Super-rotation simulation:**  
  We implement a numerical “equatorial jet” parameterization. Heat is actively transported eastward using `np.roll` shifts, recreating the asymmetric terminator and “hot-spot shift” described in modern astrophysical literature (Showman & Polvani, 2011).

- **Thermal diffusion:**  
  Atmospheric heat redistribution follows a 2D diffusion equation. Users can manipulate the diffusion coefficient ($D$) to simulate atmospheres ranging from thin, Mars-like envelopes to thick, Venus-style insulation.

---

## 1.2 Hydrological Cycle (Mass Conservation)

Water is treated as a **closed-loop system** – a critical requirement for physical validity.

- **Bulk transport closure:**  
  We mathematically guarantee **100% water mass conservation**. Water evaporates on the dayside, is transported via parameterized winds, and precipitates on the nightside.

- **Phase inventory tracking:**

  - **Liquid:** Maintained within the “habitable zone”  
    ($0\,^\circ\mathrm{C} < T < 100\,^\circ\mathrm{C}$)

  - **Ice (ice-albedo feedback):**  
    When temperature drops below freezing *and* water is present, local albedo increases to **0.75**. This triggers a cooling loop that can lead to a permanent **“Snowball Earth” state**.

  - **Gas:**  
    High temperatures trigger evaporation. Increased water vapour acts as a greenhouse gas, allowing users to observe the onset of a **runaway greenhouse effect**.

---

## 1.3 Stellar-Planet Interaction (Flare Events)

M-dwarfs like TRAPPIST-1 are notoriously active. Our engine phenomenologically simulates:

- **Atmospheric stripping:**  
  High-energy flare particles erode the atmosphere. This is modelled as a temporary reduction in greenhouse efficiency and heat diffusion, scaled by the planet’s relative gravity ($g_{\text{rel}}$).

- **UV photolysis:**  
  Stellar flares trigger rapid destruction of atmospheric methane (CH₄), demonstrating the transient nature of biosignatures on planets around active stars.

---

## 1.4 Validation

- **Terminator temperature:**  
  The baseline Earth-like scenario (albedo = 0.3, diffusion = 0.05) produces a terminator temperature of ~15 °C, consistent with 1D energy balance estimates for TRAPPIST-1e (see Turbet et al. 2016).

- **Snowball transition:**  
  The ice-albedo runaway occurs at **albedo > 0.6**, matching theoretical expectations for global glaciation thresholds.

- **Flare response:**  
  Post-flare methane collapse follows **first-order kinetics**, qualitatively reproducing the photolytic destruction expected under enhanced UV flux.

---

# 🧪 2. Biosignature Logic: The Methane Proxy

ExoStress Twin uses **biogenic methane** as a primary proxy for biological activity.

- **The “sweet spot” heuristic:**  
  CH₄ production is tied to surface habitability, specifically focusing on the **terminator zone where liquid water is stable**.

- **Sub-glacial methanogenesis:**  
  Inspired by Rugheimer et al. (2015), the model accounts for methanogenic activity under global ice sheets. This justifies why a planet in a **“Snowball” state** might still exhibit detectable biosignatures.

- **Methane decay:**  
  A first-order photolysis term removes CH₄, with a loss rate that increases during **flare events**.

---

# 🤖 3. Technology Stack & XAI Integration

## 3.1 Explainable AI (XAI) Copilot

We integrated a **deterministic XAI Copilot** to assist researchers.

Unlike generic LLMs, this tool:

- **Reads live telemetry:** habitability fractions, phase shifts, energy flux.
- **Generates insights:** provides human-readable explanations of complex climate feedbacks (e.g., why a planet entered a stable equilibrium or a drifting state).
- **Guarantees stability:** rule-based responses avoid the unpredictability of external APIs during live demonstrations.

The frontend is ready to swap in a true **LLM endpoint with one line of code**.

---

## 3.2 Numerical Stability (CFL Condition)

To keep the simulation robust under extreme user interactions (e.g., **15× flares**), we implement the **Courant-Friedrichs-Lewy (CFL) condition**.

A **dynamic time-stepping mechanism** subdivides each main step to prevent numerical divergence in the diffusion calculations.

---

## 3.3 Data Integrity

- **NASA Exoplanet Archive:**  
  Core parameters (mass, radius, luminosity) are dynamically read from the archive (local cache included).

- **Primary reference:**  
  Baseline parameters follow **Agol et al. (2021)**.

- **Fallback:**  
  If CSV files are missing, the code falls back to hard-coded values to ensure the simulation always runs.

---

# ⚠️ 4. Assumptions & Known Limitations

The project was built in **48 hours for a hackathon**.  
Below are the conscious engineering and scientific trade-offs.

---

## 4.1 Atmospheric Model: 2D EBM vs. 3D GCM

**Assumption:**  
A **2D Energy Balance Model** with advection parameterization is used instead of a full **General Circulation Model (GCM)**.

**Why:**  
GCMs require supercomputers and hours of simulation time. Our goal is **real-time interactivity**.

**Consequences:**  
No vertical atmosphere profile, clouds, or realistic 3D circulation.

---

## 4.2 Water Transport: “Teleportation” Instead of Full Dynamics

**Assumption:**  
Water is transported from the dayside to the nightside using `np.roll` (a **180° longitudinal shift**).

**Why:**  
This guarantees **mass conservation** and mimics the net effect of atmospheric circulation.

**Consequences:**  
No clouds or gradual transport.

---

## 4.3 Methane Biosignature: Heuristic Instead of Chemistry

**Assumption:**  
CH₄ production scales with the **area of the “sweet spot”**.

**Why:**  
A full biogeochemical model would require unknown extraterrestrial data.

**Consequences:**  
Methane values (scaled to **2500 ppm**) are abstract proxies.

---

## 4.4 Flare Events: Parameterized Atmospheric Loss

**Assumption:**  
Flares reduce **diffusion and greenhouse coefficients**.

**Why:**  
The 2D model has no vertical axis.

**Consequences:**  
Atmospheric loss is simulated indirectly.

---

## 4.5 Numerical Stability: Simplified CFL

**Assumption:**  
`grid_spacing = 2.0`.

**Why:**  
Maintains numerical stability.

**Consequences:**  
Time step not physically calibrated.

---

## 4.6 Ice Albedo: Fixed Value

**Assumption:**  
Ice albedo fixed at **0.75**.

**Why:**  
Captures essential **ice-albedo feedback**.

---

## 4.7 XAI Copilot: Rule-Based Instead of LLM

**Assumption:**  
Deterministic rules instead of API.

**Why:**  
Guaranteed stability during live demos.

---

# 📂 5. Project Structure

```

exostress-twin/
├── main.py
├── script.js
├── index.html
├── style.css
├── star_parameters/
├── planet_parameters/
└── requirements.txt

```

**Dependencies**

```

fastapi==0.115.0
uvicorn==0.30.1
numpy==1.26.0
pandas==2.1.0
python-multipart==0.0.6

````

---

# 🛠️ 6. Installation & Usage

```bash
git clone https://github.com/your-username/exostress-twin.git
cd exostress-twin

pip install -r requirements.txt

python main.py
````

or

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open:

```
http://localhost:8000
```

Requirements:

* Python 3.9+
* Modern browser

---

# 🎬 7. Credits & Transparency

**Visuals:** Vidu AI
**Voiceover:** ElevenLabs AI

**Data Sources**

* NASA Exoplanet Archive
* Agol et al. (2021)

---

# 📄 8. License

MIT License.

---

**ExoStress Twin** – *Because habitability is not just about location, it’s about resilience.*

```

