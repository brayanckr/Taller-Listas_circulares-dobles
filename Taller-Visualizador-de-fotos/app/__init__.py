from flask import Flask

from .models import AngleFrameList
from .routes import api_bp, pages_bp
from .seed import load_seed_frames


def create_app() -> Flask:
    app = Flask(__name__)
    frames = AngleFrameList()
    load_seed_frames(frames)
    app.config["FRAME_LIST"] = frames
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    return app
