import pygame
import time
import os
import random

pygame.font.init()  # some initialization to use font in pygame

WIN_HEIGHT = 800
WIN_WIDTH = 500
DRAW_LINES = False
GEN = 0  # declaring generation variable

pygame.display.set_caption("Flappy Bird")

# importing the images of birds, pipes, background and base
bird_images = [pygame.image.load("assets/bird_down.png"),
               pygame.image.load("assets/bird_mid.png"),
               pygame.image.load("assets/bird_up.png")]
skyline_image = pygame.image.load("assets/background.png")
ground_image = pygame.image.load("assets/ground.png")
top_pipe_image = pygame.image.load("assets/pipe_top.png")
bottom_pipe_image = pygame.image.load("assets/pipe_bottom.png")
game_over_image = pygame.image.load("assets/game_over.png")
start_image = pygame.image.load("assets/start.png")

# declaring font
STAT_FONT = pygame.font.SysFont('impact', 50)
game_started = False


# CLASS BIRD
class Bird:
    ROTATION_VEL = 20
    MAX_ROTATION = 25
    ANIMATION_TIME = 5
    IMGS = bird_images

    def __init__(self, x, y):  # constructor for class bird
        self.x = x
        self.y = y
        self.height = self.y
        self.frame_count = 0
        self.tilt = 0
        self.vel = 0
        self.img_number = 0  # image in which the bird's wings are upwards
        self.img = self.IMGS[0]  # image in which the bird's wings are upwards

    def jump(self):
        self.vel = -10.5  # negative velocity refers to jump upwards
        self.frame_count = 0  # reset the frames
        self.height = self.y  # reset the height

    def move(self):
        self.frame_count += 1  # update the frames when the bird moves
        # d > 0 means downwards and d<0 means upwards and same for velocity also
        # and also bird is just moving in y direction and not in x direction
        d = self.vel * self.frame_count + 1.5 * self.frame_count ** 2  # frame count also works as time
        if d >= 16:  # if the bird is falling and it falls more than 16 pixels then stop falling and face straight moving
            d = 16
        # if d < 0:   # just for tuning so that upward movement is seen clear
        #     d -= 2

        self.y = self.y + d

        # print("d:", d, "self.y:", self.y, "self.height:", self.height, "self.vel:", self.vel, "self.frame_count:", self.frame_count)

        if d < 0 or self.y < self.height + 50:  # (d<0) this is the case when when bird is going upward
            if self.tilt < self.MAX_ROTATION:  # so making a tilt angle of max rotation
                self.tilt = self.MAX_ROTATION

        else:
            if self.tilt > -90:  # if the tilt is greater than -90 then keep on reducing it till it reaches -90 to show
                self.tilt -= self.ROTATION_VEL  # the arc like falling

    def draw(self, win):
        self.img_number += 1

        # below work is done to show the flapping of the bird
        # animation time is that for how much time bird should be in one image state
        if self.img_number < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_number < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_number < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_number < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_number < self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_number = 0

        if self.tilt < -80:  # when the bird is nose diving it should not flap its wings
            self.img = self.IMGS[1]
            self.img_number = self.ANIMATION_TIME * 2  # reset the image number so that next image should be IMG[2]

        rotated_image = pygame.transform.rotate(self.img, self.tilt)  # just rotating the image around its center
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect)

    def get_mask(self):  # getting the mask of the bird means the contour of bird to check its collision with any pipe
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0  # for random purpose
        self.top = 0  # y coordinates of top pipe
        self.bottom = 0  # y coordinates of bottom pipe
        self.TOP_PIPE = top_pipe_image
        self.BOTTOM_PIPE = bottom_pipe_image
        self.passed = False
        self.set_height()

    def set_height(self):  # randomly setting the heights of both pipes
        self.height = random.randrange(50, 450)
        self.bottom = self.height + self.GAP
        self.top = self.height - self.TOP_PIPE.get_height()

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.TOP_PIPE, (self.x, self.top))
        win.blit(self.BOTTOM_PIPE, (self.x, self.bottom))

    def collide(self, bird):  # for checking collision of the bird with the pipes
        bird_mask = bird.get_mask()
        top_pipe_mask = pygame.mask.from_surface(self.TOP_PIPE)
        bottom_pipe_mask = pygame.mask.from_surface(self.BOTTOM_PIPE)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        top_overlap = bird_mask.overlap(top_pipe_mask, top_offset)
        bottom_overlap = bird_mask.overlap(bottom_pipe_mask, bottom_offset)

        if top_overlap or bottom_overlap:
            return True
        return False


# BASE Class for showing base
class Base:
    VEL = 5
    IMG = ground_image
    WIDTH = ground_image.get_width()

    def __init__(self, y):  # base will be shown moving by taking two images of the same base and putting it one after other
        self.y = y
        self.x1 = 0  # here x1 and x2 are the 2 images where x1 comes first and then x2
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 < -(self.WIDTH):
            self.x1 = self.x2 + self.WIDTH
        if self.x2 < -(self.WIDTH):
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


# Our main drawing function
def draw_window(win, bird, pipes, base, score):
    global DRAW_LINES
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

    win.blit(skyline_image, (0, 0))
    for pipe in pipes:
        pipe.draw(win)
    base.draw(win)

    bird.draw(win)

    text = STAT_FONT.render('Score : ' + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 50))

    alive_text = 'Alive : 1'
    alive_text_rendered = STAT_FONT.render(alive_text, 1, (255, 255, 255))
    win.blit(alive_text_rendered, (10, 50))

    pygame.display.update()


def main():
    global GEN, game_started

    pygame.init()
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption("Flappy Bird")

    bird = Bird(230, 350)
    pipes = [Pipe(500)]  # list of pipe objects
    base_object = Base(630)
    clock = pygame.time.Clock()
    run = True
    score = 0
    bird_jump = False

    while run:
        clock.tick(30)  # fps
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # if the user click on the red cross button then quit the game
                run = False
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not bird_jump:
                    bird.jump()
                    bird_jump = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    bird_jump = False

        pipe_ind = 0

        # this part is done to check in the case when 2 pipes appear on the screen that which is the pipe we are evaluating on
        if len(pipes) > 1 and bird.x > pipes[0].x + pipes[0].TOP_PIPE.get_width():
            pipe_ind = 1

        bird.move()
        for pipe in pipes:
            # checking if the bird has hit the ground or if the pipe and bird collide
            if pipe.collide(bird) or bird.y + bird.img.get_height() >= 630 or bird.y < 0:
                game_over_text = STAT_FONT.render('Game Over', 1, (255, 255, 255))
                win.blit(game_over_text, (WIN_WIDTH // 2 - game_over_text.get_width() // 2,
                                          WIN_HEIGHT // 2 - game_over_text.get_height() // 2))
                pygame.display.update()
                time.sleep(2)
                main()

            if not pipe.passed and bird.x > pipe.x:  # if the passed is not set to true and bird has passed the pipe then set it to true
                pipe.passed = True
                score += 1
                pipes.append(Pipe(500))  # add another pipe

            if pipe.x + pipe.TOP_PIPE.get_width() < 0:  # if pipe passed the screen add it to remove list
                pipes.remove(pipe)

            pipe.move()

        base_object.move()
        draw_window(win, bird, pipes, base_object, score)

    pygame.quit()


if __name__ == '__main__':
    main()
