import pygame, time, math, random
import pygame.gfxdraw
from point_mass import PointMass
from wind import Wind

class Cloth:
    def __init__(self, surface: pygame.surface, image=None, wind=True):
        # create surface
        self.surf = surface
        self.surf.set_colorkey((0, 0, 0))  # set colorkey cuz gfxdraw wants it...

        self.width, self.height = self.surf.get_size()
        self.offset = -pygame.Vector2(self.surf.get_abs_offset())

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
        self.wind = [
            wind,
            random.choice((-1, 1)) * random.randint(500, 1000),
            Wind(self.height / 2, self.width),
        ]  # (have wind? , wind speed: left or right)
        self.add_wind()

    # create 2d grid of pointmasses
    def create_cloth(self):
        # TODO: these offsets mess up the rendering, figure out what's wrong and fix it
        xoff = (
            self.width / 2 - (self.cols - 1) * self.resting_distance / 2
        )  # offset to center the cloth in the surface
        yoff = 20

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

                # up
                if row > 0:
                    p.make_link(
                        cloth[row - 1][col],
                        self.resting_distance,
                        self.stiffness,
                        self.tear_sensitivity,
                    )

                # left
                if col > 0:
                    p.make_link(
                        cloth[row][col - 1],
                        self.resting_distance,
                        self.stiffness,
                        self.tear_sensitivity,
                    )

                # right
                # if col < self.cols - 1:
                #     p.make_link(
                #         cloth[row][col + 1],
                #         self.resting_distance,
                #         self.stiffness,
                #         self.tear_sensitivity,
                #     )

                # diagonal se -> nw
                # if row > 0 and col > 0:
                #     p.make_link(
                #         cloth[row - 1][col - 1],
                #         self.diagonal_resting_distance,
                #         self.stiffness,
                #         self.tear_sensitivity,
                #     )

        return cloth

    def add_wind(self):
        self.wind[0] = True
        # set time for wind
        pygame.time.set_timer(pygame.USEREVENT + 1, 5000)

    # randomy add some wind
    def update_wind(self, e):
        if self.wind[0]:

            if e.type == pygame.USEREVENT + 1:
                self.wind[1] = random.choice([-1, 1]) * random.randint(500, 1000)
                self.wind[2].set_vel(self.wind[1])

            else:
                self.wind[1] *= 0.75  # dampen

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
                    p.update(1 / 125, self.wind[1])

        self.wind[2].update()

    # set the image for the cloth
    def set_image(self, image):
        # resize the image to match the cloth size
        self.image = pygame.transform.scale(
            image,
            (
                (self.cols - 1) * self.resting_distance,
                (self.rows - 1) * self.resting_distance,
            ),
        )

        # convert image to numpy array, so that chunks can be taken out of it
        image_arr = pygame.surfarray.array3d(self.image)

        # divide the image into chunks that can be stretched to fit the points
        self.mosaic = []
        for row in range(1, self.rows):
            self.mosaic.append([])
            for col in range(1, self.cols):
                # make a surface from a chunk out of the original image
                surf = pygame.surfarray.make_surface(
                    image_arr[
                        (col - 1)
                        * self.resting_distance : (col)
                        * self.resting_distance,
                        (row - 1)
                        * self.resting_distance : (row)
                        * self.resting_distance,
                    ]
                )
                # need to set a colorkey for gfxdraw to be happy :D
                surf.set_colorkey((255, 0, 255))

                self.mosaic[-1].append(surf)

        """ TODO : add the points that will draw the polygon also to the mosaic,
            so that they don't need to be calculated every single time in draw
        """

    # all drawing
    def draw(self, win):
        self.surf.fill((255, 0, 255))

        for r, row in enumerate(self.cloth):
            for c, p in enumerate(row):

                # draw a textured polygon with the points before it
                if r > 0 and c > 0:
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

                    if self.image is not None:
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
                                self.mosaic[r - 1][c - 1],
                                0,
                                0,
                            )

                            p.draw(self.surf, draw_links=False)

                        except pygame.error:
                            pass

                    else:
                        pygame.gfxdraw.polygon(
                            self.surf,
                            [
                                topleft.pos,
                                topright.pos,
                                bottomright.pos,
                                bottomleft.pos,
                            ],
                            (0, 255, 255),
                        )
        self.wind[2].draw(self.surf)

        # win.blit(self.surf, self.rect)

    # update the mouse position based on how much it has moved ( rel )
    # also add offset, to offset the mouse position for the surface
    def update_mouse(self, rel):
        self.mouse.update(self.offset + pygame.mouse.get_pos())
        self.pmouse.update(self.mouse - rel)

    # check for user interaction
    def check_event(self, e):

        # user interaction
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

        # wind event
        self.update_wind(e)
