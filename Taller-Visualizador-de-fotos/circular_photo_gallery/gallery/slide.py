"""Slide: one element of the doubly circular linked list."""

from __future__ import annotations

from typing import Optional

from .photo import Photo


class Slide:
    """A single link of the carousel chain.

    A slide stores one :class:`Photo` plus two references: the slide that
    follows it (``next_slide``) and the slide that precedes it
    (``previous_slide``). Inside a :class:`PhotoCarousel` these references are
    never ``None``: a lone slide points to itself in both directions.
    """

    def __init__(self, photo: Photo) -> None:
        """Create an unlinked slide holding ``photo``."""
        self._photo = photo
        self._next_slide: Optional[Slide] = None
        self._previous_slide: Optional[Slide] = None

    @property
    def photo(self) -> Photo:
        """The photo carried by this slide."""
        return self._photo

    @property
    def next_slide(self) -> Optional["Slide"]:
        """The slide after this one (clockwise direction)."""
        return self._next_slide

    @next_slide.setter
    def next_slide(self, slide: Optional["Slide"]) -> None:
        self._next_slide = slide

    @property
    def previous_slide(self) -> Optional["Slide"]:
        """The slide before this one (counter-clockwise direction)."""
        return self._previous_slide

    @previous_slide.setter
    def previous_slide(self, slide: Optional["Slide"]) -> None:
        self._previous_slide = slide

    def link_to_itself(self) -> None:
        """Make the slide a one-element circle."""
        self._next_slide = self
        self._previous_slide = self

    def __repr__(self) -> str:
        return f"Slide(photo_id={self._photo.id!r})"
