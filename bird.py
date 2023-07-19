import pygame
from sys import exit
import random
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from collections import deque

pygame.init()
clock = pygame.time.Clock()

# Window
win_height = 720
win_width = 551
window = pygame.display.set_mode((win_width, win_height))

# Images
bird_image = pygame.image.load("assets/bird_mid.png")
sky_image = pygame.image.load("assets/background.png")

# Bird
bird_start_position = (100, 250)
bird_rect = bird_image.get_rect()
bird_rect.center = bird_start_position
bird_velocity = 0

# Game
gravity = 0.5
flap_power = -10  # Adjust this value to control the bird's upward force

# Create the Q-learning model
model = Sequential()
model.add(Dense(32, input_shape=(2,), activation='relu'))
model.add(Dense(32, activation='relu'))
model.add(Dense(2, activation='linear'))
model.compile(loss='mse', optimizer=Adam())

# Experience Replay
experience_replay = deque(maxlen=10000)

# Function to preprocess the game state
def preprocess_state(y, vel):
    return np.array([y / win_height, vel / 10])

# Function to choose an action based on the Q-values
def choose_action(state, epsilon):
    if np.random.rand() < epsilon:
        return np.random.randint(2)  # Random action
    else:
        q_values = model.predict(np.array([state]))[0]
        return np.argmax(q_values)  # Action with the highest Q-value

# Function to update the Q-values based on the Bellman equation
def update_q_values(states, actions, rewards, next_states, dones, gamma):
    targets = rewards + gamma * np.max(model.predict(next_states), axis=1) * (1 - dones)
    q_values = model.predict(states)
    for i in range(len(actions)):
        q_values[i][actions[i]] = targets[i]
    model.fit(states, q_values, verbose=0)

# Game Loop
epsilon = 1.0  # Exploration rate
epsilon_decay = 0.995  # Decay rate for exploration rate
epsilon_min = 0.01  # Minimum exploration rate
gamma = 0.99  # Discount factor for future rewards
max_episodes = 1000  # Maximum number of episodes
max_steps = 1000  # Maximum number of steps per episode

for episode in range(max_episodes):
    bird_rect.center = bird_start_position
    bird_velocity = 0
    done = False
    score = 0

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        state = preprocess_state(bird_rect.centery, bird_velocity)
        action = choose_action(state, epsilon)

        if action == 0:
            bird_velocity = flap_power  # Flap the bird

        bird_velocity += gravity
        bird_velocity = min(bird_velocity, 10)  # Limit the downward velocity
        bird_rect.y += bird_velocity

        if bird_rect.top <= 0:
            bird_rect.top = 0
            bird_velocity = 0
        elif bird_rect.bottom >= win_height:
            bird_rect.bottom = win_height - 1
            bird_velocity = 0

        # Draw the sky
        window.blit(sky_image, (0, 0))

        # Draw the bird
        window.blit(bird_image, bird_rect)

        pygame.display.update()
        clock.tick(60)

        if done:
            reward = -1  # Bird went off-screen
        else:
            reward = 1  # Bird remained on-screen

        next_state = preprocess_state(bird_rect.centery, bird_velocity)
        experience_replay.append((state, action, reward, next_state, done))

        if len(experience_replay) > 100:
            batch = random.sample(experience_replay, 32)
            states, actions, rewards, next_states, dones = zip(*batch)
            update_q_values(np.array(states), np.array(actions), np.array(rewards),
                            np.array(next_states), np.array(dones), gamma)

    epsilon *= epsilon_decay
    epsilon = max(epsilon, epsilon_min)
