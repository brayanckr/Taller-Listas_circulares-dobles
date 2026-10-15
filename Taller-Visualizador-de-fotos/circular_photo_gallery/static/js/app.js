/**
 * Circular Photo Gallery - frontend controller.
 *
 * Talks to the JSON REST API, renders the viewer and the thumbnail strip,
 * drives autoplay and feeds the data structure visualizer.
 */
(function () {
  "use strict";

  var els = {
    image: document.getElementById("main-image"),
    empty: document.getElementById("empty-message"),
    title: document.getElementById("photo-title"),
    description: document.getElementById("photo-description"),
    counter: document.getElementById("counter"),
    thumbs: document.getElementById("thumbs"),
    prev: document.getElementById("btn-prev"),
    next: document.getElementById("btn-next"),
    play: document.getElementById("btn-play"),
    direction: document.getElementById("btn-direction"),
    speed: document.getElementById("speed"),
    del: document.getElementById("btn-delete"),
    shuffle: document.getElementById("btn-shuffle"),
    uploadForm: document.getElementById("upload-form"),
    searchForm: document.getElementById("search-form"),
    searchInput: document.getElementById("search-input"),
    results: document.getElementById("results"),
    toast: document.getElementById("toast")
  };

  var state = null;
  var direction = "forward";
  var timer = null;
  var toastTimer = null;
  var searchTimer = null;

  var visualizer = new window.CarouselVisualizer(
    document.getElementById("viz"),
    document.getElementById("pointers"),
    function (id) { run("POST", "/api/navigate/goto/" + encodeURIComponent(id), null, "fade"); }
  );

  // ---------------------------------------------------------------- API
  function request(method, url, body) {
    var options = { method: method };
    if (body) { options.body = body; }
    return fetch(url, options).then(function (response) {
      return response.json().then(function (data) {
        if (!response.ok) { throw new Error(data.error || "Request failed."); }
        return data;
      });
    });
  }

  /** Send a command and render the state it returns. */
  function run(method, url, body, slideEffect, quiet) {
    return request(method, url, body).then(function (data) {
      applyState(data.state, slideEffect);
      if (data.message && !quiet) { showToast(data.message); }
      return data;
    }).catch(function (error) {
      showToast(error.message, true);
    });
  }

  // ------------------------------------------------------------ Rendering
  function applyState(newState, slideEffect) {
    var previousId = state ? state.current_id : null;
    state = newState;
    renderViewer(previousId !== state.current_id || !previousId ? slideEffect || "fade" : null);
    renderThumbs();
    visualizer.render(state);
  }

  function currentSlide() {
    for (var i = 0; i < state.slides.length; i++) {
      if (state.slides[i].id === state.current_id) { return state.slides[i]; }
    }
    return null;
  }

  function renderViewer(effect) {
    var slide = currentSlide();
    els.counter.textContent = state.position + " / " + state.size;
    els.empty.hidden = !!slide;
    els.image.hidden = !slide;
    if (!slide) {
      els.title.textContent = "No photos";
      els.description.textContent = "";
      return;
    }
    els.title.textContent = slide.title;
    els.description.textContent = slide.description;
    if (effect) {
      els.image.src = slide.image_url;
      els.image.alt = slide.title;
      els.image.classList.remove("slide-forward", "slide-backward", "fade");
      void els.image.offsetWidth; // restart the CSS animation
      els.image.classList.add(effect === "forward" ? "slide-forward" : effect === "backward" ? "slide-backward" : "fade");
    }
  }

  function renderThumbs() {
    els.thumbs.innerHTML = "";
    var active = null;
    state.slides.forEach(function (slide) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "thumb" + (slide.is_current ? " active" : "");
      button.title = slide.title;
      button.setAttribute("role", "option");
      button.setAttribute("aria-selected", slide.is_current ? "true" : "false");
      var img = document.createElement("img");
      img.src = slide.image_url;
      img.alt = slide.title;
      button.appendChild(img);
      button.addEventListener("click", function () {
        run("POST", "/api/navigate/goto/" + encodeURIComponent(slide.id), null, "fade", true);
      });
      els.thumbs.appendChild(button);
      if (slide.is_current) { active = button; }
    });
    if (active) { active.scrollIntoView({ inline: "center", block: "nearest" }); }
  }

  function showToast(message, isError) {
    els.toast.textContent = message;
    els.toast.className = "toast show" + (isError ? " error" : "");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { els.toast.className = "toast"; }, 2600);
  }

  // ----------------------------------------------------------- Navigation
  function goNext() { return run("POST", "/api/navigate/next", null, "forward", true); }
  function goPrevious() { return run("POST", "/api/navigate/previous", null, "backward", true); }

  function userNavigate(step) {
    step();
    if (timer) { startAutoplay(); } // restart the interval after manual navigation
  }

  function startAutoplay() {
    stopTimer();
    timer = setInterval(function () {
      if (direction === "forward") { goNext(); } else { goPrevious(); }
    }, parseInt(els.speed.value, 10));
    els.play.innerHTML = "&#10074;&#10074; Pause";
  }

  function stopTimer() {
    if (timer) { clearInterval(timer); timer = null; }
  }

  function stopAutoplay() {
    stopTimer();
    els.play.innerHTML = "&#9654; Play";
  }

  els.next.addEventListener("click", function () { userNavigate(goNext); });
  els.prev.addEventListener("click", function () { userNavigate(goPrevious); });
  els.play.addEventListener("click", function () { if (timer) { stopAutoplay(); } else { startAutoplay(); } });
  els.speed.addEventListener("change", function () { if (timer) { startAutoplay(); } });
  els.direction.addEventListener("click", function () {
    direction = direction === "forward" ? "backward" : "forward";
    els.direction.innerHTML = direction === "forward" ? "Direction: forward &#8594;" : "Direction: backward &#8592;";
  });

  document.addEventListener("keydown", function (event) {
    var tag = event.target && event.target.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") { return; }
    if (event.key === "ArrowRight") { event.preventDefault(); userNavigate(goNext); }
    if (event.key === "ArrowLeft") { event.preventDefault(); userNavigate(goPrevious); }
  });

  // -------------------------------------------------------------- Actions
  els.del.addEventListener("click", function () {
    run("DELETE", "/api/slides/current", null, "fade");
  });

  els.shuffle.addEventListener("click", function () {
    run("POST", "/api/shuffle", null, null);
  });

  els.uploadForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var form = els.uploadForm;
    run("POST", "/api/slides", new FormData(form), "fade").then(function (data) {
      if (data) { form.reset(); }
    });
  });

  // --------------------------------------------------------------- Search
  function search() {
    var query = els.searchInput.value.trim();
    els.results.innerHTML = "";
    if (!query) { return; }
    request("GET", "/api/search?q=" + encodeURIComponent(query)).then(function (data) {
      if (!data.results.length) {
        var none = document.createElement("li");
        none.className = "none";
        none.textContent = "No photo matches \"" + query + "\".";
        els.results.appendChild(none);
        return;
      }
      data.results.forEach(function (photo) {
        var item = document.createElement("li");
        var button = document.createElement("button");
        button.type = "button";
        button.textContent = photo.title;
        button.addEventListener("click", function () {
          run("POST", "/api/navigate/goto/" + encodeURIComponent(photo.id), null, "fade", true);
        });
        item.appendChild(button);
        els.results.appendChild(item);
      });
    }).catch(function (error) { showToast(error.message, true); });
  }

  els.searchForm.addEventListener("submit", function (event) { event.preventDefault(); search(); });
  els.searchInput.addEventListener("input", function () {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(search, 250);
  });

  // ----------------------------------------------------------------- Init
  request("GET", "/api/carousel").then(function (data) {
    applyState(data, "fade");
  }).catch(function (error) { showToast(error.message, true); });
})();
