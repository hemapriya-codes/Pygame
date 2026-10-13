"""Tiny 2D vector class so the backend does not depend on Pygame."""
import math


class Vec2:
    __slots__ = ("x", "y")

    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)

    def __add__(self, o):
        return Vec2(self.x + o.x, self.y + o.y)

    def __sub__(self, o):
        return Vec2(self.x - o.x, self.y - o.y)

    def __mul__(self, k):
        return Vec2(self.x * k, self.y * k)

    __rmul__ = __mul__

    def __truediv__(self, k):
        return Vec2(self.x / k, self.y / k)

    def __neg__(self):
        return Vec2(-self.x, -self.y)

    def __iter__(self):
        yield self.x
        yield self.y

    def __repr__(self):
        return f"Vec2({self.x:.1f}, {self.y:.1f})"

    def length(self):
        return math.hypot(self.x, self.y)

    def length_squared(self):
        return self.x * self.x + self.y * self.y

    def distance_to(self, o):
        return math.hypot(self.x - o.x, self.y - o.y)

    def normalize(self):
        l = self.length()
        return Vec2(self.x / l, self.y / l) if l > 1e-9 else Vec2(0, 0)

    def dot(self, o):
        return self.x * o.x + self.y * o.y

    def rotate(self, rad):
        c, s = math.cos(rad), math.sin(rad)
        return Vec2(self.x * c - self.y * s, self.x * s + self.y * c)

    def lerp(self, o, t):
        return Vec2(self.x + (o.x - self.x) * t, self.y + (o.y - self.y) * t)

    def copy(self):
        return Vec2(self.x, self.y)

    def tuple(self):
        return (self.x, self.y)
