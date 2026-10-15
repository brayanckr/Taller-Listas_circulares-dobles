"""GalleryService: business logic between the carousel and the web routes."""

from __future__ import annotations

import io
import json
import threading
import uuid
from pathlib import Path
from typing import Any, BinaryIO, Dict, List

from PIL import Image, UnidentifiedImageError

from .photo import Photo
from .photo_carousel import PhotoCarousel
from .sample_images import generate_sample_images

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_TITLE_LENGTH = 60
MAX_DESCRIPTION_LENGTH = 300
INSERT_POSITIONS = ("first", "last", "after_current")
SAMPLE_PREFIX = "sample_"


class GalleryError(Exception):
    """Base class for errors that the web layer reports to the client."""


class ValidationError(GalleryError):
    """Raised when user input is invalid (HTTP 400)."""


class NotFoundError(GalleryError):
    """Raised when a requested photo does not exist (HTTP 404)."""


class GalleryService:
    """Validates input, manages image files and persists the carousel.

    The service owns the :class:`PhotoCarousel`. Every mutating operation is
    protected by a lock and followed by a save to the JSON file, so the order
    of the slides and the current slide survive a restart.
    """

    def __init__(
        self,
        data_file: Path,
        upload_dir: Path,
        url_prefix: str = "/static/uploads",
        seed_samples: bool = True,
    ) -> None:
        """Create the service and load (or seed) the gallery.

        Args:
            data_file: JSON file used for persistence.
            upload_dir: Directory where image files are stored.
            url_prefix: URL under which ``upload_dir`` is served.
            seed_samples: Generate sample pictures when no data file exists.
        """
        self._data_file = Path(data_file)
        self._upload_dir = Path(upload_dir)
        self._url_prefix = url_prefix.rstrip("/")
        self._carousel = PhotoCarousel()
        self._lock = threading.RLock()
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        if self._data_file.exists():
            self._load()
        elif seed_samples:
            self._seed_samples()
            self._save()

    @property
    def carousel(self) -> PhotoCarousel:
        """The underlying doubly circular linked list."""
        return self._carousel

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def get_state(self) -> Dict[str, Any]:
        """Return the full gallery state for the frontend."""
        with self._lock:
            carousel = self._carousel
            head = carousel.head
            current = carousel.current
            return {
                "slides": carousel.to_list(),
                "size": len(carousel),
                "head_id": head.photo.id if head else None,
                "tail_id": carousel.tail.photo.id if head else None,
                "current_id": current.photo.id if current else None,
                "position": carousel.current_position,
            }

    def search(self, text: str) -> List[Dict[str, Any]]:
        """Return photos whose title contains ``text``."""
        with self._lock:
            return [p.to_dict() for p in self._carousel.search_by_title(text)]

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------
    def add_photo(
        self,
        title: str,
        description: str,
        filename: str,
        stream: BinaryIO,
        position: str = "last",
    ) -> Photo:
        """Validate and store an uploaded picture, then insert it.

        Args:
            title: Photo title (required).
            description: Optional description.
            filename: Original filename, used only to read the extension.
            stream: Binary stream with the image content.
            position: ``"first"``, ``"last"`` or ``"after_current"``.

        Raises:
            ValidationError: If any input is invalid.
        """
        title = (title or "").strip()
        description = (description or "").strip()
        if not title:
            raise ValidationError("The title is required.")
        if len(title) > MAX_TITLE_LENGTH:
            raise ValidationError(f"The title must have at most {MAX_TITLE_LENGTH} characters.")
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise ValidationError(
                f"The description must have at most {MAX_DESCRIPTION_LENGTH} characters."
            )
        if position not in INSERT_POSITIONS:
            raise ValidationError(f"Position must be one of: {', '.join(INSERT_POSITIONS)}.")
        extension = Path(filename or "").suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                "Unsupported image type. Allowed: "
                + ", ".join(sorted(e.lstrip(".") for e in ALLOWED_EXTENSIONS))
                + "."
            )

        content = stream.read()
        try:
            with Image.open(io.BytesIO(content)) as image:
                image.verify()
        except (UnidentifiedImageError, OSError, SyntaxError):
            raise ValidationError("The uploaded file is not a valid image.") from None

        stored_name = f"{uuid.uuid4().hex}{extension}"
        (self._upload_dir / stored_name).write_bytes(content)
        photo = Photo(title, f"{self._url_prefix}/{stored_name}", description)

        with self._lock:
            if position == "first":
                self._carousel.add_first(photo)
            elif position == "last":
                self._carousel.add_last(photo)
            else:
                self._carousel.add_after_current(photo)
            self._save()
        return photo

    def remove_current(self) -> Photo:
        """Remove the current photo.

        Raises:
            NotFoundError: If the gallery is empty.
        """
        with self._lock:
            photo = self._carousel.remove_current()
            if photo is None:
                raise NotFoundError("The gallery is empty.")
            self._delete_file(photo)
            self._save()
            return photo

    def remove_photo(self, photo_id: str) -> Photo:
        """Remove the photo with ``photo_id``.

        Raises:
            NotFoundError: If no such photo exists.
        """
        with self._lock:
            photo = self._carousel.remove_by_id(photo_id)
            if photo is None:
                raise NotFoundError(f"Photo '{photo_id}' was not found.")
            self._delete_file(photo)
            self._save()
            return photo

    def next(self) -> None:
        """Move the current slide forward."""
        with self._lock:
            self._carousel.move_next()
            self._save()

    def previous(self) -> None:
        """Move the current slide backward."""
        with self._lock:
            self._carousel.move_previous()
            self._save()

    def go_to(self, photo_id: str) -> None:
        """Jump to a photo.

        Raises:
            NotFoundError: If no such photo exists.
        """
        with self._lock:
            if not self._carousel.go_to(photo_id):
                raise NotFoundError(f"Photo '{photo_id}' was not found.")
            self._save()

    def shuffle(self) -> None:
        """Randomly reorder the slides."""
        with self._lock:
            self._carousel.shuffle_order()
            self._save()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _save(self) -> None:
        """Write the order, metadata and current slide to the JSON file."""
        payload = {
            "current_id": (
                self._carousel.current.photo.id if self._carousel.current else None
            ),
            "photos": [slide.photo.to_dict() for slide in self._carousel],
        }
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self._data_file.with_suffix(".tmp")
        temp_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temp_file.replace(self._data_file)

    def _load(self) -> None:
        """Rebuild the linked list from the JSON file."""
        try:
            payload = json.loads(self._data_file.read_text(encoding="utf-8"))
            photos = [Photo.from_dict(item) for item in payload.get("photos", [])]
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise GalleryError(f"Could not read {self._data_file}: {error}") from error
        for photo in photos:
            self._carousel.add_last(photo)
        current_id = payload.get("current_id")
        if current_id:
            self._carousel.go_to(current_id)

    def _seed_samples(self) -> None:
        """Generate sample pictures and add them to the carousel."""
        for title, description, filename in generate_sample_images(self._upload_dir):
            self._carousel.add_last(Photo(title, f"{self._url_prefix}/{filename}", description))

    def _delete_file(self, photo: Photo) -> None:
        """Delete an uploaded image file (sample pictures are kept)."""
        name = photo.image_url.rsplit("/", 1)[-1]
        if name.startswith(SAMPLE_PREFIX):
            return
        path = self._upload_dir / name
        if path.is_file():
            path.unlink()
