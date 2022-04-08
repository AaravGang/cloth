import pygame
from constants import *
from cloth import Cloth

pygame.init()

win = pygame.display.set_mode((WIDTH, HEIGHT))


def draw(cloth):
    win.fill((0, 0, 0))
    cloth.draw()
    pygame.display.update()


def main():
    sub_surface = win.subsurface((100, 100, SURF_WIDTH, SURF_HEIGHT))
    cloth = Cloth(
        sub_surface, image=pygame.image.load("texture.png").convert(), flag=False
    )

    clock = pygame.time.Clock()
    run = True

    while run:
        # clock.tick()
        # print(clock.get_fps())

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                run = False
                break

            cloth.check_event(e)

        cloth.update()
        draw(cloth)


if __name__ == "__main__":
    main()
