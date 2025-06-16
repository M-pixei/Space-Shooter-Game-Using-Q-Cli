import pygame
import random
import os
import time
from pygame import mixer

# Initialize pygame
pygame.init()

# Set up the game window
WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")

# Load images
# Note: You'll need to create or download these images
PLAYER_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("assets", "player_ship.png")), (50, 50))
ENEMY_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("assets", "enemy_ship.png")), (40, 40))
LASER_PLAYER = pygame.transform.scale(pygame.image.load(os.path.join("assets", "laser_player.png")), (5, 20))
LASER_ENEMY = pygame.transform.scale(pygame.image.load(os.path.join("assets", "laser_enemy.png")), (5, 20))
BACKGROUND = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background.png")), (WIDTH, HEIGHT))

# Load sounds
mixer.music.load(os.path.join("assets", "background.wav"))
mixer.music.play(-1)  # Play on loop
laser_sound = mixer.Sound(os.path.join("assets", "laser.wav"))
explosion_sound = mixer.Sound(os.path.join("assets", "explosion.wav"))

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

# Game variables
FPS = 60
clock = pygame.time.Clock()
level = 0
lives = 5
score = 0
high_score = 0
main_font = pygame.font.SysFont("comicsans", 30)
lost_font = pygame.font.SysFont("comicsans", 60)

# Load high score if exists
try:
    with open("highscore.txt", "r") as f:
        high_score = int(f.read())
except:
    high_score = 0

class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not(self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)

class Ship:
    COOLDOWN = 30  # Half a second cooldown at 60 FPS

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers[:]:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x + self.ship_img.get_width()//2 - self.laser_img.get_width()//2, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1
            laser_sound.play()

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = PLAYER_SHIP
        self.laser_img = LASER_PLAYER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def move_lasers(self, vel, objs):
        self.cooldown()
        for laser in self.lasers[:]:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        explosion_sound.play()
                        global score
                        score += 10
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, RED, (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, GREEN, (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (self.health/self.max_health), 10))

class Enemy(Ship):
    COLOR_MAP = {
        "red": (ENEMY_SHIP, LASER_ENEMY),
        "blue": (ENEMY_SHIP, LASER_ENEMY),
        "green": (ENEMY_SHIP, LASER_ENEMY)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x + self.ship_img.get_width()//2 - self.laser_img.get_width()//2, self.y + self.ship_img.get_height(), self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None

def main():
    global level, lives, score, high_score
    run = True
    lost = False
    lost_count = 0

    player_vel = 5
    laser_vel = 5
    enemy_vel = 1
    enemy_laser_vel = 4

    player = Player(WIDTH//2 - 25, HEIGHT - 100)
    enemies = []
    wave_length = 5

    def redraw_window():
        win.blit(BACKGROUND, (0, 0))
        
        # Draw UI elements
        lives_label = main_font.render(f"Lives: {lives}", 1, WHITE)
        level_label = main_font.render(f"Level: {level}", 1, WHITE)
        score_label = main_font.render(f"Score: {score}", 1, WHITE)
        high_score_label = main_font.render(f"High Score: {high_score}", 1, WHITE)
        
        win.blit(lives_label, (10, 10))
        win.blit(level_label, (10, 40))
        win.blit(score_label, (WIDTH - score_label.get_width() - 10, 10))
        win.blit(high_score_label, (WIDTH - high_score_label.get_width() - 10, 40))

        # Draw enemies
        for enemy in enemies:
            enemy.draw(win)

        # Draw player
        player.draw(win)

        # Draw lost message
        if lost:
            lost_label = lost_font.render("You Lost!!", 1, WHITE)
            win.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, HEIGHT/2 - lost_label.get_height()/2))

        pygame.display.update()

    while run:
        clock.tick(FPS)
        redraw_window()

        # Check if player lost
        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1

        # Display lost message for 3 seconds
        if lost:
            if lost_count > FPS * 3:
                # Update high score if needed
                if score > high_score:
                    high_score = score
                    with open("highscore.txt", "w") as f:
                        f.write(str(high_score))
                
                # Reset game
                run = False
            else:
                continue

        # Create new wave of enemies
        if len(enemies) == 0:
            level += 1
            wave_length += 5
            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1500, -100), 
                             random.choice(["red", "blue", "green"]))
                enemies.append(enemy)

        # Check for quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        # Player movement controls
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.x - player_vel > 0:  # left
            player.x -= player_vel
        if keys[pygame.K_RIGHT] and player.x + player_vel + player.get_width() < WIDTH:  # right
            player.x += player_vel
        if keys[pygame.K_UP] and player.y - player_vel > 0:  # up
            player.y -= player_vel
        if keys[pygame.K_DOWN] and player.y + player_vel + player.get_height() + 15 < HEIGHT:  # down
            player.y += player_vel
        if keys[pygame.K_SPACE]:
            player.shoot()

        # Move enemies and their lasers
        for enemy in enemies[:]:
            enemy.move(enemy_vel)
            enemy.move_lasers(enemy_laser_vel, player)

            # Random enemy shooting
            if random.randrange(0, 120) == 1:
                enemy.shoot()

            # Check collision with player
            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
                explosion_sound.play()
                score += 5

            # Check if enemy passed the screen
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)

        # Move player lasers
        player.move_lasers(-laser_vel, enemies)

def main_menu():
    title_font = pygame.font.SysFont("comicsans", 50)
    run = True
    
    while run:
        win.blit(BACKGROUND, (0, 0))
        title_label = title_font.render("Click to begin...", 1, WHITE)
        win.blit(title_label, (WIDTH/2 - title_label.get_width()/2, HEIGHT/2 - title_label.get_height()/2))
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                main()
    
    pygame.quit()

if __name__ == "__main__":
    main_menu()
