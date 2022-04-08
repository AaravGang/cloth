import pygame

# link b/w 2 points
class Link:
    def __init__(self, p1, p2, resting_distance, stiffness, tear_sensitivity):
        self.p1, self.p2 = p1, p2
        self.pos1: pygame.Vector2 = self.p1.pos
        self.pos2: pygame.Vector2 = self.p2.pos

        self.resting_distance, self.stiffness, self.tear_sensitivity = (
            resting_distance,
            stiffness,
            tear_sensitivity,
        )

    def solve(self):
        diff = self.pos1 - self.pos2

        # calculate the distance  between the 2 points
        d = self.pos1.distance_to(self.pos2)

        if d < 0.0000001:  # if d is too small, 0 division error may be raised
            return

        # if the distance is too great, break the link
        if d > self.tear_sensitivity:
            self.p1.remove_link(self)

        # ratio of how far along the resting distance they are
        difference = (self.resting_distance - d) / d
        # divide the stiffness equally b/w the 2 point masses
        # if one was heavier than other, then some mapping would be required
        scalar = self.stiffness / 2

        self.pos1 += diff * scalar * difference
        self.pos2 -= diff * scalar * difference

    def draw(self, surf):
        pygame.draw.line(surf, (255, 255, 0), self.pos1, self.pos2, 1)

