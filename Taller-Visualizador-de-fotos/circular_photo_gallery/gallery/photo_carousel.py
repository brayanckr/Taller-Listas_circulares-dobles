"""PhotoCarousel: a hand-made doubly circular linked list of slides."""

from __future__ import annotations

import random
from typing import Any, Dict, Iterator, List, Optional

from .photo import Photo
from .slide import Slide


class PhotoCarousel:
    """Doubly circular linked list that stores the gallery slides.

    Invariants (kept by every operation):

    * An empty carousel has ``head is None`` and ``current is None``.
    * Otherwise ``head`` and ``current`` are slides of the list.
    * Following ``next_slide`` from ``head`` visits every slide exactly once
      and then returns to ``head``; following ``previous_slide`` does the
      same in the opposite direction.
    * ``head.previous_slide`` is the last slide (the *tail*) and
      ``tail.next_slide`` is ``head``.
    * ``size`` equals the number of slides in the circle.

    No Python list, deque or dict stores the slides: the only way to reach a
    slide is to follow the links.
    """

    def __init__(self) -> None:
        """Create an empty carousel."""
        self._head: Optional[Slide] = None
        self._current: Optional[Slide] = None
        self._size = 0

    # ------------------------------------------------------------------
    # Basic properties
    # ------------------------------------------------------------------
    @property
    def head(self) -> Optional[Slide]:
        """First slide of the list (``None`` when empty)."""
        return self._head

    @property
    def current(self) -> Optional[Slide]:
        """Slide currently shown by the viewer (``None`` when empty)."""
        return self._current

    @property
    def size(self) -> int:
        """Number of slides in the carousel."""
        return self._size

    @property
    def tail(self) -> Optional[Slide]:
        """Last slide of the list, i.e. ``head.previous_slide``."""
        return self._head.previous_slide if self._head else None

    @property
    def current_position(self) -> int:
        """1-based position of ``current`` counted from ``head`` (0 if empty)."""
        for position, slide in enumerate(self, start=1):
            if slide is self._current:
                return position
        return 0

    def is_empty(self) -> bool:
        """Return ``True`` when the carousel holds no slides."""
        return self._size == 0

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Slide]:
        """Yield every slide once, from ``head`` forward (one full lap)."""
        if self._head is None:
            return
        slide = self._head
        while True:
            yield slide
            slide = slide.next_slide
            if slide is self._head:
                break

    def traverse_backward(self) -> Iterator[Slide]:
        """Yield every slide once, from the tail back to ``head``."""
        if self._head is None:
            return
        slide = self._head.previous_slide
        while True:
            yield slide
            if slide is self._head:
                break
            slide = slide.previous_slide

    # ------------------------------------------------------------------
    # Insertion
    # ------------------------------------------------------------------
    def add_first(self, photo: Photo) -> Slide:
        """Insert ``photo`` before ``head``; the new slide becomes the head."""
        slide = Slide(photo)
        if self._head is None:
            self._start_circle(slide)
        else:
            self._insert_between(slide, self._head.previous_slide, self._head)
            self._head = slide
            self._size += 1
        return slide

    def add_last(self, photo: Photo) -> Slide:
        """Insert ``photo`` after the tail (just before ``head``)."""
        slide = Slide(photo)
        if self._head is None:
            self._start_circle(slide)
        else:
            self._insert_between(slide, self._head.previous_slide, self._head)
            self._size += 1
        return slide

    def add_after_current(self, photo: Photo) -> Slide:
        """Insert ``photo`` right after ``current``; ``current`` is unchanged."""
        if self._current is None:
            return self.add_first(photo)
        slide = Slide(photo)
        self._insert_between(slide, self._current, self._current.next_slide)
        self._size += 1
        return slide

    # ------------------------------------------------------------------
    # Removal
    # ------------------------------------------------------------------
    def remove_current(self) -> Optional[Photo]:
        """Remove ``current`` and return its photo (``None`` if empty).

        The new ``current`` is the slide that followed the removed one.
        """
        if self._current is None:
            return None
        return self._unlink(self._current)

    def remove_by_id(self, photo_id: str) -> Optional[Photo]:
        """Remove the slide holding ``photo_id``.

        Returns the removed photo, or ``None`` if the carousel is empty or
        the id is not present.
        """
        slide = self.find_slide(photo_id)
        if slide is None:
            return None
        return self._unlink(slide)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def move_next(self) -> Optional[Slide]:
        """Move ``current`` one slide forward, wrapping from tail to head."""
        if self._current is not None:
            self._current = self._current.next_slide
        return self._current

    def move_previous(self) -> Optional[Slide]:
        """Move ``current`` one slide backward, wrapping from head to tail."""
        if self._current is not None:
            self._current = self._current.previous_slide
        return self._current

    def go_to(self, photo_id: str) -> bool:
        """Make the slide holding ``photo_id`` the current one.

        Returns ``False`` (leaving ``current`` untouched) if it is not found.
        """
        slide = self.find_slide(photo_id)
        if slide is None:
            return False
        self._current = slide
        return True

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def find_slide(self, photo_id: str) -> Optional[Slide]:
        """Return the slide holding ``photo_id`` or ``None`` (one lap max)."""
        for slide in self:
            if slide.photo.id == photo_id:
                return slide
        return None

    def search_by_title(self, text: str) -> List[Photo]:
        """Return photos whose title contains ``text`` (case-insensitive).

        The circle is traversed exactly once, so the search always ends.
        """
        needle = text.strip().lower()
        if not needle:
            return []
        return [s.photo for s in self if needle in s.photo.title.lower()]

    # ------------------------------------------------------------------
    # Reordering
    # ------------------------------------------------------------------
    def shuffle_order(self, rng: Optional[random.Random] = None) -> None:
        """Randomly reorder the slides by relinking them.

        The circle is opened into a linear chain, then each slide is
        re-inserted into a new circle at a random place. Slide objects (and
        their photos) are never copied, only their ``next_slide`` and
        ``previous_slide`` references change. ``current`` keeps pointing at
        the same slide.
        """
        if self._size < 2:
            return
        rng = rng or random.Random()
        self._head.previous_slide.next_slide = None  # open the circle
        pending: Optional[Slide] = self._head
        new_head: Optional[Slide] = None
        placed = 0
        while pending is not None:
            following = pending.next_slide
            if new_head is None:
                pending.link_to_itself()
                new_head = pending
            else:
                offset = rng.randint(0, placed)
                anchor = new_head
                for _ in range(offset):
                    anchor = anchor.next_slide
                self._insert_between(pending, anchor.previous_slide, anchor)
                if offset == 0:
                    new_head = pending
            placed += 1
            pending = following
        self._head = new_head

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def to_list(self) -> List[Dict[str, Any]]:
        """Return one dictionary per slide, in order from ``head``.

        Each dictionary has the photo fields plus ``previous_id`` and
        ``next_id`` (the ids of the neighbouring slides) and the flags
        ``is_head`` and ``is_current``. The visualizer draws from this data.
        """
        result: List[Dict[str, Any]] = []
        for slide in self:
            data = slide.photo.to_dict()
            data["previous_id"] = slide.previous_slide.photo.id
            data["next_id"] = slide.next_slide.photo.id
            data["is_head"] = slide is self._head
            data["is_current"] = slide is self._current
            result.append(data)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _start_circle(self, slide: Slide) -> None:
        """Make ``slide`` the only element of an empty carousel."""
        slide.link_to_itself()
        self._head = slide
        self._current = slide
        self._size = 1

    @staticmethod
    def _insert_between(slide: Slide, before: Slide, after: Slide) -> None:
        """Link ``slide`` between two adjacent slides (may be the same one)."""
        slide.previous_slide = before
        slide.next_slide = after
        before.next_slide = slide
        after.previous_slide = slide

    def _unlink(self, slide: Slide) -> Photo:
        """Detach ``slide`` from the circle and repair head/current/size."""
        photo = slide.photo
        if self._size == 1:
            self._head = None
            self._current = None
            self._size = 0
        else:
            before = slide.previous_slide
            after = slide.next_slide
            before.next_slide = after
            after.previous_slide = before
            if slide is self._head:
                self._head = after
            if slide is self._current:
                self._current = after
            self._size -= 1
        slide.next_slide = None
        slide.previous_slide = None
        return photo
