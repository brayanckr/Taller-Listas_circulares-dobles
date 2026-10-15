"use strict";

const SVG_NS = "http://www.w3.org/2000/svg";
const COLORS = { current: "#22c55e", prev: "#f59e0b", next: "#3b82f6", other: "#475569" };

const els = {
  image: document.getElementById("frame-image"),
  title: document.getElementById("frame-title"),
  description: document.getElementById("frame-description"),
  meta: document.getElementById("frame-meta"),
  diagram: document.getElementById("diagram"),
  pointerInfo: document.getElementById("pointer-info"),
  message: document.getElementById("message"),
  form: document.getElementById("add-form"),
  btnPrev: document.getElementById("btn-prev"),
  btnNext: document.getElementById("btn-next"),
  btnDelete: document.getElementById("btn-delete"),
};

let state = { current: null, frames: [] };

/* ---------- API ---------- */

async function api(path, method = "GET", body) {
  const response = await fetch(`/api/frames/${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

async function run(path, method, body, successMessage) {
  try {
    state = await api(path, method, body);
    render();
    if (successMessage) showMessage(successMessage, "ok");
    return true;
  } catch (error) {
    showMessage(error.message, "error");
    return false;
  }
}

/* ---------- Rendering ---------- */

function showMessage(text, kind) {
  els.message.textContent = text;
  els.message.className = `message ${kind || ""}`;
}

function render() {
  renderViewer();
  renderDiagram();
}

function renderViewer() {
  const frame = state.current;
  const empty = !frame;
  els.btnPrev.disabled = els.btnNext.disabled = els.btnDelete.disabled = empty;
  if (empty) {
    els.image.removeAttribute("src");
    els.title.textContent = "No frames available";
    els.description.textContent = "Add a frame using the management panel below.";
    els.meta.textContent = "";
    return;
  }
  els.image.classList.add("swapping");
  els.image.onload = () => els.image.classList.remove("swapping");
  els.image.src = frame.image_url;
  els.image.alt = frame.title;
  els.title.textContent = frame.title;
  els.description.textContent = frame.description;
  els.meta.textContent = `Frame #${frame.frame_id} · ${state.size} frame(s) in the list`;
}

function svgEl(name, attrs = {}, text) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
}

function roleOf(frame) {
  if (frame.is_current) return "current";
  if (frame.is_prev) return "prev";
  if (frame.is_next) return "next";
  return "other";
}

function renderDiagram() {
  const svg = els.diagram;
  svg.replaceChildren();

  const defs = svgEl("defs");
  const marker = (id, color) => {
    const m = svgEl("marker", { id, viewBox: "0 0 10 10", refX: 8, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" });
    m.appendChild(svgEl("path", { d: "M0 0 L10 5 L0 10 z", fill: color }));
    return m;
  };
  defs.append(marker("arrow", "#94a3b8"), marker("arrow-wrap", "#e879f9"));
  svg.appendChild(defs);

  const frames = state.frames;
  const count = frames.length;
  if (!count) {
    svg.appendChild(svgEl("text", { x: 350, y: 230 }, "The list is empty"));
    els.pointerInfo.textContent = "head = null";
    return;
  }

  const cx = 350, cy = 230, radius = 175;
  const boxW = 104, boxH = 54;
  const positions = frames.map((_, i) => {
    const theta = -Math.PI / 2 + (2 * Math.PI * i) / count;
    return { x: cx + radius * Math.cos(theta), y: cy + radius * Math.sin(theta), theta };
  });

  // Bidirectional links between consecutive frames; the last one wraps to the first.
  if (count > 1) {
    frames.forEach((_, i) => {
      const j = (i + 1) % count;
      const isWrap = i === count - 1;
      if (count === 2 && i === 1) return; // two frames: one pair of arrows is enough
      const a = positions[i], b = positions[j];
      const mid = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
      const push = 1.18; // bow the link outward to keep it visible next to the boxes
      const ctrl = { x: cx + (mid.x - cx) * push, y: cy + (mid.y - cy) * push };
      const start = trim(a, ctrl, boxW, boxH);
      const end = trim(b, ctrl, boxW, boxH);
      const markerId = isWrap ? "arrow-wrap" : "arrow";
      svg.appendChild(svgEl("path", {
        d: `M${start.x} ${start.y} Q${ctrl.x} ${ctrl.y} ${end.x} ${end.y}`,
        class: `link${isWrap ? " wrap" : ""}`,
        "marker-start": `url(#${markerId})`,
        "marker-end": `url(#${markerId})`,
      }));
      if (isWrap) {
        svg.appendChild(svgEl("text", { x: ctrl.x, y: ctrl.y - 8, class: "wrap-label" }, "circular link"));
      }
    });
  }

  frames.forEach((frame, i) => {
    const { x, y } = positions[i];
    const role = roleOf(frame);
    const group = svgEl("g");
    group.appendChild(svgEl("rect", {
      x: x - boxW / 2, y: y - boxH / 2, width: boxW, height: boxH, rx: 10,
      class: "box", fill: COLORS[role], stroke: role === "other" ? "#64748b" : "#fff",
    }));
    group.appendChild(svgEl("text", { x, y: y - 4 }, `${frame.angle_degree}°`));
    group.appendChild(svgEl("text", { x, y: y + 13, class: "sub" }, `id ${frame.frame_id}`));
    if (role !== "other") {
      const label = { current: "CURRENT", prev: "PREV", next: "NEXT" }[role];
      group.appendChild(svgEl("text", { x, y: y - boxH / 2 - 6, class: "tag" }, label));
    }
    svg.appendChild(group);
  });

  const cur = frames.find((f) => f.is_current);
  els.pointerInfo.textContent =
    `current = #${cur.frame_id} (${cur.angle_degree}°)  |  ` +
    `prev_frame → #${cur.prev_id}  |  next_frame → #${cur.next_id}  |  size = ${state.size}`;
}

// Shorten a link so it ends at the edge of the box instead of its center.
function trim(from, toward, w, h) {
  const dx = toward.x - from.x, dy = toward.y - from.y;
  const scale = Math.min((w / 2 + 4) / Math.abs(dx || 1e-6), (h / 2 + 4) / Math.abs(dy || 1e-6));
  return { x: from.x + dx * scale, y: from.y + dy * scale };
}

/* ---------- Events ---------- */

els.btnNext.addEventListener("click", () => run("next", "POST"));
els.btnPrev.addEventListener("click", () => run("prev", "POST"));

document.addEventListener("keydown", (event) => {
  if (["INPUT", "TEXTAREA"].includes(event.target.tagName)) return;
  if (event.key === "ArrowRight") run("next", "POST");
  if (event.key === "ArrowLeft") run("prev", "POST");
});

els.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const ok = await run("add", "POST", {
    angle_degree: Number(document.getElementById("input-angle").value),
    image_url: document.getElementById("input-image").value,
    description: document.getElementById("input-description").value,
  }, "Frame added.");
  if (ok) els.form.reset();
});

els.btnDelete.addEventListener("click", () => {
  if (!state.current) return;
  run(`delete/${state.current.frame_id}`, "DELETE", undefined, "Current frame deleted.");
});

run("state", "GET");
