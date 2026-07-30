"use strict";

// The badge catalog is NEVER hand-written here (audit AA-03): static
// mode reads window.RGCS_CATALOG from assets/catalog.data.js, which
// build_static_hub.py generates from the canonical module registry
// (rgcs_lab.common.status.module_catalog). Server mode asks /api/modules.
const FALLBACK_MODULES =
  (typeof window !== "undefined" && window.RGCS_CATALOG) || [];

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
