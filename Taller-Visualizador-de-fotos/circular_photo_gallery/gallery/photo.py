"""Photo: the plain data record stored inside each slide of the carousel."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class Photo:
    """Data-only description of a gallery picture.

    A photo knows nothing about the carousel; it only carries information.
    """

    def __init__(
        self,
        title: str,
        image_url: str,
        description: str = "",
        photo_id: Optional[str] = None,
        upload_date: Optional[str] = None,
    ) -> None:
        """Create a photo.

        Args:
            title: Short human readable title.
            image_url: Public URL (or path) of the image file.
            description: Optional longer text shown below the picture.
            photo_id: Unique identifier; generated when omitted.
            upload_date: ISO-8601 timestamp; the current UTC time when omitted.
        """
        self._id = photo_id or uuid.uuid4().hex[:8]
        self.title = title
        self.description = description
        self.image_url = image_url
        self._upload_date = upload_date or datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )

    @property
    def id(self) -> str:
        """Unique identifier of the photo (read-only)."""
        return self._id

    @property
    def upload_date(self) -> str:
        """ISO-8601 upload timestamp (read-only)."""
        return self._upload_date

    def to_dict(self) -> Dict[str, Any]:
        """Return the photo as a JSON-serializable dictionary."""
        return {
            "id": self._id,
            "title": self.title,
            "description": self.description,
            "image_url": self.image_url,
            "upload_date": self._upload_date,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Photo":
        """Rebuild a photo from the dictionary produced by :meth:`to_dict`."""
        return cls(
            title=data["title"],
            image_url=data["image_url"],
            description=data.get("description", ""),
            photo_id=data["id"],
            upload_date=data.get("upload_date"),
        )

    def __repr__(self) -> str:
        return f"Photo(id={self._id!r}, title={self.title!r})"
