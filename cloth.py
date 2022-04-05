import pygame, time, math, random
import pygame.gfxdraw
from point_mass import PointMass


class Cloth:
    def __init__(self, width, height, x, y, image=None):
        # cloth constants
        self.width, self.height = width, height
        self.x, self.y, self.offset = x, y, pygame.Vector2(-x, -y)

        # create surface
        self.surf = pygame.Surface((width, height))
        self.rect = self.surf.get_rect(topleft=(self.x, self.y))
        self.surf.set_colorkey((0, 0, 0))  # set colorkey cuz gfxdraw wants it...

        # no. of rows and cols, cols is really just cols+1 for a quick fix for rendering
        self.rows, self.cols = 40, 41

        # how far away are the points while at rest?
        self.resting_distance = min(
            self.width // (self.cols), self.height // self.rows
        )  # dynamically calculate resting distance based on nrows and ncols
        self.diagonal_resting_distance = math.sqrt(2) * self.resting_distance

        self.tear_sensitivity = (
            self.resting_distance * 8
        )  # the links b/w 2 point masses will tear when they go this far apart

        self.stiffness = 1  # stiffer it is, harder it will be to influence

        # all the pointmasses in the cloth in a 2d grid
        self.cloth = self.create_cloth()

        self.image = None
        if image:
            self.set_image(image)

        self.constraint_accuracy = (
            3  # solve constraints these many times to increase accuracy
        )

        # variable for dynamically calculating number of iterations
        self.prev_time = time.time()
        self.remainder_time = 0
        self.fixed_delta_time = 16 / 1000  # 16 ms -> approx 60 fps

        # variables for mouse interaction
        self.mouse_dragging = False
        self.pmouse = pygame.Vector2(-1, -1) + self.offset
        self.mouse = pygame.Vector2(pygame.mouse.get_pos()) + self.offset

        # mouse influence constants
        self.mouse_influence_scalar = 1

        # wind
        self.wind = 0  # wind will be horizontal left or right

    # create 2d grid of pointmasses
    def create_cloth(self):

        xoff = (
            self.width / 2 - (self.cols - 1) * self.resting_distance / 2
        )  # offset to center the cloth in the surface
        yoff = 0

        self.xoff, self.yoff = xoff, yoff

        cloth = []  # will be a 2d list of pointmasses

        # row corresponds to y coord
        for row in range(self.rows):
            cloth.append([])
            # col corresponds to x coord
            for col in range(self.cols):
                p = PointMass(
                    xoff + col * self.resting_distance,
                    yoff + row * self.resting_distance,
                )

                # if col == 0 and row % (self.rows - 1) == 0:
                #     p.pin(p.pos)
                # if row % (self.rows - 1) == 0 and col == self.cols - 1:
                #     p.pin(p.pos)
                if row == 0 and col % 5 == 0:
                    p.pin(p.pos)

                cloth[row].append(p)

        # form the links b/w the point masses
        for row in range(self.rows):
            for col in range(self.cols):
                p = cloth[row][col]

                if row > 0:
                    # make a link with the point mass above it
                    p.make_link(
                        cloth[row - 1][col],
                        self.resting_distance,
                        self.stiffness,
                        self.tear_sensitivity,
                    )

                    # diagonal top left
                    # if col > 0:
                    #     p.make_link(
                    #         cloth[row - 1][col - 1],
                    #         self.diagonal_resting_distance,
                    #         self.stiffness,
                    #         self.tear_sensitivity,
                    #     )

                # make a link with the point mass left of it
                if col > 0:
                    p.make_link(
                        cloth[row][col - 1],
                        self.resting_distance,
                        self.stiffness,
                        self.tear_sensitivity,
                    )

                # make a link with the point mass right of it
                # if col < self.cols - 1:
                #     p.make_link(
                #         cloth[row][col + 1],
                #         self.resting_distance,
                #         self.stiffness,
                #         self.tear_sensitivity,
                #     )

        return cloth

    # randomy add some wind
    def update_wind(self):
        self.wind = random.randint(-1000, 1000)

    # update the physics
    def update(self):
        # calculate the number of iterations to make it feel like 60fps
        t = time.time()
        elapsed_time = t - self.prev_time
        self.prev_time = t

        n_iterations, self.remainder_time = (
            int((elapsed_time + self.remainder_time) // self.fixed_delta_time),
            elapsed_time % self.fixed_delta_time,
        )

        if n_iterations == 0:
            return

        # limit the number of iterations to 5 to avoid potential freezing
        n_iterations = min(n_iterations, 5)

        # update the mouse influence mulitplier
        self.mouse_influence_scalar = 1 / n_iterations

        # multiple iterations to maintain a near 60 fps feel
        for i in range(n_iterations):
            # solve the constraints of the physics multiple times for higher accuracy
            for _ in range(self.constraint_accuracy):
                for row in self.cloth:
                    for p in row:
                        p.solve(self.surf)

            # update the physics of each pointmass
            for row in self.cloth:
                for p in row:
                    p.update(1 / 125, self.wind)

    # set the image for the cloth
    def set_image(self, image):
        self.image = pygame.transform.scale(
            image,
            (
                (self.cols - 1) * self.resting_distance,
                (self.rows - 1) * self.resting_distance,
            ),
        )

    # all drawing
    def draw(self, win):
        self.surf.fill((255, 0, 255))

        for r, row in enumerate(self.cloth):
            for c, p in enumerate(row):

                # draw a textured polygon with the points before it
                if self.image is not None and r > 0 and c > 0:
                    topleft = self.cloth[r - 1][c - 1]  # diagonal left of p
                    topright = self.cloth[r - 1][c]  # above p
                    bottomright = p
                    bottomleft = self.cloth[r][c - 1]  # left of p

                    # if these 4 pointmasses are not connected by links, there is no need to draw a texture
                    # simply show the links
                    if not (
                        topright in [link.p2 for link in bottomright.links]
                        and bottomleft in [link.p2 for link in bottomright.links]
                        and topleft in [link.p2 for link in topright.links]
                    ):
                        p.draw(self.surf)
                        continue

                    # might throw a few random errors
                    try:
                        pygame.gfxdraw.textured_polygon(
                            self.surf,
                            [
                                topleft.pos,
                                topright.pos,
                                bottomright.pos,
                                bottomleft.pos,
                            ],
                            self.image,
                            0,
                            0,
                        )
                    except:
                        pass

                elif self.image is None:
                    p.draw(self.surf)

        win.blit(self.surf, self.rect)

    # update the mouse position based on how much it has moved ( rel )
    # also add offset, to offset the mouse position for the surface
    def update_mouse(self, rel):
        self.mouse.update(pygame.mouse.get_pos() + self.offset)
        self.pmouse.update(self.mouse - rel)

    # check for user interaction
    def check_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and (e.button == 1 or e.button == 3):
            self.mouse_dragging = e.button
        elif e.type == pygame.MOUSEBUTTONUP and (e.button == 1 or e.button == 3):
            self.mouse_dragging = False
        elif e.type == pygame.MOUSEMOTION and self.mouse_dragging:
            if (
                pygame.Vector2(e.rel).length_squared() < 0.0001
            ):  # if length is near 0, it will throw a zero division error
                return

            self.update_mouse(e.rel)

            for row in self.cloth:
                for p in row:
                    p.check_event(
                        self.mouse_dragging,  # left or right button
                        self.pmouse,  # previous mouse pos
                        self.mouse,  # current mouse pos
                        self.mouse_influence_scalar,  # how strong the mouse force is
                    )

