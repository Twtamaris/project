import pygame
from sys import exit

from sys import exit
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
    # Normalize the bird's y position and the distance to the next pipe
    bird_y = bird.rect.y / win_height
    next_pipe = None
    for pipe in pipes:
        if pipe.rect.x > bird.rect.x:
            next_pipe = pipe
            break
    if next_pipe:
        pipe_dist = (next_pipe.rect.x - bird.rect.x) / win_width
        pipe_top = next_pipe.rect.y / win_height
        pipe_bottom = (next_pipe.rect.y + next_pipe.rect.height) / win_height
    else:
        # If there are no pipes, set the distance to 1
        pipe_dist = 1.0
        pipe_top = 1.0
        pipe_bottom = 1.0
    return np.array([bird_y, pipe_dist, pipe_top, pipe_bottom])

# Function to choose an action based on the Q-values
def choose_action(state, epsilon):
    if np.random.rand() < epsilon:
        # Choose a random action (exploration)
        return np.random.randint(2)
    else:
        # Choose the action with the highest Q-value (exploitation)
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
        self.image = bird_images[0]
        self.rect = self.image.get_rect()
        self.rect.center = bird_start_position
        self.image_index = 0
        self.vel = 0
        self.flap = False
        self.alive = True

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

        # User Input
        if user_input[pygame.K_SPACE] and not self.flap and self.rect.y > 0 and self.alive:
            self.flap = True
            self.vel = -7


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


# Game Main Method
def main():
    global score
    
    # Instantiate Bird
    bird = pygame.sprite.GroupSingle()
    bird.add(Bird())
    
    
    epsilon = 1.0  # Exploration rate
    epsilon_decay = 0.999  # Decay rate for exploration rate
    epsilon_min = 0.01  # Minimum exploration rate
    gamma = 0.99  # Discount factor for future rewards
    max_episodes = 1000  # Maximum number of episodes
    max_steps = 1000  # Maximum number of steps per episode



    # Setup Pipes
    pipe_timer = 0
    pipes = pygame.sprite.Group()

    # Instantiate Initial Ground
    x_pos_ground, y_pos_ground = 0, 520
    ground = pygame.sprite.Group()
    ground.add(Ground(x_pos_ground, y_pos_ground))

    run = True
    for episode in range(max_episodes):

        # Reset the game...
        bird.sprite.alive = True
        bird.sprite.rect.center = bird_start_position
        score = 0
        pipes.empty()
        ground.empty()
        ground.add(Ground(x_pos_ground, y_pos_ground))

        for step in range(max_steps):
            # Quit...
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

            # Reset Frame
            window.fill((0, 0, 0))

            # User Input
            user_input = pygame.key.get_pressed()

            # Draw Background
            window.blit(skyline_image, (0, 0))

            # Spawn Ground
            if len(ground) <= 2:
                ground.add(Ground(win_width, y_pos_ground))

            # Draw - Pipes, Ground and Bird
            pipes.draw(window)
            ground.draw(window)
            bird.draw(window)

            # Show Score
            score_text = font.render('Score: ' + str(score), True, pygame.Color(255, 255, 255))
            window.blit(score_text, (20, 20))

            # Choose an action...
            state = preprocess_state(bird.sprite, pipes)
            action = choose_action(state, epsilon)
            
            
            # Take the action and observe the next state and reward...
            if action == 0:
                bird.sprite.flap = True




            # Update - Pipes, Ground and Bird
            if bird.sprite.alive:
                pipes.update()
                ground.update()
            bird.update(user_input)

            # Collision Detection
            collision_pipes = pygame.sprite.spritecollide(bird.sprites()[0], pipes, False)
            collision_ground = pygame.sprite.spritecollide(bird.sprites()[0], ground, False)
            if collision_pipes or collision_ground:
                bird.sprite.alive = False
                if collision_ground:
                    window.blit(game_over_image, (win_width // 2 - game_over_image.get_width() // 2,
                                                win_height // 2 - game_over_image.get_height() // 2))
                    if user_input[pygame.K_r]:
                        score = 0
                        break
                    
            # Preprocess the next state...
            next_state = preprocess_state(bird.sprite, pipes)

                # Determine the reward...
            reward = 1 if bird.sprite.alive else -1
            
                        # Determine if the episode is done...
            done = not bird.sprite.alive

            # Update the Q-values...
            if bird.sprite.alive:
                update_q_values(np.array([state]), np.array([action]), np.array([reward]), np.array([next_state]), np.array([done]), gamma)

            

            # Spawn Pipes
            if pipe_timer <= 0 and bird.sprite.alive:
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
        
        # Decay the exploration rate...
        epsilon *= epsilon_decay
        epsilon = max(epsilon, epsilon_min)

        


# Menu
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
            main()

        pygame.display.update()


menu()
