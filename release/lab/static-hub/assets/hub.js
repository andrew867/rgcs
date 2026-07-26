"use strict";

const FALLBACK_MODULES = [
  {id:"coordinate",title:"Coordinate",status:"GREEN",physical_status:"YELLOW",purpose:"Exact Federation/Terra 30-bit F5|Q22|S3 structural codec.",does_not:"Does not yet establish a unique physical source map."},
  {id:"golay",title:"Golay",status:"GREEN",physical_status:"YELLOW",purpose:"Extended binary Golay G24 transport wrapper for a 36-bit address.",does_not:"Does not show that an external civilization uses Golay coding."},
  {id:"frames",title:"Frames",status:"GREEN",physical_status:"YELLOW",purpose:"Ordered quaternion frame compositions with round-trip checks.",does_not:"Does not demonstrate a physical field effect."},
  {id:"memory",title:"Memory",status:"GREEN",physical_status:"YELLOW",purpose:"Reproducible provenance-memory retrieval benchmark harness.",does_not:"Does not demonstrate consciousness."},
  {id:"dual_pole",title:"Dual-Pole",status:"GREEN",physical_status:"YELLOW",purpose:"Proposer/critic research loop with typed attack families.",does_not:"Does not make two models independent witnesses."},
  {id:"lattice",title:"Lattice",status:"GREEN",physical_status:"YELLOW",purpose:"64-state synthetic resonant lattice with an energy ledger.",does_not:"Does not transport matter."},
  {id:"metasurface",title:"Metasurface",status:"YELLOW",physical_status:"YELLOW",purpose:"Passive reduced-order spoof-SPP cell with energy accounting.",does_not:"Does not modify gravity."},
  {id:"predictions",title:"Predictions",status:"YELLOW",physical_status:"YELLOW",purpose:"Freeze prospective predictions and null controls before measurement.",does_not:"Does not validate a mechanism merely because one outcome matches."},
  {id:"proofs",title:"Proofs",status:"GREEN",physical_status:"YELLOW",purpose:"Aggregate receipts, hashes, and claim-boundary audit surface.",does_not:"Does not convert a green UI into a physical proof."}
];

function detectMode() {
  // Static file:// or missing API → static fixtures. Server mode uses /api.
  if (location.protocol === "file:") return "static";
  return "auto";
}

async function loadModules() {
  if (detectMode() === "static") return FALLBACK_MODULES;
  try {
    const res = await fetch("/api/modules", {credentials: "omit"});
    if (!res.ok) throw new Error("api unavailable");
    const data = await res.json();
    return data.modules || FALLBACK_MODULES;
  } catch (_) {
    // Prefer fixtures when API is absent (static hosting of /hub).
    try {
      const res = await fetch("fixtures/catalog.json", {credentials: "omit"});
      if (res.ok) {
        const data = await res.json();
        return data.modules || FALLBACK_MODULES;
      }
    } catch (__) {}
    return FALLBACK_MODULES;
  }
}

function card(mod) {
  const el = document.createElement("article");
  el.className = "card";
  el.innerHTML = `
    <div class="badges">
      <span class="badge ${mod.status}">${mod.status}</span>
      <span class="badge YELLOW phys">PHYS ${mod.physical_status || "YELLOW"}</span>
    </div>
    <h3>${mod.title}</h3>
    <p><strong>Does:</strong> ${mod.purpose}</p>
    <p class="does-not"><strong>Does not:</strong> ${mod.does_not}</p>
    <div class="card-actions">
      <a href="modules/${mod.id}.html">Open</a>
      <a href="fixtures/${mod.id}.json">Example</a>
      <a href="receipts/${mod.id}.json" download>Receipt</a>
      <a href="modules/${mod.id}.html#source">Source</a>
    </div>`;
  return el;
}

async function boot() {
  const grid = document.getElementById("module-grid");
  if (!grid) return;
  const modules = await loadModules();
  grid.replaceChildren(...modules.map(card));

  // Adjust coordinate demo link for server vs static layouts.
  const coord = document.getElementById("coord-demo");
  const wb = document.getElementById("wb-link");
  if (location.pathname.includes("/hub") || location.pathname.endsWith("/")) {
    // served from FastAPI root or /hub/
  }
  if (location.protocol !== "file:" && coord) {
    coord.setAttribute("href", "/workbench");
  }
  if (location.protocol !== "file:" && wb) {
    wb.setAttribute("href", "/workbench");
  }

  const toggle = document.getElementById("theme-toggle");
  const root = document.documentElement;
  const saved = localStorage.getItem("rgcs-lab-theme");
  if (saved) root.setAttribute("data-theme", saved);
  if (toggle) {
    toggle.addEventListener("click", () => {
      const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      if (next === "light") root.removeAttribute("data-theme");
      else root.setAttribute("data-theme", "dark");
      localStorage.setItem("rgcs-lab-theme", next === "light" ? "" : "dark");
      toggle.setAttribute("aria-pressed", next === "dark" ? "true" : "false");
    });
  }
}

boot();

// Shared helpers for module pages.
window.RGCSLab = {
  async run(path, body) {
    if (location.protocol === "file:") {
      const name = path.split("/").filter(Boolean).slice(-2, -1)[0] || path;
      const fixture = await fetch(`../fixtures/${name}.json`).then(r => r.json());
      return fixture;
    }
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body || {}),
        credentials: "omit"
      });
      if (!res.ok) throw new Error(await res.text());
      return await res.json();
    } catch (err) {
      const fallback = path.includes("coordinate") ? "coordinate"
        : path.includes("golay") ? "golay"
        : path.includes("frames") ? "frames"
        : path.includes("memory") ? "memory"
        : path.includes("dual") ? "dual_pole"
        : path.includes("lattice") ? "lattice"
        : path.includes("metasurface") ? "metasurface"
        : path.includes("prediction") ? "predictions"
        : "proofs";
      return fetch(`../fixtures/${fallback}.json`).then(r => r.json());
    }
  },
  downloadJSON(filename, obj) {
    const blob = new Blob([JSON.stringify(obj, null, 2) + "\n"], {type: "application/json"});
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  }
};
