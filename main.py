import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (128, 128, 128)

# Game setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mask Swap Game")
clock = pygame.time.Clock()

class Player:
    def __init__(self, x, y):
        self.width = 50
        self.height = 50
        self.x = x
        self.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.jump_strength = 15
        self.gravity = 0.8
        self.on_ground = False
        self.is_white = True  # Start as white character
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def swap_mask(self):
        """Swap between white and black character"""
        self.is_white = not self.is_white
    
    def update(self, platforms):
        # Horizontal movement
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = self.speed
        
        # Jump
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = -self.jump_strength
        
        # Apply gravity
        self.vel_y += self.gravity
        
        # Cap falling speed
        if self.vel_y > 20:
            self.vel_y = 20
        
        # Move horizontally
        self.x += self.vel_x
        
        # Horizontal collision check
        player_rect = self.get_rect()
        for platform in platforms:
            # Check if this platform should collide
            # Check if this platform should collide
            # Interaction Mode: Like lands on Like
            should_collide = (self.is_white and platform.is_white) or (not self.is_white and not platform.is_white)
            
            if should_collide:
                platform_rect = platform.get_rect()
                if player_rect.colliderect(platform_rect):
                    # Moving right
                    if self.vel_x > 0:
                        self.x = platform_rect.left - self.width
                    # Moving left
                    elif self.vel_x < 0:
                        self.x = platform_rect.right
        
        # Move vertically
        self.y += self.vel_y
        
        # Vertical collision check
        self.on_ground = False
        player_rect = self.get_rect()
        
        for platform in platforms:
            # Check if this platform should collide
            should_collide = (self.is_white and platform.is_white) or (not self.is_white and not platform.is_white)
            
            if should_collide:
                platform_rect = platform.get_rect()
                
                if player_rect.colliderect(platform_rect):
                    # Falling down (landing on platform)
                    if self.vel_y > 0:
                        self.y = platform_rect.top - self.height
                        self.vel_y = 0
                        self.on_ground = True
                    # Moving up (hitting platform from below)
                    elif self.vel_y < 0:
                        self.y = platform_rect.bottom
                        self.vel_y = 0
        
        # Keep player on screen (left/right)
        if self.x < 0:
            self.x = 0
        if self.x + self.width > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.width
        
        # Fall off screen = game over (or respawn)
        if self.y > SCREEN_HEIGHT:
            self.y = 100
            # self.x = 100
            self.vel_y = 0
    
    def draw(self, screen):
        color = WHITE if self.is_white else BLACK
        pygame.draw.rect(screen, color, self.get_rect())
        # Add a border to differentiate if needed, though high contrast helps
        border_color = GRAY
        pygame.draw.rect(screen, border_color, self.get_rect(), 2)

class Platform:
    def __init__(self, x, y, width, height, is_white=True):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_white = is_white
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, screen):
        color = WHITE if self.is_white else BLACK
        pygame.draw.rect(screen, color, self.get_rect())
        # Add border for visibility
        border_color = BLACK if self.is_white else WHITE
        pygame.draw.rect(screen, border_color, self.get_rect(), 2)

# Create player (starts as WHITE character)
player = Player(100, 100)

# Create platforms
# Remember: WHITE character lands on BLACK platforms, BLACK character lands on WHITE platforms
platforms = [
    # Starting platform (BLACK - for WHITE character)
    Platform(50, 400, 300, 30, is_white=False),
    
    # Second platform (WHITE - need to swap to BLACK character)
    Platform(400, 350, 250, 30, is_white=True),
    
    # Third platform (BLACK - swap back to WHITE character)
    Platform(700, 300, 250, 30, is_white=False),
    
    # Ground floor (BLACK)
    Platform(0, 650, SCREEN_WIDTH, 70, is_white=False),
    
    # More platforms for fun
    Platform(200, 200, 200, 30, is_white=True),
    Platform(900, 450, 200, 30, is_white=True),
]

# Main game loop
running = True
while running:
    clock.tick(FPS)
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e or event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                player.swap_mask()
                print(f"Swapped to: {'WHITE' if player.is_white else 'BLACK'}")
    
    # Update
    player.update(platforms)
    
    # Draw
    bg_color = BLACK if player.is_white else WHITE
    screen.fill(bg_color)
    
    # Draw platforms
    for platform in platforms:
        platform.draw(screen)
    
    # Draw player
    player.draw(screen)
    
    # Draw instructions
    font = pygame.font.Font(None, 36)
    player_color_text = 'WHITE' if player.is_white else 'BLACK'
    text = font.render(f"Press E/SHIFT to swap | Mode: {player_color_text}", True, (255, 255, 0))
    screen.blit(text, (10, 10))
    
    # Draw collision info
    info_text = font.render(f"White char lands on WHITE platforms | Black char lands on BLACK platforms", True, (255, 255, 0))
    screen.blit(info_text, (10, 50))
    
    pygame.display.flip()

pygame.quit()
sys.exit()