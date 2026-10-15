/**
 * CarouselVisualizer
 *
 * Draws the doubly circular linked list as boxes placed on a circle.
 * Every slide has two arrows: next_slide (blue) and previous_slide (orange).
 * HEAD, CURRENT and TAIL tags are attached to the boxes. When the state
 * changes (insert, remove, shuffle, navigate) positions, arrows and
 * highlights are tweened so the relinking can be followed on screen.
 */
(function () {
  "use strict";

  var SVG_SIZE = 560;
  var CENTER = SVG_SIZE / 2;
  var RADIUS = 175;
  var ANIMATION_MS = 600;
  var NEXT_COLOR = "#4fc3f7";
  var PREV_COLOR = "#ffb74d";

  function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function lerp(a, b, t) { return a + (b - a) * t; }
  function ease(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }

  /** Distance from a box center to its border along the unit direction (dx, dy). */
  function borderDistance(w, h, dx, dy) {
    var tx = Math.abs(dx) < 1e-6 ? Infinity : w / 2 / Math.abs(dx);
    var ty = Math.abs(dy) < 1e-6 ? Infinity : h / 2 / Math.abs(dy);
    return Math.min(tx, ty);
  }

  function CarouselVisualizer(svg, pointersEl, onSelect) {
    this.svg = svg;
    this.pointersEl = pointersEl;
    this.onSelect = onSelect;
    this.layout = new Map();   // id -> {x, y, w, h, index, slide} of the last target
    this.arrows = new Map();   // key -> {kind, from, to} of the last target
    this.shown = new Map();    // id -> {x, y, w, h} currently on screen
    this.state = null;
    this.frame = null;

    svg.innerHTML =
      "<defs>" +
      this._marker("arrow-next", NEXT_COLOR) +
      this._marker("arrow-prev", PREV_COLOR) +
      "</defs>" +
      '<g id="viz-arrows"></g><g id="viz-boxes"></g><g id="viz-tags"></g><g id="viz-center"></g>';
    this.arrowLayer = svg.querySelector("#viz-arrows");
    this.boxLayer = svg.querySelector("#viz-boxes");
    this.tagLayer = svg.querySelector("#viz-tags");
    this.centerLayer = svg.querySelector("#viz-center");

    var self = this;
    svg.addEventListener("click", function (event) {
      var target = event.target.closest("[data-id]");
      if (target && self.onSelect) { self.onSelect(target.getAttribute("data-id")); }
    });
  }

  CarouselVisualizer.prototype._marker = function (id, color) {
    return '<marker id="' + id + '" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" ' +
      'markerHeight="7" markerUnits="userSpaceOnUse" orient="auto-start-reverse">' +
      '<path d="M0,0 L10,5 L0,10 z" fill="' + color + '"/></marker>';
  };

  /** Compute the target box geometry of every slide for the given state. */
  CarouselVisualizer.prototype._computeLayout = function (state) {
    var slides = state.slides;
    var n = slides.length;
    var layout = new Map();
    var width = n <= 2 ? 104 : Math.max(36, Math.min(104, 2 * RADIUS * Math.sin(Math.PI / n) * 0.84));
    var height = Math.max(26, Math.round(width * 0.56));
    slides.forEach(function (slide, i) {
      var angle = -Math.PI / 2 + (2 * Math.PI * i) / n;
      layout.set(slide.id, {
        x: CENTER + RADIUS * Math.cos(angle),
        y: CENTER + RADIUS * Math.sin(angle),
        w: width,
        h: height,
        index: i + 1,
        slide: slide
      });
    });
    return layout;
  };

  CarouselVisualizer.prototype._computeArrows = function (state) {
    var arrows = new Map();
    state.slides.forEach(function (slide) {
      arrows.set("next:" + slide.id + ">" + slide.next_id, { kind: "next", from: slide.id, to: slide.next_id });
      arrows.set("prev:" + slide.id + ">" + slide.previous_id, { kind: "prev", from: slide.id, to: slide.previous_id });
    });
    return arrows;
  };

  /** Update the diagram with a new state, animating the difference. */
  CarouselVisualizer.prototype.render = function (state) {
    if (this.frame) { cancelAnimationFrame(this.frame); this.frame = null; }
    var previous = {
      layout: this.layout,
      arrows: this.arrows,
      shown: new Map(this.shown),
      state: this.state
    };
    this.state = state;
    this.layout = this._computeLayout(state);
    this.arrows = this._computeArrows(state);
    this._renderPointers(state);

    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var duration = reduce || !previous.state ? 0 : ANIMATION_MS;
    var start = performance.now();
    var self = this;

    function step(now) {
      var t = duration === 0 ? 1 : Math.min(1, (now - start) / duration);
      self._draw(previous, ease(t));
      if (t < 1) { self.frame = requestAnimationFrame(step); } else { self.frame = null; }
    }
    step(start);
  };

  CarouselVisualizer.prototype._draw = function (previous, t) {
    var self = this;
    var boxes = new Map();   // id -> {x, y, w, h, index, slide, alpha, cur, head, tail}
    var state = this.state;
    var prevState = previous.state;

    this.layout.forEach(function (target, id) {
      var from = previous.shown.get(id) || { x: target.x, y: target.y, w: target.w, h: target.h };
      var wasNew = !previous.layout.has(id);
      var before = previous.layout.get(id);
      var oldCur = before && before.slide.is_current ? 1 : 0;
      var oldHead = before && before.slide.is_head ? 1 : 0;
      var oldTail = prevState && prevState.tail_id === id ? 1 : 0;
      boxes.set(id, {
        x: lerp(from.x, target.x, t), y: lerp(from.y, target.y, t),
        w: lerp(from.w, target.w, t), h: lerp(from.h, target.h, t),
        index: target.index, slide: target.slide,
        alpha: wasNew ? t : 1,
        scale: wasNew ? 0.6 + 0.4 * t : 1,
        cur: lerp(oldCur, target.slide.is_current ? 1 : 0, t),
        head: lerp(oldHead, target.slide.is_head ? 1 : 0, t),
        tail: lerp(oldTail, state.tail_id === id ? 1 : 0, t)
      });
    });
    previous.layout.forEach(function (old, id) {
      if (self.layout.has(id)) { return; }
      var from = previous.shown.get(id) || old;
      boxes.set(id, {
        x: from.x, y: from.y, w: from.w, h: from.h,
        index: old.index, slide: old.slide,
        alpha: 1 - t, scale: 1 - 0.4 * t, cur: 0, head: 0, tail: 0
      });
    });

    // Remember what is on screen so a new render can start from here.
    this.shown = new Map();
    boxes.forEach(function (b, id) {
      if (self.layout.has(id)) { self.shown.set(id, { x: b.x, y: b.y, w: b.w, h: b.h }); }
    });

    var arrowMarkup = "";
    var count = state.slides.length;
    this.arrows.forEach(function (arrow, key) {
      var alpha = previous.arrows.has(key) ? 1 : t;
      arrowMarkup += self._arrowPath(arrow, boxes, alpha, count);
    });
    previous.arrows.forEach(function (arrow, key) {
      if (self.arrows.has(key)) { return; }
      arrowMarkup += self._arrowPath(arrow, boxes, 1 - t, previous.state ? previous.state.slides.length : count);
    });
    this.arrowLayer.innerHTML = arrowMarkup;

    var boxMarkup = "";
    var tagMarkup = "";
    boxes.forEach(function (b, id) {
      boxMarkup += self._boxMarkup(id, b);
      tagMarkup += self._tagMarkup(b);
    });
    this.boxLayer.innerHTML = boxMarkup;
    this.tagLayer.innerHTML = tagMarkup;

    this.centerLayer.innerHTML =
      '<text class="center-text" x="' + CENTER + '" y="' + (CENTER - 8) + '">size = ' + state.size + "</text>" +
      '<text class="center-text" x="' + CENTER + '" y="' + (CENTER + 12) + '">head.previous_slide = tail</text>' +
      '<text class="center-text" x="' + CENTER + '" y="' + (CENTER + 30) + '">tail.next_slide = head</text>';
  };

  CarouselVisualizer.prototype._arrowPath = function (arrow, boxes, alpha, count) {
    var a = boxes.get(arrow.from);
    var b = boxes.get(arrow.to);
    if (!a || !b || alpha <= 0.01) { return ""; }
    var cls = arrow.kind === "next" ? "arrow-next" : "arrow-prev";
    var marker = arrow.kind === "next" ? "arrow-next" : "arrow-prev";

    if (a === b) {
      // A lone slide points to itself: draw loops above (next) and below (previous).
      var up = arrow.kind === "next" ? -1 : 1;
      var edgeY = a.y + up * a.h / 2;
      var x1 = a.x + a.w / 4, x2 = a.x - a.w / 4;
      var d = "M" + x1 + "," + edgeY + " C" + x1 + "," + (edgeY + up * 48) + " " +
        x2 + "," + (edgeY + up * 48) + " " + x2 + "," + (edgeY + up * 3);
      return '<path class="' + cls + '" d="' + d + '" opacity="' + alpha + '" marker-end="url(#' + marker + ')"/>';
    }

    var dx = b.x - a.x, dy = b.y - a.y;
    var length = Math.sqrt(dx * dx + dy * dy) || 1;
    var ux = dx / length, uy = dy / length;
    var lane = arrow.kind === "prev" && count === 2 ? 24 : 9;
    var ox = -uy * lane, oy = ux * lane;
    var gapA = borderDistance(a.w, a.h, ux, uy) + 3;
    var gapB = borderDistance(b.w, b.h, ux, uy) + 4;
    if (length - gapA - gapB < 6) { return ""; }
    var sx = a.x + ox + ux * gapA, sy = a.y + oy + uy * gapA;
    var ex = b.x + ox - ux * gapB, ey = b.y + oy - uy * gapB;
    return '<path class="' + cls + '" d="M' + sx + "," + sy + " L" + ex + "," + ey +
      '" opacity="' + alpha + '" marker-end="url(#' + marker + ')"/>';
  };

  CarouselVisualizer.prototype._boxMarkup = function (id, b) {
    var w = b.w * b.scale, h = b.h * b.scale;
    var x = b.x - w / 2, y = b.y - h / 2;
    var classes = "box" + (b.head > 0.5 ? " is-head" : "") + (b.cur > 0.5 ? " is-current" : "");
    var showTitle = h >= 34;
    var maxChars = Math.max(4, Math.floor(w / 5.6));
    var title = b.slide.title.length > maxChars ? b.slide.title.slice(0, maxChars - 1) + "…" : b.slide.title;
    var indexY = showTitle ? b.y - 2 : b.y + 4.5;
    var markup = '<g data-id="' + escapeHtml(id) + '" opacity="' + b.alpha + '" style="cursor:pointer">' +
      '<title>' + escapeHtml(b.slide.title) + " (previous: " + escapeHtml(b.slide.previous_id) +
      ", next: " + escapeHtml(b.slide.next_id) + ")</title>" +
      '<rect class="' + classes + '" x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="9"/>';
    if (b.cur > 0.01) {
      markup += '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="9" ' +
        'fill="#4cd9a0" fill-opacity="' + (0.35 * b.cur) + '" stroke="#4cd9a0" stroke-opacity="' + b.cur + '" stroke-width="3"/>';
    }
    markup += '<text class="box-index" x="' + b.x + '" y="' + indexY + '">' + b.index + "</text>";
    if (showTitle) {
      markup += '<text class="box-title" x="' + b.x + '" y="' + (b.y + 12) + '">' + escapeHtml(title) + "</text>";
    }
    return markup + "</g>";
  };

  CarouselVisualizer.prototype._tagMarkup = function (b) {
    var tags = [];
    if (b.head > 0.01) { tags.push({ text: "HEAD", cls: "tag-head", alpha: b.head }); }
    if (b.cur > 0.01) { tags.push({ text: "CURRENT", cls: "tag-current", alpha: b.cur }); }
    if (b.tail > 0.01) { tags.push({ text: "TAIL", cls: "tag-tail", alpha: b.tail }); }
    if (!tags.length) { return ""; }

    var dx = b.x - CENTER, dy = b.y - CENTER;
    var length = Math.sqrt(dx * dx + dy * dy);
    var ux = length < 1 ? 0 : dx / length, uy = length < 1 ? -1 : dy / length;
    var start = borderDistance(b.w, b.h, ux, uy) + 12;
    var markup = "";
    tags.forEach(function (tag, i) {
      var px = b.x + ux * (start + i * 13);
      var py = b.y + uy * (start + i * 13) + 3;
      markup += '<text class="tag ' + tag.cls + '" x="' + px + '" y="' + py + '" opacity="' + (tag.alpha * b.alpha) + '">' +
        tag.text + "</text>";
    });
    return markup;
  };

  CarouselVisualizer.prototype._renderPointers = function (state) {
    var el = this.pointersEl;
    if (!state.slides.length) {
      el.innerHTML = "<p>head = null, current = null, size = 0</p>";
      return;
    }
    var byId = {};
    state.slides.forEach(function (s) { byId[s.id] = s; });
    var current = byId[state.current_id];
    var head = byId[state.head_id];
    var tail = byId[state.tail_id];
    function label(s) { return escapeHtml(s.title) + " (" + escapeHtml(s.id) + ")"; }
    el.innerHTML =
      "<table><thead><tr><th>current.previous_slide</th><th>current</th><th>current.next_slide</th></tr></thead>" +
      '<tbody><tr><td>' + label(byId[current.previous_id]) + '</td><td class="mid">' + label(current) +
      "</td><td>" + label(byId[current.next_id]) + "</td></tr></tbody></table>" +
      "<p>head = " + label(head) + " &nbsp;|&nbsp; tail = head.previous_slide = " + label(tail) + "</p>";
  };

  window.CarouselVisualizer = CarouselVisualizer;
})();
