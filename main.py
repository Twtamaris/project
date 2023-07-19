import pygame
import random
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam

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
scroll_speed = 1
bird_start_position = (100, 250)
score = 0
font = pygame.font.SysFont('Segoe', 26)
game_stopped = True

# Create the Q-learning model
model = Sequential()
model.add(Dense(32, input_shape=(4,), activation='relu'))
model.add(Dense(32, activation='relu'))
model.add(Dense(2, activation='linear'))
model.compile(loss='mse', optimizer=Adam())

# Function to preprocess the game state
def preprocess_state(bird, pipes):
    bird_y = bird.rect.centery / win_height
    next_pipe = None
    for pipe in pipes:
        if pipe.rect.x > bird.rect.right:
            next_pipe = pipe
            break
    if next_pipe:
        pipe_dist = (next_pipe.rect.x - bird.rect.right) / win_width
        pipe_top = next_pipe.rect.top / win_height    
        pipe_bottom = next_pipe.rect.bottom / win_height
    else:
        pipe_dist = 1.0
        pipe_top = 1.0
        pipe_bottom = 1.0
    return np.array([bird_y, pipe_dist, pipe_top, pipe_bottom])

# Function to choose an action based on the Q-values
def choose_action(state, epsilon):
    if np.random.rand() < epsilon:
        return np.random.randint(2)
    else:
        q_values = model.predict(np.array([state]))[0]
        return np.argmax(q_values)
    
# Function to update the Q-values based on the Bellman equation
def update_q_values(states, actions, rewards, next_states, dones, gamma):
    targets = rewards + gamma * np.max(model.predict(next_states), axis=1) * (1 - dones)
    q_values = model.predict(states)
    for i in range(len(actions)):
        q_values[i][actions[i]] = targets[i]
    model.fit(states, q_values, verbose=0)

class Bird(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.images = bird_images
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=bird_start_position)
        self.image_index = 0
        self.vel = 0
        self.flap = False
        self.alive = True

    def update(self, user_input):
        if self.alive:
            self.image_index = (self.image_index + 1) % len(self.images)
            self.image = self.images[self.image_index]

        self.vel += 0.5
        self.vel = min(self.vel, 7)
        self.rect.y += int(self.vel)

        if user_input[pygame.K_SPACE] and not self.flap and self.alive:
            self.flap = True
            self.vel = -7

        self.image = pygame.transform.rotate(self.images[self.image_index], self.vel * -7)

class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, image, pipe_type):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.enter, self.exit, self.passed = False, False, False
        self.pipe_type = pipe_type

    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.right <= 0:
            self.kill()

        global score
        if self.pipe_type == 'bottom':
            if bird.rect.right > self.rect.left and not self.passed:
                self.enter = True
            if bird.rect.right > self.rect.right and not self.passed:
                self.exit = True
            if self.enter and self.exit and not self.passed:
                self.passed = True
                score += 1

class Ground(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = ground_image
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.right <= 0:
            self.kill()

def quit_game():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

def main():
    global score
    
    bird = Bird()
    
    epsilon = 1.0  # Exploration rate
    epsilon_decay = 0.999  # Decay rate for exploration rate
    epsilon_min = 0.01  # Minimum exploration rate
    gamma = 0.99  # Discount factor for future rewards
    max_episodes = 20  # Maximum number of episodes
    max_steps = 1000  # Maximum number of steps per episode
    
    for episode in range(max_episodes):
        pipe_timer = 0
        pipes = pygame.sprite.Group()

        x_pos_ground, y_pos_ground = 0, 520
        ground = pygame.sprite.Group()
        ground.add(Ground(x_pos_ground, y_pos_ground))
        
        bird.alive = True
        bird.rect.center = bird_start_position
        bird.vel = 0
        score = 0

        for step in range(max_steps):
            quit_game() 

            window.fill((0, 0, 0))
            window.blit(skyline_image, (0, 0))

            if len(ground) <= 2:
                ground.add(Ground(win_width, y_pos_ground))

            pipes.draw(window)
            ground.draw(window)
            window.blit(bird.image, bird.rect)

            score_text = font.render('Score: ' + str(score), True, pygame.Color(255, 255, 255))
            window.blit(score_text, (20, 20))

            state = preprocess_state(bird, pipes)
            action = choose_action(state, epsilon)

            if action == 0:
                bird.flap = True

            if bird.alive:
                pipes.update()
                ground.update()
            bird.update(pygame.key.get_pressed())

            collision_pipes = pygame.sprite.spritecollide(bird, pipes, False)
            collision_ground = pygame.sprite.spritecollide(bird, ground, False)
            if collision_pipes or collision_ground:
                bird.alive = False
                if collision_ground:
                    window.blit(game_over_image, (win_width // 2 - game_over_image.get_width() // 2,
                                                win_height // 2 - game_over_image.get_height() // 2))
                    if pygame.key.get_pressed()[pygame.K_r]:
                        score = 0
                        break

            next_state = preprocess_state(bird, pipes)
            reward = 1 if bird.alive else -1
            done = not bird.alive

            update_q_values(np.array([state]), np.array([action]), np.array([reward]), np.array([next_state]), np.array([done]), gamma)

            if pipe_timer <= 0 and bird.alive:
                x_top, x_bottom = 550, 550
                y_top = random.randint(-600, -480)
                y_bottom = y_top + random.randint(90, 130) + bottom_pipe_image.get_height()
                pipes.add(Pipe(x_top, y_top, top_pipe_image, 'top'))
                pipes.add(Pipe(x_bottom, y_bottom, bottom_pipe_image, 'bottom'))
                pipe_timer = random.randint(180, 250)
            pipe_timer -= 1

            clock.tick(60)
            pygame.display.update()

            if done:
                break

        epsilon *= epsilon_decay
        epsilon = max(epsilon, epsilon_min)

def menu():
    global game_stopped

    while game_stopped:
        quit_game() 

        window.fill((0, 0, 0))
        window.blit(skyline_image, (0, 0))
        window.blit(ground_image, Ground(0, 520))
        window.blit(bird_images[0], (100, 250))
        window.blit(start_image, (win_width // 2 - start_image.get_width() // 2,
                                  win_height // 2 - start_image.get_height() // 2))

        user_input = pygame.key.get_pressed()
        if user_input[pygame.K_SPACE]:
            main()

        pygame.display.update()

menu()
