from flask import Blueprint, current_app, jsonify, render_template, request

pages_bp = Blueprint("pages", __name__)
api_bp = Blueprint("api", __name__)


def _frames():
    return current_app.config["FRAME_LIST"]


def _state():
    """Full state payload so the client can refresh viewer and diagram at once."""
    frames = _frames()
    state = frames.get_current_frame_info()
    state["frames"] = [] if frames.is_empty() else frames.get_all_frames()
    return state


@pages_bp.get("/")
def index():
    return render_template("index.html")


@api_bp.get("/frames/current")
def get_current():
    return jsonify(_frames().get_current_frame_info())


@api_bp.get("/frames/all")
def get_all():
    frames = _frames()
    return jsonify({
        "frames": [] if frames.is_empty() else frames.get_all_frames(),
        "size": frames.size,
    })


@api_bp.get("/frames/state")
def get_state():
    return jsonify(_state())


@api_bp.post("/frames/next")
def post_next():
    _frames().step_next()
    return jsonify(_state())


@api_bp.post("/frames/prev")
def post_prev():
    _frames().step_prev()
    return jsonify(_state())


@api_bp.post("/frames/add")
def post_add():
    data = request.get_json(silent=True) or {}
    try:
        angle = int(data.get("angle_degree"))
    except (TypeError, ValueError):
        return jsonify({"error": "angle_degree must be an integer"}), 400
    try:
        frame = _frames().insert_frame(
            angle,
            str(data.get("image_url", "")).strip(),
            str(data.get("description", "")).strip(),
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    state = _state()
    state["added"] = frame.to_dict()
    return jsonify(state), 201


@api_bp.delete("/frames/delete/<int:frame_id>")
def delete_frame(frame_id):
    if _frames().delete_frame(frame_id) is None:
        return jsonify({"error": f"Frame {frame_id} not found"}), 404
    return jsonify(_state())
