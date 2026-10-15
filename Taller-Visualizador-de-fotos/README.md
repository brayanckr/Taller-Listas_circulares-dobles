# 360° Interactive Product Viewer

A Flask + vanilla JavaScript app that rotates a product through 360° using a
**doubly circular linked list** implemented from scratch.

## Run

```bash
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:5000.

## Project structure

```
run.py                     Entry point
app/
  __init__.py              App factory (creates list, seeds data)
  models.py                AngleFrame + AngleFrameList (the data structure)
  seed.py                  Initial 6 frames (generated SVG car placeholders)
  routes.py                Page + REST API blueprints
  templates/index.html     Dashboard
  static/css/styles.css
  static/js/app.js         fetch() calls, viewer, SVG diagram, CRUD
```

## Data structure

- `AngleFrame`: `frame_id`, `angle_degree`, `image_url`, `description`,
  plus `next_frame` / `prev_frame` pointers (a lone frame points to itself).
- `AngleFrameList`: `current_frame`, `head_frame`, `size`.
  - `insert_frame(angle_degree, image_url, description)` — inserts in ascending
    angle order, keeping the list circular (duplicate angles are rejected).
  - `delete_frame(frame_id)` — relinks neighbours; if the current frame is
    deleted, the pointer moves to its next frame.
  - `step_next()` / `step_prev()` — move the current pointer; the last frame
    wraps to the first and vice versa.
  - `get_current_frame_info()` — current frame plus its next/prev frames.
  - `get_all_frames()` — traversal from the head, flagged with
    current/next/prev roles for the diagram.

No Python list/dict/deque stores the frames; lists are only built when
serializing the response.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/frames/current` | Current frame with `next` / `prev` references |
| GET | `/api/frames/all` | All frames |
| POST | `/api/frames/next` | Move to next frame, return updated state |
| POST | `/api/frames/prev` | Move to previous frame, return updated state |
| POST | `/api/frames/add` | JSON `{angle_degree, image_url, description}` |
| DELETE | `/api/frames/delete/<frame_id>` | Delete a frame |
| GET | `/api/frames/state` | Current info + all frames (used by the UI) |

Errors return `{"error": "..."}` with status 400 or 404.

## UI

1. **Viewer** – image, title, description; `◀ Previous` / `Next ▶` buttons and
   ← / → keyboard keys.
2. **Visualizer** – frames on a circle with bidirectional arrows; current
   (green), previous (amber) and next (blue) are highlighted, and the
   last ↔ first link is drawn dashed in magenta.
3. **Management panel** – add a frame, or delete the current one.
