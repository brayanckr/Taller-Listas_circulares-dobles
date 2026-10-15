"""Tests for GalleryService (persistence, validation) and the REST API."""

import io
import json

import pytest
from PIL import Image

from app import create_app
from gallery import GalleryService, NotFoundError, ValidationError


def png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def service(tmp_path):
    return GalleryService(tmp_path / "gallery.json", tmp_path / "uploads", seed_samples=False)


def add(service, title="Photo", position="last"):
    return service.add_photo(title, "desc", "pic.png", io.BytesIO(png_bytes()), position)


class TestService:
    def test_starts_empty_without_samples(self, service):
        assert service.get_state()["size"] == 0

    def test_samples_are_seeded_on_first_run(self, tmp_path):
        seeded = GalleryService(tmp_path / "g.json", tmp_path / "up")
        assert 6 <= seeded.get_state()["size"] <= 8
        assert (tmp_path / "g.json").exists()

    def test_add_positions(self, service):
        add(service, "B")
        add(service, "A", "first")
        add(service, "C", "last")
        add(service, "X", "after_current")  # current is still B (the first photo added)
        titles = [s["title"] for s in service.get_state()["slides"]]
        assert titles == ["A", "B", "X", "C"]

    def test_validation_errors(self, service):
        with pytest.raises(ValidationError):
            service.add_photo("  ", "", "a.png", io.BytesIO(png_bytes()))
        with pytest.raises(ValidationError):
            service.add_photo("T", "", "a.exe", io.BytesIO(png_bytes()))
        with pytest.raises(ValidationError):
            service.add_photo("T", "", "a.png", io.BytesIO(b"not an image"))
        with pytest.raises(ValidationError):
            service.add_photo("T", "", "a.png", io.BytesIO(png_bytes()), "middle")
        with pytest.raises(ValidationError):
            service.add_photo("T" * 100, "", "a.png", io.BytesIO(png_bytes()))
        assert service.get_state()["size"] == 0

    def test_remove_current_and_empty_error(self, service):
        add(service, "A")
        service.remove_current()
        assert service.get_state()["size"] == 0
        with pytest.raises(NotFoundError):
            service.remove_current()

    def test_remove_deletes_uploaded_file(self, service, tmp_path):
        photo = add(service, "A")
        stored = tmp_path / "uploads" / photo.image_url.rsplit("/", 1)[-1]
        assert stored.exists()
        service.remove_photo(photo.id)
        assert not stored.exists()

    def test_remove_unknown_and_goto_unknown(self, service):
        with pytest.raises(NotFoundError):
            service.remove_photo("nope")
        with pytest.raises(NotFoundError):
            service.go_to("nope")

    def test_state_has_head_tail_and_position(self, service):
        for name in "ABC":
            add(service, name)
        service.next()
        state = service.get_state()
        assert state["position"] == 2
        assert state["tail_id"] == state["slides"][0]["previous_id"]

    def test_persistence_round_trip(self, tmp_path):
        first = GalleryService(tmp_path / "g.json", tmp_path / "up", seed_samples=False)
        for name in "ABCD":
            add(first, name)
        first.next()
        first.next()
        first.shuffle()
        saved = first.get_state()

        second = GalleryService(tmp_path / "g.json", tmp_path / "up", seed_samples=False)
        restored = second.get_state()
        assert [s["id"] for s in restored["slides"]] == [s["id"] for s in saved["slides"]]
        assert restored["current_id"] == saved["current_id"]
        assert restored["tail_id"] == saved["tail_id"]

    def test_json_file_content(self, service, tmp_path):
        add(service, "A")
        payload = json.loads((tmp_path / "gallery.json").read_text(encoding="utf-8"))
        assert payload["photos"][0]["title"] == "A"
        assert payload["current_id"] == payload["photos"][0]["id"]

    def test_search(self, service):
        add(service, "Beach")
        add(service, "Forest")
        assert [p["title"] for p in service.search("bea")] == ["Beach"]


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path / "g.json", tmp_path / "up", seed_samples=False)
    return app.test_client()


def upload(client, title="Pic", position="last"):
    return client.post(
        "/api/slides",
        data={"title": title, "description": "d", "position": position,
              "image": (io.BytesIO(png_bytes()), "x.png")},
        content_type="multipart/form-data",
    )


class TestApi:
    def test_index_page(self, client):
        assert client.get("/").status_code == 200

    def test_empty_carousel(self, client):
        data = client.get("/api/carousel").get_json()
        assert data["size"] == 0 and data["current_id"] is None

    def test_upload_navigate_delete_flow(self, client):
        assert upload(client, "A").status_code == 201
        assert upload(client, "B").status_code == 201
        state = client.post("/api/navigate/next").get_json()["state"]
        assert state["position"] == 2
        state = client.post("/api/navigate/next").get_json()["state"]
        assert state["position"] == 1  # wrapped around
        state = client.post("/api/navigate/previous").get_json()["state"]
        assert state["position"] == 2
        state = client.delete("/api/slides/current").get_json()["state"]
        assert state["size"] == 1

    def test_goto_search_shuffle_and_delete_by_id(self, client):
        for title in ("Alpha", "Beta", "Gamma"):
            upload(client, title)
        slides = client.get("/api/carousel").get_json()["slides"]
        target = slides[2]["id"]
        assert client.post(f"/api/navigate/goto/{target}").get_json()["state"]["current_id"] == target
        results = client.get("/api/search?q=bet").get_json()["results"]
        assert [r["title"] for r in results] == ["Beta"]
        assert client.post("/api/shuffle").status_code == 200
        assert client.delete(f"/api/slides/{target}").get_json()["state"]["size"] == 2

    def test_errors(self, client):
        assert upload(client, "").status_code == 400
        assert client.post("/api/slides", data={"title": "x"}).status_code == 400
        assert client.delete("/api/slides/current").status_code == 404
        assert client.delete("/api/slides/nope").status_code == 404
        assert client.post("/api/navigate/goto/nope").status_code == 404
        assert client.post("/api/navigate/next").status_code == 200  # empty gallery is fine
