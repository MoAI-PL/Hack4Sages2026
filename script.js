let timeoutId;
let lastSimData = null; 
let lastWasFlare = false; 

async function runSimulation(flare = false) {
    const endpoint = flare ? "/simulate_flare" : "/simulate";
    lastWasFlare = flare;
    
    const diffSlider = document.getElementById("diff-slider");
    const greenhouseSlider = document.getElementById("greenhouse-slider");
    
    // UI LOGIC FIX: Retrieve variables dynamically (using 'let') to allow for backend processing 
    // without prematurely overwriting frontend slider positions.
    let diff = parseFloat(diffSlider.value);
    let albedo = parseFloat(document.getElementById("albedo-slider").value);
    let flareMult = parseFloat(document.getElementById("flare-slider").value);
    let greenhouse = parseFloat(greenhouseSlider.value);

    // The payload sent to the server contains 100% accurate and synchronized values from user input.
    const payload = { diffusion: diff, albedo: albedo, flare_multiplier: flareMult, greenhouse: greenhouse };

    const flareBtn = document.getElementById("flareBtn");
    let originalText = "";
    if (flareBtn && flare) {
        originalText = flareBtn.textContent;
        flareBtn.textContent = "UPLOADING TELEMETRY...";
    }
    
    try {
        const resp = await fetch(endpoint, { 
            method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
        });
        
        // DATA VALIDATION FIX: Ensure the parsed JSON is a valid object before proceeding to avoid crashes.
        const data = await resp.json();
        if (!data || typeof data !== 'object') throw new Error('Invalid response from server');
        lastSimData = data; 
        
        if (flareBtn && flare) flareBtn.textContent = originalText;
        
        // Push warning to the GenAI Copilot upon successful flare execution
        if (flare) {
            sendChatMessage("CRITICAL WARNING: Flare impact detected.", true);
        }
        
        updateKPI(data.habitability_fraction, data.methane_level);
        updateTelemetry(data.telemetry); 
        plotGlobe(data.heatmap_data); 
        plotTempEvolution(data.temp_evolution);
        plotWater(data.water_inventory);
    } catch (e) {
        console.error("Simulation failed:", e);
        if (flareBtn && flare) flareBtn.textContent = "ERROR: NO CONNECTION";
    }
}

// DEBOUNCING IMPLEMENTATION: Protects the backend from excessive REST API calls when sliding inputs.
function debouncedRun() {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => { 
        try { runSimulation(false); } catch(e) { console.error(e); } 
    }, 150);
}

document.getElementById("diff-slider").addEventListener("input", (e) => { document.getElementById("diff-val").textContent = e.target.value; document.getElementById("diff-val").style.color = "#00ffcc"; debouncedRun(); });
document.getElementById("albedo-slider").addEventListener("input", (e) => { document.getElementById("albedo-val").textContent = e.target.value; debouncedRun(); });
document.getElementById("greenhouse-slider").addEventListener("input", (e) => { document.getElementById("greenhouse-val").textContent = parseFloat(e.target.value).toFixed(2); document.getElementById("greenhouse-val").style.color = "#00ffcc"; debouncedRun(); });
// Flare slider independently triggers the debounced simulation run to show immediate impact preview.
document.getElementById("flare-slider").addEventListener("input", (e) => { document.getElementById("flare-val").textContent = parseFloat(e.target.value).toFixed(1); debouncedRun(); });

function applyScenario(diff, alb, green) {
    document.getElementById("diff-slider").value = diff;
    document.getElementById("albedo-slider").value = alb;
    document.getElementById("greenhouse-slider").value = green;
    document.getElementById("diff-val").textContent = diff;
    document.getElementById("albedo-val").textContent = alb;
    document.getElementById("greenhouse-val").textContent = parseFloat(green).toFixed(2);
    document.getElementById("diff-val").style.color = "#00ffcc";
    document.getElementById("greenhouse-val").style.color = "#00ffcc";
    runSimulation(false);
}

document.getElementById("btn-earth").addEventListener("click", () => applyScenario(0.05, 0.3, 0.1));
document.getElementById("btn-snowball").addEventListener("click", () => applyScenario(0.01, 0.7, 0.0));
document.getElementById("btn-venus").addEventListener("click", () => applyScenario(0.15, 0.1, 0.7));

document.getElementById("chat-send").addEventListener("click", () => sendChatMessage());
document.getElementById("chat-input").addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendChatMessage();
});

async function sendChatMessage(systemOverrideMsg = null, isFlareEvent = false) {
    const input = document.getElementById("chat-input");
    const question = systemOverrideMsg ? systemOverrideMsg : input.value.trim();
    
    if (!question || !lastSimData) return;

    if (!systemOverrideMsg) {
        addChatMessage("user", question);
        input.value = "";
    }

    const payload = {
        question: question,
        habitability: lastSimData.habitability_fraction,
        methane: lastSimData.methane_level,
        albedo: parseFloat(document.getElementById("albedo-slider").value),
        greenhouse: parseFloat(document.getElementById("greenhouse-slider").value),
        diffusion: parseFloat(document.getElementById("diff-slider").value),
        is_flare: isFlareEvent ? true : lastWasFlare
    };

    try {
        const resp = await fetch("/copilot", {
            method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
        });
        const data = await resp.json();
        addChatMessage(isFlareEvent ? "flare" : "ai", "> " + data.response);
    } catch (e) {
        addChatMessage("flare", "> Error: AI Copilot offline.");
    }
}

function addChatMessage(sender, text) {
    const history = document.getElementById("chat-history");
    if (!history) return; // UI SAFETY: Prevents application crash if the chat container is missing
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-msg ${sender}-msg`;
    msgDiv.textContent = text;
    history.appendChild(msgDiv);
    history.scrollTop = history.scrollHeight;
}

// DATA EXPORT: Extended CSV generation including water phases, habitability and temperatures.
document.getElementById("exportBtn").addEventListener("click", () => {
    if (!lastSimData) return alert("NO TELEMETRY. RUN SIMULATION FIRST.");
    const data = lastSimData;
    let csv = "EXOSTRESS TWIN // MISSION LOG\n";
    csv += `Habitability Surface %,${(data.habitability_fraction * 100).toFixed(2)}\n`;
    csv += `Methane Signature PPM,${(data.methane_level * 2500).toFixed(0)}\n\n`;
    
    csv += "TIME_STEP,NORTH_POLE_C,SUB_STELLAR_C,ANTI_STELLAR_C,TERMINATOR_C,ICE_MASS,LIQUID_MASS,GAS_MASS\n";
    const evo = data.temp_evolution;
    const inv = data.water_inventory;
    
    for(let i=0; i<evo.north_pole.length; i++) {
        csv += `${i},${evo.north_pole[i].toFixed(2)},${evo.sub_stellar[i].toFixed(2)},${evo.anti_stellar[i].toFixed(2)},${evo.terminator[i].toFixed(2)},${inv.ice[i].toFixed(1)},${inv.liquid[i].toFixed(1)},${inv.gas[i].toFixed(1)}\n`;
    }
    
    const encodedUri = encodeURI("data:text/csv;charset=utf-8," + csv);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "TRAPPIST-1e_Full_Telemetry.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});

function updateKPI(habit, methane) { 
    if (habit === undefined || methane === undefined) return;
    document.getElementById("habitability").textContent = `${(habit * 100).toFixed(1)}%`; 
    // The scalar 2500 represents the estimated upper limit of biogenic methane (in ppm) 
    // for M-Dwarf planets based on literature approximations (e.g., Rugheimer et al. 2015).
    document.getElementById("biosignatures").textContent = `${(methane * 2500).toFixed(0)} ppm`; 
}

function updateTelemetry(tel) {
    if (!tel) return;
    document.getElementById("tel-mstar").textContent = tel.m_star.toFixed(3);
    document.getElementById("tel-orbit").textContent = tel.orbit.toFixed(3);
    document.getElementById("tel-mplan").textContent = tel.m_planet.toFixed(3);
    document.getElementById("tel-grav").textContent = tel.gravity.toFixed(2);
    document.getElementById("tel-tlock").textContent = tel.t_lock.toExponential(2);
    document.getElementById("tel-aeq").textContent = tel.a_eq.toFixed(3);
    document.getElementById("tel-steady").textContent = tel.steady;
}

const darkLayout = { plot_bgcolor: "rgba(0,0,0,0)", paper_bgcolor: "rgba(0,0,0,0)", font: { color: "#8892b0", family: "Inter, sans-serif", size: 10 }, margin: { t: 40, b: 30, l: 40, r: 20 } };

function plotGlobe(z_data) {
    const rows = z_data.length; const cols = z_data[0].length;
    const x = []; const y = []; const z = [];
    for (let i = 0; i < rows; i++) {
        const rowX = []; const rowY = []; const rowZ = [];
        const v = (i / (rows - 1)) * Math.PI;
        for (let j = 0; j < cols; j++) {
            const u = (j / (cols - 1)) * 2 * Math.PI - Math.PI;
            rowX.push(Math.sin(v) * Math.cos(u)); rowY.push(Math.sin(v) * Math.sin(u)); rowZ.push(Math.cos(v));
        }
        x.push(rowX); y.push(rowY); z.push(rowZ);
    }
    const trace = { type: 'surface', x: x, y: y, z: z, surfacecolor: z_data, colorscale: 'Inferno', cmin: -100, cmax: 120, colorbar: { title: 'Temp (°C)', thickness: 15, x: 1.05 }, contours: { z: { show: true, usecolormap: false, highlightcolor: "#00ffcc", project: {z: false}, start: 0, end: 50, size: 50, color: "#00ffcc", width: 3 } } };
    const layout3D = { ...darkLayout, title: { text: "TRAPPIST-1e // LIVE 3D ORBITAL VIEW", font: { color: "#ffffff", size: 14, letterSpacing: 1 } }, scene: { xaxis: { visible: false }, yaxis: { visible: false }, zaxis: { visible: false }, camera: { eye: { x: 1.5, y: -1.5, z: 0.5 } }, aspectratio: { x: 1, y: 1, z: 1 } }, margin: { t: 50, b: 0, l: 0, r: 0 }, uirevision: 'true' };
    Plotly.react("heatmap", [trace], layout3D);
}

function plotTempEvolution(evo) {
    const x = [...Array(evo.north_pole.length).keys()];
    const data = [ { x: x, y: evo.north_pole, name: "NORTH POLE", line: {color: '#555555'} }, { x: x, y: evo.sub_stellar, name: "DAYSIDE", line: {color: '#ff3333'} }, { x: x, y: evo.anti_stellar, name: "NIGHT", line: {color: '#3366ff'} }, { x: x, y: evo.terminator, name: "TERMINATOR", line: {color: '#00ffcc', width: 3} } ];
    const layout = { ...darkLayout, title: { text: "TEMPERATURE EVOLUTION", font: { color: "#ffffff", size: 14 } }, xaxis: { title: "TIME", gridcolor: "rgba(255,255,255,0.05)", zeroline: false }, yaxis: { title: "TEMP (°C)", gridcolor: "rgba(255,255,255,0.05)", zeroline: false }, legend: { orientation: "h", y: -0.3 }, uirevision: 'true' };
    Plotly.react("tempChart", data, layout);
}

function plotWater(inv) {
    const x = [...Array(inv.ice.length).keys()];
    const traces = [ { x: x, y: inv.ice, stackgroup: "one", name: "ICE", fillcolor: '#1a365d', line: {width: 0} }, { x: x, y: inv.liquid, stackgroup: "one", name: "LIQUID", fillcolor: '#00ffcc', line: {width: 0} }, { x: x, y: inv.gas, stackgroup: "one", name: "GAS", fillcolor: '#742a2a', line: {width: 0} } ];
    const layout = { ...darkLayout, title: { text: "WATER PHASE INVENTORY", font: { color: "#ffffff", size: 14 } }, xaxis: { title: "TIME", gridcolor: "rgba(255,255,255,0.05)", zeroline: false }, yaxis: { title: "MASS", gridcolor: "rgba(255,255,255,0.05)", zeroline: false }, legend: { orientation: "h", y: -0.3 }, uirevision: 'true' };
    Plotly.react("waterChart", traces, layout);
}

// Event listener initialization for the flare trigger button.
if (document.getElementById("flareBtn")) document.getElementById("flareBtn").addEventListener("click", () => runSimulation(true));

// Fires an initial silent simulation upon window load to populate the dashboard and prevent blinking empty data.
window.addEventListener('load', () => {
    runSimulation(false);
});