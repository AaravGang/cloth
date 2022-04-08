import pygame
from constants import *
from link import Link


def point_to_segment_dist_squared(
    end_point1: pygame.Vector2, end_point2: pygame.Vector2, point: pygame.Vector2
):
    v = end_point1 - point
    u = end_point2 - end_point1

    hyp_sq = u.x ** 2 + u.y ** 2  # end_point2.distance_squared_to(end_point1)

    det = (-v.x * u.x) + (-v.y * u.y)
    if (det < 0) or (det > hyp_sq):
        u = end_point2 - point
        return min(
            v.x ** 2 + v.y ** 2, u.x ** 2 + u.y ** 2
        )  # min(v.length_squared(), u.length_squared())

    det = u.x * v.y - u.y * v.x
    return (det * det) / hyp_sq


class PointMass:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.prev_pos = pygame.Vector2(x, y)

        self.acc = pygame.Vector2()

        # if pinned to a point, it will be a pygame vector2
        self.pinned = False

        self.links = []

    # update the position using verlet integration
    def update(self, time_step, wind):
        self.acc += (wind, GRAVITY)

        vel = self.pos - self.prev_pos
        vel *= 0.99  # dampen velocity

        next = self.pos + vel + 0.5 * self.acc * time_step ** 2

        self.prev_pos.update(self.pos)
        self.pos.update(next)
        self.acc.update(0, 0)

    # user interaction
    def check_event(self, button_type, pmouse, mouse, mouse_influence_scalar):
        distance_squared = point_to_segment_dist_squared(pmouse, mouse, self.pos)

        if button_type == 1 and distance_squared < mouse_influence_size_sq:
            self.prev_pos = self.pos - (mouse - pmouse) * mouse_influence_scalar

        if button_type == 3 and distance_squared < mouse_tear_size_sq:
            self.links.clear()  # tear if right clicking

    # solve the physics
    def solve(self, surf):
        # solve constrains for all the links
        for link in reversed(self.links):
            link.solve()

        # keep the point masses within the boundary
        if self.pos.x < 0:
            self.pos.x = 0
        if self.pos.x > surf.get_width():
            self.pos.x = surf.get_width()
        if self.pos.y < 0:
            self.pos.y = 0
        if self.pos.y > surf.get_height():
            self.pos.y = surf.get_height()

        # if this pointmass is pinned then move it back to the pinned position
        if self.pinned:
            self.pos.update(self.pinned)

    def draw(self, surf, draw_links=True):
        if draw_links:
            for link in self.links:
                link.draw(surf)

        if len(self.links) == 0 or self.pinned:
            pygame.draw.circle(surf, (0, 0, 0), self.pos, 2)

    # create a link with another pointmass
    def make_link(self, p, resting_distance, stiffness, tear_sensitivity):
        l = Link(self, p, resting_distance, stiffness, tear_sensitivity)
        self.links.append(l)

    # remove a link
    def remove_link(self, l):
        self.links.remove(l)

    # pin to a point
    def pin(self, point):
        self.pinned = pygame.Vector2(point)

