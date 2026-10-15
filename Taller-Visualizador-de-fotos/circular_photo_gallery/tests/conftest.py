"""Shared test helpers."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gallery import Photo, PhotoCarousel  # noqa: E402


def make_photo(name: str) -> Photo:
    """Build a photo whose id equals ``name`` for readable assertions."""
    return Photo(title=f"Title {name}", image_url=f"/img/{name}.png", photo_id=name)


def build_carousel(*names: str) -> PhotoCarousel:
    """Build a carousel by calling ``add_last`` for every name."""
    carousel = PhotoCarousel()
    for name in names:
        carousel.add_last(make_photo(name))
    return carousel


def forward_ids(carousel: PhotoCarousel) -> list:
    """Photo ids from head following ``next_slide`` (one lap)."""
    return [slide.photo.id for slide in carousel]


def assert_circular_integrity(carousel: PhotoCarousel) -> None:
    """Check every invariant of the doubly circular linked list."""
    if carousel.size == 0:
        assert carousel.head is None
        assert carousel.current is None
        assert carousel.is_empty()
        assert list(carousel) == []
        return

    head = carousel.head
    assert head is not None and carousel.current is not None
    assert not carousel.is_empty()

    # Walk forward exactly ``size`` steps: we must come back to the head.
    slide = head
    visited = []
    for _ in range(carousel.size):
        assert slide.next_slide is not None
        assert slide.next_slide.previous_slide is slide
        assert slide.previous_slide.next_slide is slide
        visited.append(slide)
        slide = slide.next_slide
    assert slide is head
    assert len({id(s) for s in visited}) == carousel.size

    # Circular closure at the boundaries.
    tail = visited[-1]
    assert tail.next_slide is head
    assert head.previous_slide is tail
    assert carousel.tail is tail

    # Backward walk mirrors the forward walk.
    backward = list(carousel.traverse_backward())
    assert backward == list(reversed(visited))

    assert len(carousel) == carousel.size
    assert any(s is carousel.current for s in visited)
    assert any(s is carousel.head for s in visited)


@pytest.fixture
def empty_carousel() -> PhotoCarousel:
    return PhotoCarousel()
