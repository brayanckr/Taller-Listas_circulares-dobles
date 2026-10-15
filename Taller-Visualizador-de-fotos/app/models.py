"""Doubly circular linked list of 360° product angle frames.

The circularity is handled purely with `next_frame` / `prev_frame` pointers;
no native Python collection is used to store the frames.
"""


def angle_label(angle_degree):
    """Human-readable name for an angle."""
    labels = {
        0: "Front View",
        90: "Right Side View",
        180: "Rear View",
        270: "Left Side View",
    }
    if angle_degree in labels:
        return labels[angle_degree]
    names = ("Front", "Right Side", "Rear", "Left Side")
    quadrant = (angle_degree + 45) // 90 % 4
    offset = angle_degree - quadrant * 90 if angle_degree < 315 else angle_degree - 360
    if abs(offset) <= 10:
        return f"{names[quadrant]} View"
    return "Three-Quarter View" if abs(offset) >= 25 else "Angled View"


class AngleFrame:
    """A single frame (one camera angle) of the 360° product view."""

    def __init__(self, frame_id, angle_degree, image_url, description):
        self.frame_id = frame_id
        self.angle_degree = angle_degree
        self.image_url = image_url
        self.description = description
        self.next_frame = self
        self.prev_frame = self

    def title(self):
        return f"Angle {self.angle_degree}° - {angle_label(self.angle_degree)}"

    def to_dict(self):
        return {
            "frame_id": self.frame_id,
            "angle_degree": self.angle_degree,
            "image_url": self.image_url,
            "description": self.description,
            "title": self.title(),
        }

    def to_summary(self):
        return {
            "frame_id": self.frame_id,
            "angle_degree": self.angle_degree,
            "title": self.title(),
        }


class AngleFrameList:
    """Doubly circular linked list ordered by ascending angle."""

    def __init__(self):
        self.current_frame = None
        self.head_frame = None  # frame with the smallest angle
        self.size = 0
        self._next_id = 1

    def is_empty(self):
        return self.size == 0

    def insert_frame(self, angle_degree, image_url, description):
        """Insert a frame keeping the list sorted by angle and circular."""
        if not isinstance(angle_degree, int) or isinstance(angle_degree, bool):
            raise ValueError("angle_degree must be an integer")
        if not 0 <= angle_degree < 360:
            raise ValueError("angle_degree must be between 0 and 359")
        if not image_url or not description:
            raise ValueError("image_url and description are required")

        new_frame = AngleFrame(self._next_id, angle_degree, image_url, description)

        if self.head_frame is None:
            self.head_frame = self.current_frame = new_frame
        else:
            # Find the first frame with a larger angle and insert before it;
            # if none exists the new frame goes at the end (just before head).
            probe = self.head_frame
            for _ in range(self.size):
                if probe.angle_degree == angle_degree:
                    raise ValueError(f"A frame at {angle_degree}° already exists")
                if probe.angle_degree > angle_degree:
                    break
                probe = probe.next_frame
            before = probe.prev_frame
            before.next_frame = new_frame
            new_frame.prev_frame = before
            new_frame.next_frame = probe
            probe.prev_frame = new_frame
            if probe is self.head_frame and probe.angle_degree > angle_degree:
                self.head_frame = new_frame

        self._next_id += 1
        self.size += 1
        return new_frame

    def delete_frame(self, frame_id):
        """Delete a frame by id and reconnect its neighbours. Returns it, or None."""
        target = self._find(frame_id)
        if target is None:
            return None

        if self.size == 1:
            self.head_frame = self.current_frame = None
        else:
            target.prev_frame.next_frame = target.next_frame
            target.next_frame.prev_frame = target.prev_frame
            if self.current_frame is target:
                self.current_frame = target.next_frame
            if self.head_frame is target:
                self.head_frame = target.next_frame
        target.next_frame = target.prev_frame = target
        self.size -= 1
        return target

    def step_next(self):
        if self.current_frame is None:
            return None
        self.current_frame = self.current_frame.next_frame
        return self.current_frame

    def step_prev(self):
        if self.current_frame is None:
            return None
        self.current_frame = self.current_frame.prev_frame
        return self.current_frame

    def get_current_frame_info(self):
        if self.current_frame is None:
            return {"current": None, "next": None, "prev": None, "size": 0}
        cur = self.current_frame
        return {
            "current": cur.to_dict(),
            "next": cur.next_frame.to_summary(),
            "prev": cur.prev_frame.to_summary(),
            "size": self.size,
        }

    def get_all_frames(self):
        """Frames in list order starting at the head, flagged by role."""
        result = []
        probe = self.head_frame
        for _ in range(self.size):
            data = probe.to_dict()
            data["next_id"] = probe.next_frame.frame_id
            data["prev_id"] = probe.prev_frame.frame_id
            data["is_current"] = probe is self.current_frame
            data["is_next"] = probe is self.current_frame.next_frame
            data["is_prev"] = probe is self.current_frame.prev_frame
            result.append(data)
            probe = probe.next_frame
        return result

    def _find(self, frame_id):
        probe = self.head_frame
        for _ in range(self.size):
            if probe.frame_id == frame_id:
                return probe
            probe = probe.next_frame
        return None
