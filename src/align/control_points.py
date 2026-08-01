from dataclasses import dataclass


@dataclass
class ControlPoint:
    """
    하나의 Control Point Pair
    """

    name: str

    t1: tuple | None = None
    t2: tuple | None = None

    @property
    def complete(self):

        return self.t1 is not None and self.t2 is not None


class ControlPointManager:
    """
    Wizard 방식의 Point 관리 클래스

    상태

    T1 클릭 대기
        ↓
    T2 클릭 대기
        ↓
    Point 완료
        ↓
    다음 Point 생성
    """

    def __init__(self):

        self.points = []

        self.current_point = None

        self.current_index = 1

        self.state = "T1"

        self.create_next_point()

    # -------------------------

    def create_next_point(self):

        name = f"P{self.current_index}"

        self.current_point = ControlPoint(name)

        self.points.append(self.current_point)

    # -------------------------

    def set_t1(self, x, y):

        if self.state != "T1":
            return

        self.current_point.t1 = (x, y)

        self.state = "T2"

    # -------------------------

    def set_t2(self, x, y):

        if self.state != "T2":
            return

        self.current_point.t2 = (x, y)

        self.current_index += 1

        self.state = "T1"

        self.create_next_point()

    # -------------------------

    def add_click(self, image_name, x, y):
        """
        image_name

        T1
        T2
        """

        if image_name == "T1":

            self.set_t1(x, y)

        elif image_name == "T2":

            self.set_t2(x, y)

    # -------------------------

    def delete_point(self, point_name):

        target = None

        for p in self.points:

            if p.name == point_name:

                target = p

                break

        if target is None:
            return

        is_current = (target == self.current_point)
        self.points.remove(target)

        if is_current:
            # If we deleted the current (active / being input) point, we might need to reset state or handle it.
            # But normally we delete completed points. Let's make sure self.current_point is always valid.
            if not self.points:
                self.current_index = 1
                self.state = "T1"
                self.create_next_point()
            else:
                self.current_point = self.points[-1]
                if self.current_point.complete:
                    self.current_index = int(self.current_point.name[1:]) + 1
                    self.state = "T1"
                    self.create_next_point()
                else:
                    self.current_index = int(self.current_point.name[1:])
                    self.state = "T2" if self.current_point.t1 else "T1"
        else:
            # We deleted some other point. Let's ensure self.current_point is still consistent or we recreate if needed.
            # Usually we don't need to change self.current_point unless it is affected, but we should make sure the next point indices remain logical if needed.
            # The simplest way to keep things robust is to check if current_point is still in self.points.
            if self.current_point not in self.points:
                if not self.points:
                    self.current_index = 1
                    self.state = "T1"
                    self.create_next_point()
                else:
                    self.current_point = self.points[-1]
                    if self.current_point.complete:
                        self.current_index = int(self.current_point.name[1:]) + 1
                        self.state = "T1"
                        self.create_next_point()
                    else:
                        self.current_index = int(self.current_point.name[1:])
                        self.state = "T2" if self.current_point.t1 else "T1"

    # -------------------------

    def clear(self):

        self.points.clear()

        self.current_index = 1

        self.state = "T1"

        self.create_next_point()

    # -------------------------

    def completed_points(self):

        return [p for p in self.points if p.complete]

    # -------------------------

    def completed_count(self):

        return len(self.completed_points())

    # -------------------------

    def current_name(self):

        return self.current_point.name

    # -------------------------

    def current_step(self):

        if self.state == "T1":

            return "Click T1"

        return "Click T2"

    # -------------------------

    def ready_for_alignment(self):

        return self.completed_count() >= 3

    # -------------------------

    def get_points(self):

        return self.points

    def current_step(self):
        return self.state

    def current_name(self):
        return self.current_point.name

    def get_points(self):
        return self.points
    
    def update_point(self, point_name, image_name, x, y):
        for p in self.points:
            if p.name == point_name:
                if image_name == "T1":
                    p.t1 = (x, y)
                elif image_name == "T2":
                    p.t2 = (x, y)
                break

    def status_text(self):

        if self.state == "T1":
            return "Click T1"

        return "Click T2"
