"""Flask application: HTML page and JSON REST API for the photo gallery."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Tuple

from flask import Flask, jsonify, render_template, request
from flask.typing import ResponseReturnValue

from gallery import GalleryError, GalleryService, NotFoundError, ValidationError

BASE_DIR = Path(__file__).resolve().parent


def create_app(
    data_file: Optional[Path] = None,
    upload_dir: Optional[Path] = None,
    seed_samples: bool = True,
) -> Flask:
    """Application factory.

    Args:
        data_file: JSON persistence file (defaults to ``data/gallery.json``).
        upload_dir: Image directory (defaults to ``static/uploads``).
        seed_samples: Generate sample pictures on the very first run.
    """
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB per upload
    service = GalleryService(
        data_file=data_file or BASE_DIR / "data" / "gallery.json",
        upload_dir=upload_dir or BASE_DIR / "static" / "uploads",
        seed_samples=seed_samples,
    )
    app.extensions["gallery_service"] = service

    def state_response(message: str = "", status: int = 200) -> Tuple[Any, int]:
        return jsonify({"message": message, "state": service.get_state()}), status

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/api/carousel")
    def get_carousel() -> ResponseReturnValue:
        return jsonify(service.get_state())

    @app.post("/api/slides")
    def add_slide() -> ResponseReturnValue:
        upload = request.files.get("image")
        if upload is None or not upload.filename:
            raise ValidationError("An image file is required.")
        photo = service.add_photo(
            title=request.form.get("title", ""),
            description=request.form.get("description", ""),
            filename=upload.filename,
            stream=upload.stream,
            position=request.form.get("position", "last"),
        )
        return state_response(f"Added '{photo.title}'.", 201)

    @app.delete("/api/slides/current")
    def delete_current() -> ResponseReturnValue:
        photo = service.remove_current()
        return state_response(f"Removed '{photo.title}'.")

    @app.delete("/api/slides/<photo_id>")
    def delete_slide(photo_id: str) -> ResponseReturnValue:
        photo = service.remove_photo(photo_id)
        return state_response(f"Removed '{photo.title}'.")

    @app.post("/api/navigate/next")
    def navigate_next() -> ResponseReturnValue:
        service.next()
        return state_response()

    @app.post("/api/navigate/previous")
    def navigate_previous() -> ResponseReturnValue:
        service.previous()
        return state_response()

    @app.post("/api/navigate/goto/<photo_id>")
    def navigate_goto(photo_id: str) -> ResponseReturnValue:
        service.go_to(photo_id)
        return state_response()

    @app.post("/api/shuffle")
    def shuffle() -> ResponseReturnValue:
        service.shuffle()
        return state_response("Slides shuffled by relinking.")

    @app.get("/api/search")
    def search() -> ResponseReturnValue:
        return jsonify({"query": request.args.get("q", ""), "results": service.search(request.args.get("q", ""))})

    @app.errorhandler(ValidationError)
    def handle_validation(error: ValidationError) -> ResponseReturnValue:
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(NotFoundError)
    def handle_not_found(error: NotFoundError) -> ResponseReturnValue:
        return jsonify({"error": str(error)}), 404

    @app.errorhandler(GalleryError)
    def handle_gallery_error(error: GalleryError) -> ResponseReturnValue:
        return jsonify({"error": str(error)}), 500

    @app.errorhandler(413)
    def handle_too_large(_: Exception) -> ResponseReturnValue:
        return jsonify({"error": "The image is too large (max 8 MB)."}), 413

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5001, debug=False)
