import pygame
from sys import exit
import random
import neat

pygame.init()
clock = pygame.time.Clock()

# Window
win_height = 720
win_width = 551
window = pygame.display.set_mode((win_width, win_height))

# Images
bird_images = [pygame.image.load("assets/bird_down.png"),
               pygame.image.load("assets/bird_mid.png"),
               pygame.image.load("assets/bird_up.png")]
skyline_image = pygame.image.load("assets/background.png")
ground_image = pygame.image.load("assets/ground.png")
top_pipe_image = pygame.image.load("assets/pipe_top.png")
bottom_pipe_image = pygame.image.load("assets/pipe_bottom.png")
game_over_image = pygame.image.load("assets/game_over.png")
start_image = pygame.image.load("assets/start.png")

# Game
scroll_speed = 3
bird_start_position = (100, 250)
score = 0
font = pygame.font.SysFont('Segoe', 26)
game_stopped = True


class Bird(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = bird_images[0]
        self.rect = self.image.get_rect()
        self.rect.center = bird_start_position
        self.image_index = 0
        self.vel = 0
        self.flap = False
        self.alive = True

    def flap_wings(self):
        self.flap = True
        self.vel = -7
    

    def update(self, user_input):
        # Animate Bird
        if self.alive:
            self.image_index += 1
        if self.image_index >= 30:
            self.image_index = 0
        self.image = bird_images[self.image_index // 10]

        # Gravity and Flap
        self.vel += 0.5
        if self.vel > 7:
            self.vel = 7
        if self.rect.y < 500:

            self.rect.y += int(self.vel)
        if self.vel == 0:
            self.flap = False

        # Rotate Bird
        self.image = pygame.transform.rotate(self.image, self.vel * -7)

        # # User Input
        # if user_input[pygame.K_SPACE] and not self.flap and self.rect.y > 0 and self.alive:
        #     self.flap = True
        #     self.vel = -7


class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, image, pipe_type):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.enter, self.exit, self.passed = False, False, False
        self.pipe_type = pipe_type

    def update(self):
        # Move Pipe
        self.rect.x -= scroll_speed
        if self.rect.x <= -win_width:
            self.kill()

        # Score
        global score
        if self.pipe_type == 'bottom':
            if bird_start_position[0] > self.rect.topleft[0] and not self.passed:
                print("Entry")
                self.enter = True
            if bird_start_position[0] > self.rect.topright[0] and not self.passed:
                self.exit = True
            if self.enter and self.exit and not self.passed:
                self.passed = True
                score += 1


class Ground(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = ground_image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

    def update(self):
        # Move Ground
        self.rect.x -= scroll_speed
        if self.rect.x <= -win_width:
            self.kill()


def quit_game():
    # Exit Game
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()



# NEAT Training Function
def eval_genomes(genomes, config):
    global score

    birds = []
    neural_networks = []
    ge = []

    # Setup Pipes
    pipe_timer = 0
    pipes = pygame.sprite.Group()

    # Instantiate Initial Ground
    x_pos_ground, y_pos_ground = 0, 520
    ground = pygame.sprite.Group()
    ground.add(Ground(x_pos_ground, y_pos_ground))

    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        neural_networks.append(net)
        bird = Bird()
        birds.append(bird)
        ge.append(genome)
        genome.fitness = 0

    bird_group = pygame.sprite.Group(birds)

    run = True
    while run:
        # Quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        # Reset Frame
        window.fill((0, 0, 0))

        # Draw Background
        window.blit(skyline_image, (0, 0))

        # Spawn Ground
        if len(ground) <= 2:
            ground.add(Ground(win_width, y_pos_ground))

        # Draw - Pipes, Ground and Bird
        pipes.draw(window)
        ground.draw(window)
        bird_group.draw(window)

        # Show Score
        score_text = font.render('Score: ' + str(score), True, pygame.Color(255, 255, 255))
        window.blit(score_text, (20, 20))

        for bird, net, genome in zip(birds, neural_networks, ge):
            input_data = None  # Initialize the variable here
            if bird.alive:
                pipes.update()
                ground.update()

                # Neural Network Input
                nearest_pipe_ind = 0
                pipe_list = pipes.sprites()  # Convert group to a list of sprites
                if len(pipe_list) > 1:
                    if bird.rect.centerx > pipe_list[0].rect.centerx:
                        nearest_pipe_ind = 1

                if nearest_pipe_ind < len(pipe_list):
                    input_data = (bird.rect.y, abs(bird.rect.y - pipe_list[nearest_pipe_ind].rect.height), 
                                  abs(bird.rect.y - pipe_list[nearest_pipe_ind].rect.bottom))

                if input_data is not None:  # Check if input_data is assigned a value before using it
                    output = net.activate(input_data)
                else:
                    output = [0]  # Set default value if input_data is None

                if output[0] > 0.5:
                    bird.flap_wings()

                # ... (existing code)


            collision_pipes = pygame.sprite.spritecollide(bird, pipes, False)
            collision_ground = pygame.sprite.spritecollide(bird, ground, False)
            if collision_pipes or collision_ground:
                bird.alive = False
                genome.fitness -= 1

            # Check if the bird passed a pipe
            for pipe in pipes:
                if pipe.pipe_type == 'bottom' and bird.rect.centerx > pipe.rect.centerx and not pipe.passed:
                    pipe.passed = True
                    genome.fitness += 5

        # Spawn Pipes
        if pipe_timer <= 0 and any(bird.alive for bird in birds):
            x_top, x_bottom = 550, 550
            y_top = random.randint(-600, -480)
            y_bottom = y_top + random.randint(110, 130) + bottom_pipe_image.get_height()
            pipes.add(Pipe(x_top, y_top, top_pipe_image, 'top'))
            pipes.add(Pipe(x_bottom, y_bottom, bottom_pipe_image, 'bottom'))
            pipe_timer = random.randint(180, 250)
        pipe_timer -= 2

        clock.tick(60)
        pygame.display.update()

        # Check if all birds are dead
        if not any(bird.alive for bird in birds):
            break

# Run NEAT algorithm
def run_neat(config_file):
    # Load NEAT configuration
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation, config_file)

    # Create a population
    population = neat.Population(config)

    # Add a reporter to show progress in the terminal
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    # Run the NEAT algorithm
    winner = population.run(eval_genomes, 50)

    print("Best genome:\n", winner)


def menu():
    global game_stopped

    while game_stopped:
        quit_game()

        # Draw Menu
        window.fill((0, 0, 0))
        window.blit(skyline_image, (0, 0))
        window.blit(ground_image, Ground(0, 520))
        window.blit(bird_images[0], (100, 250))
        window.blit(start_image, (win_width // 2 - start_image.get_width() // 2,
                                  win_height // 2 - start_image.get_height() // 2))

        # User Input
        user_input = pygame.key.get_pressed()
        if user_input[pygame.K_SPACE]:
            run_neat("config-feedforward.txt")  # Start the NEAT algorithm

        pygame.display.update()


menu()