import pygame
from constants import *
from cloth import Cloth

pygame.init()

win = pygame.display.set_mode((WIDTH, HEIGHT))


def draw(cloth):
    win.fill((0, 0, 0))
    cloth.draw(win)
    pygame.display.update()


def main():
    cloth = Cloth(
        SURF_WIDTH,
        SURF_HEIGHT,
        100,
        100,
        image=pygame.image.load("image.jpg").convert(),
    )

    clock = pygame.time.Clock()

    pygame.time.set_timer(pygame.USEREVENT + 1, 1000)

    run = True

    while run:
        clock.tick()
        # print(clock.get_fps())

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                run = False
                break

            if e.type == pygame.USEREVENT + 1:
                cloth.update_wind()
            cloth.check_event(e)

        cloth.update()
        draw(cloth)


if __name__ == "__main__":
    main()
