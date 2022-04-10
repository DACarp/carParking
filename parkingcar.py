# This Code is Heavily Inspired By The YouTuber: Cheesy AI
# Code Changed, Optimized And Commented By: NeuralNine (Florian Dedov)

# Code changed for parking simulation by

import math
import random
import sys
import os

import neat
import pygame

# Constants
# WIDTH = 1600
# HEIGHT = 880

WIDTH = 1920
HEIGHT = 1080

CAR_SIZE_X = 60
CAR_SIZE_Y = 60

BORDER_COLOR = (255, 255, 255, 255)  # Color To Crash on Hit (White)
BEST_SPOTS_COLOR = (0, 200, 0, 255)  # Color for best parking spots (Green)
MED_SPOTS_COLOR = (255, 200, 0, 255) # Color for middle parking spots (Yellow)
BAD_SPOTS_COLOR = ()  # Color for worst parking spots (red)

DOOR_LOCATION = [1060, 160]  # Target for the agents, for tuning of parking spaces chosen.

current_generation = 0  # Generation counter


class Car:

    def __init__(self):
        # Load Car Sprite and Rotate
        self.sprite = pygame.image.load('car.png').convert()  # Convert Speeds Up A Lot
        self.sprite = pygame.transform.scale(self.sprite, (CAR_SIZE_X, CAR_SIZE_Y))
        self.rotated_sprite = self.sprite 

        self.position = [930, 930]  # map starting position
        self.angle = 180
        self.speed = 0

        self.speed_set = False  # Flag for starting speed

        self.center = [self.position[0] + CAR_SIZE_X / 2, self.position[1] + CAR_SIZE_Y / 2]  # Calculate Center

        self.radars = []  # List For Sensors / Radars
        self.drawing_radars = []  # Radars To Be Drawn

        self.active = True  # Boolean To Check If Car is Crashed or has finished
        self.has_crashed = False  #
        self.final_time = 0  # Time at which the car became inactive, in frames

        self.last_choice = 4  # What the car's action choice was last frame

        self.distance = 0  # Distance Driven
        self.time = 0  # Time Passed in Frames (usually a few dozen/few hundred)

    def draw(self, screen):
        screen.blit(self.rotated_sprite, self.position) # Draw Sprite
        #  self.draw_radar(screen)  # OPTIONAL FOR SENSORS

    def draw_radar(self, screen):
        # Optionally Draw All Sensors / Radars
        for radar in self.radars:
            position = radar[0]
            pygame.draw.line(screen, (0, 255, 0), self.center, position, 1)
            pygame.draw.circle(screen, (0, 255, 0), position, 5)

    def check_collision(self, game_map):
        for point in self.corners:
            # If Any Corner Touches Border Color -> Crash
            # Assumes Rectangle
            if game_map.get_at((int(point[0]), int(point[1]))) == BORDER_COLOR:
                self.active = False
                self.has_crashed = True
                self.final_time = self.time
                self.speed = 0  # Stop car and update flags
                self.sprite = pygame.image.load('carRed.png').convert()
                self.sprite = pygame.transform.scale(self.sprite, (CAR_SIZE_X, CAR_SIZE_Y))
                self.rotated_sprite = self.rotate_center(self.sprite, self.angle)

                break

    def check_radar(self, degree, game_map):
        length = 0
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # While We Don't Hit BORDER_COLOR AND length < 1000 (just a max) -> go further and further
        while not game_map.get_at((x, y)) == BORDER_COLOR and length < 1000:
            length = length + 1
            x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
            y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

        # Calculate Distance To Border And Append To Radars List
        dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
        self.radars.append([(x, y), dist])
    
    def update(self, game_map):
        # Speed starts at 10
        if not self.speed_set:
            self.speed = 10
            self.speed_set = True

        # Get Rotated Sprite And Move Into The Right X-Direction
        # Don't Let The Car Go Closer Than 20px To The Edge
        self.rotated_sprite = self.rotate_center(self.sprite, self.angle)
        self.position[0] += math.cos(math.radians(360 - self.angle)) * self.speed
        self.position[0] = max(self.position[0], 20)
        self.position[0] = min(self.position[0], WIDTH - 120)

        # Increase Distance and Time
        self.distance += self.speed
        self.time += 1
        
        # Same For Y-Position
        self.position[1] += math.sin(math.radians(360 - self.angle)) * self.speed
        self.position[1] = max(self.position[1], 20)
        self.position[1] = min(self.position[1], WIDTH - 120)

        # Calculate New Center
        self.center = [int(self.position[0]) + CAR_SIZE_X / 2, int(self.position[1]) + CAR_SIZE_Y / 2]

        # Calculate Four Corners
        # Length Is Half The Side
        length = 0.5 * CAR_SIZE_X
        left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * length]
        right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * length]
        left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * length]
        right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * length]
        self.corners = [left_top, right_top, left_bottom, right_bottom]

        # Check Collisions And Clear Radars
        if not self.has_crashed:
            self.check_collision(game_map)

        self.radars.clear()

        # From -90 To 120 With Step-Size 45 Check Radar
        for d in range(-90, 120, 45):
            self.check_radar(d, game_map)

    def get_data(self):
        # Get Distances To Border
        radars = self.radars
        return_values = [0, 0, 0, 0, 0]
        for i, radar in enumerate(radars):
            return_values[i] = int(radar[1] / 30)

        return return_values

    def is_active(self):
        return self.active

    def get_reward(self, game_map):

        score = 3000  # Base score

        car_x = int(self.center[0])
        car_y = int(self.center[1])

        spot_color = game_map.get_at((car_x, car_y))
        distance = math.hypot(car_x - DOOR_LOCATION[0], car_y - DOOR_LOCATION[1])
        # Distance from the car to the spot in front of the door, about a thousand at far corners

        if spot_color == BEST_SPOTS_COLOR:  # Green
            multiplier = 5
        elif spot_color == MED_SPOTS_COLOR:  # Yellow
            multiplier = 4
        elif spot_color == BAD_SPOTS_COLOR:  # Red
            multiplier = 3
        else:  # No spot
            multiplier = 1

        if self.active:  # Car did not signal finish, but did not crash
            score = score * multiplier
        else:  # Car signaled finish
            score = score * (multiplier + 1)
        # TODO: implement scoring based on alignment with parking spot. All spots of one color
        #       are oriented the same way, so checking orientation based on spot color is easy.
        #       Can also check for being closer to the center of a parking spot by comparing
        #       length of the left and right sensors.

        score = (score - distance) - self.final_time
        # Penalties for distance from target and time spent

        if self.has_crashed:  # Car was stopped by crash, overwrite score
            score = (800 - distance) + multiplier*12  # Give low score, but a slight push
            #  toward parking spaces

        # Debug
        if self.has_crashed:
            status = "Crashed"
        elif self.active:
            status = "Timed Out"
        else:
            status = "Parked"
        print("Status: " + status)
        print("Time: " + str(self.final_time))
        print("Distance: " + str(distance))
        print("Fitness: " + str(score))
        print("Spot Multiplier: " + str(multiplier))
        print()
        # Debug

        return score

    def rotate_center(self, image, angle):
        # Rotate The Rectangle
        rectangle = image.get_rect()
        rotated_image = pygame.transform.rotate(image, angle)
        rotated_rectangle = rectangle.copy()
        rotated_rectangle.center = rotated_image.get_rect().center
        rotated_image = rotated_image.subsurface(rotated_rectangle).copy()
        return rotated_image


def run_simulation(genomes, config):
    
    # Empty Collections For Nets and Cars
    nets = []
    cars = []

    # Initialize PyGame And The Display
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)

    # For All Genomes Passed Create A New Neural Network
    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0

        cars.append(Car())

    # Clock Settings
    # Font Settings & Loading Map
    clock = pygame.time.Clock()
    generation_font = pygame.font.SysFont("Arial", 30)
    active_font = pygame.font.SysFont("Arial", 20)

    game_map = pygame.image.load('Map01.png').convert()  # Convert Speeds Up A Lot
    # TODO: Randomize map, either by choosing a random one or randomly blocking
    #       parking spots. Will demonstrate algorithm robustness.

    global current_generation
    current_generation += 1

    # Simple Counter To Roughly Limit Time (Not Good Practice)
    counter = 0

    while True:
        # Exit On Quit Event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

        # For Each Car Get The Acton It Takes, unless it has stopped
        for i, car in enumerate(cars):
            output = nets[i].activate(car.get_data())
            choice = output.index(max(output))

            if not car.active:
                continue # Ignore this car if it is no longer active
            if choice == 0:  # LEFT
                car.angle += 10

            elif choice == 1:  # RIGHT
                car.angle -= 10

            elif choice == 2:  # BRAKE
                if car.speed == 1:  # Stop moving and set flags
                    car.speed = 0
                    car.final_time = car.time
                    car.active = False
                else:  # Reduce speed by 1
                    car.speed -= 1

            elif choice == 3:  # ACCELERATE
                if car.speed <= 14:
                    car.speed += 1

            # Choice 4 is COAST, changing nothing and requiring no code.

            car.last_choice = choice
            # TODO: subtract "bad handling" from score, representing over-acceleration as consecutive
            #       acceleration/brake commands, steering at high speed. Would need a "handling
            #       penalty" field of the car object to subtract from score. Don't overdo, handling
            #       would be a minor optimization after cars have figured out how to park at all.

        # Check if cars are still active
        still_active = 0
        for i, car in enumerate(cars):
            if car.is_active():
                still_active += 1
                car.update(game_map)

        if still_active == 0:  # If all cars are stopped, get their reward and go to next iteration.
            for i, car in enumerate(cars):
                genomes[i][1].fitness += car.get_reward(game_map)
            break

        counter += 1
        if counter == 30 * 20:  # Stop after about 10 seconds
            for i, car in enumerate(cars):
                if car.is_active():
                    car.final_time = car.time

                genomes[i][1].fitness += car.get_reward(game_map)
            break

        # Draw Map And All Cars
        screen.blit(game_map, (0, 0))
        for car in cars:
            car.draw(screen)
        
        # Display Info
        text = generation_font.render("Generation: " + str(current_generation), True, (0,0,0))
        text_rect = text.get_rect()
        text_rect.center = (1220, 50)
        screen.blit(text, text_rect)

        text = active_font.render("Still Active: " + str(still_active), True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (1220, 30)
        screen.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(60) # 60 FPS


if __name__ == "__main__":

    # Load Config
    config_path = "./config.txt"
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                config_path)

    # Create Population And Add Reporters
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    
    # Run Simulation For A Maximum of 100,000 Generations
    population.run(run_simulation, 100000)
