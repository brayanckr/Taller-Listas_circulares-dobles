"""Unit tests for PhotoCarousel (doubly circular linked list)."""

import random

from conftest import assert_circular_integrity, build_carousel, forward_ids, make_photo

from gallery import Photo, PhotoCarousel


# ---------------------------------------------------------------- empty list
class TestEmptyCarousel:
    def test_new_carousel_is_empty(self, empty_carousel):
        assert empty_carousel.is_empty()
        assert len(empty_carousel) == 0
        assert empty_carousel.size == 0
        assert empty_carousel.head is None
        assert empty_carousel.current is None
        assert empty_carousel.tail is None
        assert empty_carousel.current_position == 0
        assert_circular_integrity(empty_carousel)

    def test_operations_on_empty_do_not_fail(self, empty_carousel):
        assert empty_carousel.remove_current() is None
        assert empty_carousel.remove_by_id("x") is None
        assert empty_carousel.move_next() is None
        assert empty_carousel.move_previous() is None
        assert empty_carousel.go_to("x") is False
        assert empty_carousel.search_by_title("a") == []
        assert list(empty_carousel) == []
        assert list(empty_carousel.traverse_backward()) == []
        assert empty_carousel.to_list() == []
        empty_carousel.shuffle_order()
        assert_circular_integrity(empty_carousel)


# ------------------------------------------------------------------ insertion
class TestInsertion:
    def test_add_first_on_empty_creates_self_circle(self, empty_carousel):
        slide = empty_carousel.add_first(make_photo("a"))
        assert empty_carousel.head is slide
        assert empty_carousel.current is slide
        assert slide.next_slide is slide
        assert slide.previous_slide is slide
        assert len(empty_carousel) == 1
        assert_circular_integrity(empty_carousel)

    def test_add_last_on_empty_creates_self_circle(self, empty_carousel):
        slide = empty_carousel.add_last(make_photo("a"))
        assert empty_carousel.head is slide
        assert slide.next_slide is slide and slide.previous_slide is slide
        assert_circular_integrity(empty_carousel)

    def test_add_after_current_on_empty(self, empty_carousel):
        slide = empty_carousel.add_after_current(make_photo("a"))
        assert empty_carousel.head is slide
        assert empty_carousel.current is slide
        assert_circular_integrity(empty_carousel)

    def test_add_first_becomes_head_and_keeps_current(self):
        carousel = build_carousel("a", "b")
        new = carousel.add_first(make_photo("z"))
        assert carousel.head is new
        assert forward_ids(carousel) == ["z", "a", "b"]
        assert carousel.current.photo.id == "a"
        assert new.previous_slide.photo.id == "b"
        assert_circular_integrity(carousel)

    def test_add_last_becomes_tail_and_head_unchanged(self):
        carousel = build_carousel("a", "b")
        new = carousel.add_last(make_photo("z"))
        assert carousel.head.photo.id == "a"
        assert carousel.tail is new
        assert new.next_slide is carousel.head
        assert carousel.head.previous_slide is new
        assert forward_ids(carousel) == ["a", "b", "z"]
        assert_circular_integrity(carousel)

    def test_add_after_current_in_the_middle(self):
        carousel = build_carousel("a", "b", "c")
        carousel.go_to("b")
        new = carousel.add_after_current(make_photo("z"))
        assert forward_ids(carousel) == ["a", "b", "z", "c"]
        assert carousel.current.photo.id == "b"
        assert new.previous_slide.photo.id == "b"
        assert new.next_slide.photo.id == "c"
        assert_circular_integrity(carousel)

    def test_add_after_current_when_current_is_tail(self):
        carousel = build_carousel("a", "b", "c")
        carousel.go_to("c")
        new = carousel.add_after_current(make_photo("z"))
        assert carousel.tail is new
        assert new.next_slide is carousel.head
        assert forward_ids(carousel) == ["a", "b", "c", "z"]
        assert_circular_integrity(carousel)

    def test_add_after_current_with_single_slide(self):
        carousel = build_carousel("a")
        new = carousel.add_after_current(make_photo("z"))
        assert forward_ids(carousel) == ["a", "z"]
        assert new.next_slide is carousel.head
        assert_circular_integrity(carousel)

    def test_size_grows_with_each_insertion(self, empty_carousel):
        for index in range(5):
            empty_carousel.add_last(make_photo(str(index)))
            assert len(empty_carousel) == index + 1
            assert_circular_integrity(empty_carousel)


# -------------------------------------------------------------------- removal
class TestRemoval:
    def test_remove_current_single_slide(self):
        carousel = build_carousel("a")
        photo = carousel.remove_current()
        assert photo.id == "a"
        assert carousel.is_empty()
        assert_circular_integrity(carousel)

    def test_remove_by_id_single_slide(self):
        carousel = build_carousel("a")
        assert carousel.remove_by_id("a").id == "a"
        assert carousel.is_empty()
        assert_circular_integrity(carousel)

    def test_remove_current_when_it_is_head(self):
        carousel = build_carousel("a", "b", "c")
        assert carousel.current is carousel.head
        carousel.remove_current()
        assert forward_ids(carousel) == ["b", "c"]
        assert carousel.head.photo.id == "b"
        assert carousel.current.photo.id == "b"
        assert carousel.head.previous_slide.photo.id == "c"
        assert_circular_integrity(carousel)

    def test_remove_current_in_the_middle_moves_to_next(self):
        carousel = build_carousel("a", "b", "c")
        carousel.go_to("b")
        carousel.remove_current()
        assert forward_ids(carousel) == ["a", "c"]
        assert carousel.current.photo.id == "c"
        assert_circular_integrity(carousel)

    def test_remove_current_when_it_is_tail_wraps_to_head(self):
        carousel = build_carousel("a", "b", "c")
        carousel.go_to("c")
        carousel.remove_current()
        assert forward_ids(carousel) == ["a", "b"]
        assert carousel.current is carousel.head
        assert carousel.tail.photo.id == "b"
        assert carousel.tail.next_slide is carousel.head
        assert_circular_integrity(carousel)

    def test_remove_by_id_head_keeps_current(self):
        carousel = build_carousel("a", "b", "c")
        carousel.go_to("c")
        carousel.remove_by_id("a")
        assert carousel.head.photo.id == "b"
        assert carousel.current.photo.id == "c"
        assert carousel.head.previous_slide.photo.id == "c"
        assert_circular_integrity(carousel)

    def test_remove_by_id_tail(self):
        carousel = build_carousel("a", "b", "c")
        carousel.remove_by_id("c")
        assert forward_ids(carousel) == ["a", "b"]
        assert carousel.head.previous_slide.photo.id == "b"
        assert_circular_integrity(carousel)

    def test_remove_by_id_that_is_current(self):
        carousel = build_carousel("a", "b", "c")
        carousel.go_to("b")
        carousel.remove_by_id("b")
        assert carousel.current.photo.id == "c"
        assert_circular_integrity(carousel)

    def test_remove_by_id_unknown_returns_none(self):
        carousel = build_carousel("a", "b")
        assert carousel.remove_by_id("nope") is None
        assert len(carousel) == 2
        assert_circular_integrity(carousel)

    def test_remove_two_slides_down_to_one(self):
        carousel = build_carousel("a", "b")
        carousel.remove_by_id("a")
        only = carousel.head
        assert only.photo.id == "b"
        assert only.next_slide is only and only.previous_slide is only
        assert_circular_integrity(carousel)

    def test_remove_everything_one_by_one(self):
        carousel = build_carousel("a", "b", "c", "d")
        while not carousel.is_empty():
            carousel.remove_current()
            assert_circular_integrity(carousel)
        assert len(carousel) == 0

    def test_removed_slide_is_detached(self):
        carousel = build_carousel("a", "b", "c")
        slide = carousel.find_slide("b")
        carousel.remove_by_id("b")
        assert slide.next_slide is None and slide.previous_slide is None

    def test_can_add_again_after_emptying(self):
        carousel = build_carousel("a")
        carousel.remove_current()
        carousel.add_last(make_photo("b"))
        assert forward_ids(carousel) == ["b"]
        assert_circular_integrity(carousel)


# ----------------------------------------------------------------- navigation
class TestNavigation:
    def test_move_next_wraps_from_tail_to_head(self):
        carousel = build_carousel("a", "b", "c")
        ids = [carousel.move_next().photo.id for _ in range(4)]
        assert ids == ["b", "c", "a", "b"]
        assert_circular_integrity(carousel)

    def test_move_previous_wraps_from_head_to_tail(self):
        carousel = build_carousel("a", "b", "c")
        ids = [carousel.move_previous().photo.id for _ in range(4)]
        assert ids == ["c", "b", "a", "c"]
        assert_circular_integrity(carousel)

    def test_full_lap_returns_to_start_both_ways(self):
        carousel = build_carousel("a", "b", "c", "d", "e")
        start = carousel.current
        for _ in range(5):
            carousel.move_next()
        assert carousel.current is start
        for _ in range(5):
            carousel.move_previous()
        assert carousel.current is start

    def test_single_slide_navigation_stays_put(self):
        carousel = build_carousel("a")
        assert carousel.move_next() is carousel.head
        assert carousel.move_previous() is carousel.head

    def test_next_then_previous_is_identity(self):
        carousel = build_carousel("a", "b", "c")
        carousel.move_next()
        carousel.move_previous()
        assert carousel.current is carousel.head

    def test_head_previous_is_tail(self):
        carousel = build_carousel("a", "b", "c")
        assert carousel.head.previous_slide.photo.id == "c"
        assert carousel.head.previous_slide is carousel.tail
        assert carousel.tail.next_slide is carousel.head

    def test_go_to_existing(self):
        carousel = build_carousel("a", "b", "c")
        assert carousel.go_to("c") is True
        assert carousel.current.photo.id == "c"
        assert carousel.current_position == 3

    def test_go_to_missing_keeps_current(self):
        carousel = build_carousel("a", "b")
        carousel.go_to("b")
        assert carousel.go_to("nope") is False
        assert carousel.current.photo.id == "b"


# ----------------------------------------------------------------- traversals
class TestTraversal:
    def test_iter_is_one_full_lap(self):
        carousel = build_carousel("a", "b", "c")
        assert forward_ids(carousel) == ["a", "b", "c"]
        assert len(list(carousel)) == 3

    def test_iter_is_independent_of_current(self):
        carousel = build_carousel("a", "b", "c")
        carousel.go_to("c")
        assert forward_ids(carousel) == ["a", "b", "c"]

    def test_iter_single_slide(self):
        assert forward_ids(build_carousel("a")) == ["a"]

    def test_traverse_backward_goes_from_tail_to_head(self):
        carousel = build_carousel("a", "b", "c")
        assert [s.photo.id for s in carousel.traverse_backward()] == ["c", "b", "a"]

    def test_traverse_backward_single_slide(self):
        carousel = build_carousel("a")
        assert [s.photo.id for s in carousel.traverse_backward()] == ["a"]

    def test_iteration_can_be_repeated(self):
        carousel = build_carousel("a", "b")
        assert forward_ids(carousel) == forward_ids(carousel)

    def test_current_position(self):
        carousel = build_carousel("a", "b", "c")
        assert carousel.current_position == 1
        carousel.move_next()
        assert carousel.current_position == 2


# --------------------------------------------------------------------- search
class TestSearch:
    def test_search_is_case_insensitive_and_partial(self):
        carousel = PhotoCarousel()
        for index, title in enumerate(["Beach Sunset", "Mountain", "sunrise", "Forest"]):
            carousel.add_last(Photo(title, f"/{index}.png", photo_id=str(index)))
        assert [p.title for p in carousel.search_by_title("SUN")] == ["Beach Sunset", "sunrise"]
        assert [p.title for p in carousel.search_by_title("forest")] == ["Forest"]

    def test_search_without_match(self):
        assert build_carousel("a", "b").search_by_title("zzz") == []

    def test_search_blank_text_returns_nothing(self):
        assert build_carousel("a").search_by_title("   ") == []

    def test_search_terminates_on_single_slide(self):
        carousel = build_carousel("a")
        assert len(carousel.search_by_title("title")) == 1

    def test_search_does_not_change_current(self):
        carousel = build_carousel("a", "b", "c")
        carousel.go_to("b")
        carousel.search_by_title("title")
        assert carousel.current.photo.id == "b"


# -------------------------------------------------------------------- shuffle
class TestShuffle:
    def test_shuffle_empty_and_single_are_noops(self, empty_carousel):
        empty_carousel.shuffle_order()
        assert empty_carousel.is_empty()
        single = build_carousel("a")
        single.shuffle_order()
        assert forward_ids(single) == ["a"]
        assert_circular_integrity(single)

    def test_shuffle_keeps_same_slide_objects(self):
        carousel = build_carousel("a", "b", "c", "d", "e", "f")
        before = {id(slide): slide.photo.id for slide in carousel}
        carousel.shuffle_order(random.Random(7))
        after = {id(slide): slide.photo.id for slide in carousel}
        assert before == after  # same slide objects, only links changed
        assert_circular_integrity(carousel)

    def test_shuffle_keeps_size_and_elements(self):
        carousel = build_carousel(*"abcdefgh")
        carousel.shuffle_order(random.Random(1))
        assert len(carousel) == 8
        assert sorted(forward_ids(carousel)) == sorted("abcdefgh")
        assert_circular_integrity(carousel)

    def test_shuffle_keeps_current_slide(self):
        carousel = build_carousel(*"abcdef")
        carousel.go_to("d")
        current = carousel.current
        carousel.shuffle_order(random.Random(3))
        assert carousel.current is current
        assert_circular_integrity(carousel)

    def test_shuffle_can_change_order(self):
        original = list("abcdefgh")
        changed = False
        for seed in range(10):
            carousel = build_carousel(*original)
            carousel.shuffle_order(random.Random(seed))
            changed = changed or forward_ids(carousel) != original
        assert changed

    def test_shuffle_many_times_stays_consistent(self):
        carousel = build_carousel(*"abcdefg")
        rng = random.Random(42)
        for _ in range(100):
            carousel.shuffle_order(rng)
            assert_circular_integrity(carousel)
            assert len(carousel) == 7

    def test_shuffle_two_slides(self):
        carousel = build_carousel("a", "b")
        carousel.shuffle_order(random.Random(0))
        assert sorted(forward_ids(carousel)) == ["a", "b"]
        assert_circular_integrity(carousel)


# --------------------------------------------------------------------- export
class TestToList:
    def test_to_list_contains_neighbour_ids(self):
        carousel = build_carousel("a", "b", "c")
        data = carousel.to_list()
        assert [d["id"] for d in data] == ["a", "b", "c"]
        assert [d["next_id"] for d in data] == ["b", "c", "a"]
        assert [d["previous_id"] for d in data] == ["c", "a", "b"]

    def test_to_list_flags_head_and_current(self):
        carousel = build_carousel("a", "b", "c")
        carousel.go_to("b")
        data = carousel.to_list()
        assert [d["is_head"] for d in data] == [True, False, False]
        assert [d["is_current"] for d in data] == [False, True, False]

    def test_to_list_single_slide_points_to_itself(self):
        data = build_carousel("a").to_list()
        assert data[0]["next_id"] == "a" and data[0]["previous_id"] == "a"

    def test_to_list_includes_photo_fields(self):
        data = build_carousel("a").to_list()[0]
        for key in ("id", "title", "description", "image_url", "upload_date"):
            assert key in data


# ------------------------------------------------------------ mixed scenarios
def test_random_operations_keep_structure_consistent():
    """Fuzz test: apply many random operations and verify the invariants."""
    rng = random.Random(2024)
    carousel = PhotoCarousel()
    counter = 0
    for _ in range(500):
        action = rng.choice(["first", "last", "after", "rm_cur", "rm_id", "next", "prev", "goto", "shuffle"])
        ids = forward_ids(carousel)
        if action in ("first", "last", "after"):
            counter += 1
            photo = make_photo(f"p{counter}")
            {"first": carousel.add_first, "last": carousel.add_last, "after": carousel.add_after_current}[action](photo)
        elif action == "rm_cur":
            carousel.remove_current()
        elif action == "rm_id" and ids:
            carousel.remove_by_id(rng.choice(ids))
        elif action == "next":
            carousel.move_next()
        elif action == "prev":
            carousel.move_previous()
        elif action == "goto" and ids:
            carousel.go_to(rng.choice(ids))
        elif action == "shuffle":
            carousel.shuffle_order(rng)
        assert_circular_integrity(carousel)
