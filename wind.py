import pygame, imageio
import numpy as np


class Wind(pygame.sprite.Sprite):
    def __init__(self, y, parent_width, size=(300, 100)):
        super(Wind, self).__init__()

        self.surf = pygame.Surface(size)
        self.surf.set_alpha(255)
        self.surf.set_colorkey((0, 0, 0))
        self.parent_width = parent_width

        self.rect = self.surf.get_rect(centery=y)

        self.images = [
            pygame.transform.smoothscale(
                pygame.surfarray.make_surface(
                    np.delete(frame, 3, 2).transpose(1, 0, 2)
                ),
                self.surf.get_size(),
            )
            for frame in imageio.get_reader("wind.gif")
        ]
        for image in self.images:
            pygame.transform.threshold(
                image,
                image,
                (137, 130, 130),
                (10, 10, 10),
                (141, 130, 130),
                inverse_set=True,
            )
            image.set_colorkey((141, 130, 130))

        self.n_frames = len(self.images)
        self.index = 0

        self.fixed_vel_x = 50

        self.play = False

    def set_vel(self, velx):
        if velx >= 0:
            self.rect.x = 0
            self.rotation = 0
            self.fixed_vel_x = abs(self.fixed_vel_x)
        else:
            self.rotation = 180
            self.rect.x = self.parent_width
            self.fixed_vel_x = -1 * abs(self.fixed_vel_x)

        self.index = 0
        self.play = True

    def update(self):
        self.surf.fill((0, 0, 0))

        if not self.play:
            return

        self.surf.blit(
            pygame.transform.rotate(self.images[self.index], self.rotation), (0, 0),
        )

        self.index += 1
        self.index %= self.n_frames

        self.rect.x += self.fixed_vel_x

        if self.index == 0:
            self.play = False

    def draw(self, surf):
        surf.blit(self.surf, self.rect)

