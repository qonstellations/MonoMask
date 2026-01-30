import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Colors
WHITE = (240, 240, 230) # Cream/Off-White
BLACK = (20, 20, 20)    # Soft Black
RED = (255, 60, 60)     # Soft Red
GRAY = (128, 128, 128) # Neutral Gray

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
        self.is_white = True
          # Start as white character
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def swap_mask(self):
        """Swap between white and black character"""
        self.is_white = not self.is_white

    def is_neutral_collision(self, platform):
        if platform.is_neutral:
            return True
        return (self.is_white and platform.is_white) or (not self.is_white and not platform.is_white)
    
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
            # Interaction Mode: Like lands on Like OR Neutral lands on everything
            should_collide = self.is_neutral_collision(platform)
            
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
            should_collide = self.is_neutral_collision(platform)
            
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
    def __init__(self, x, y, width, height, is_white=True, is_neutral=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_white = is_white
        self.is_neutral = is_neutral
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, is_white_mode):
        if self.is_neutral:
            color = GRAY
            # Neutral is always filled/active
            pygame.draw.rect(screen, color, self.get_rect())
            pygame.draw.rect(screen, BLACK if is_white_mode else WHITE, self.get_rect(), 2) # Border contrast
            return

        # Platform drawing depends on mode
        # If platform is same color as mode (Active) -> Filled
        # If platform is diff color as mode (Inactive) -> Outline (Ghost)
        should_be_filled = (self.is_white and is_white_mode) or (not self.is_white and not is_white_mode)
        
        color = WHITE if self.is_white else BLACK
        
        if should_be_filled:
            pygame.draw.rect(screen, color, self.get_rect())
            # Border for contrast
            border_color = GRAY
            pygame.draw.rect(screen, border_color, self.get_rect(), 2)
        else:
            # Ghost mode (outline only)
            border_color = color # Use its own color as outline
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
    
    # Ground floor (Neutral)
    Platform(0, 650, SCREEN_WIDTH, 70, is_neutral=True),
    
    # More platforms for fun
    Platform(200, 200, 200, 30, is_white=True),
    Platform(900, 450, 200, 30, is_white=True),
    
    # Neutral floating platform
    Platform(500, 550, 200, 30, is_neutral=True),
]

# Helper function to draw the game state
def draw_game(surface, is_white_mode, player, platforms):
    # Background
    bg_color = BLACK if is_white_mode else WHITE
    surface.fill(bg_color)
    
    # Draw platforms
    for platform in platforms:
        platform.draw(surface, is_white_mode)
    
    # Draw player
    player.draw(surface)
    
    # Draw UI
    font = pygame.font.Font(None, 36)
    # Text color inverse of background
    text_color = WHITE if not is_white_mode else BLACK
    
    mode_text = 'WHITE' if is_white_mode else 'BLACK'
    text = font.render(f"Press E/SHIFT to swap | Mode: {mode_text}", True, (255, 255, 0)) # Yellow always visible
    surface.blit(text, (10, 10))
    
    info_text = font.render(f"White/Black: Lands on SAME color | GRAY: Neutral (Lands on BOTH)", True, (255, 255, 0))
    surface.blit(info_text, (10, 50))


# Main game loop
running = True

# Transition state
transition_active = False
transition_radius = 0
transition_speed = 30
max_radius = int((SCREEN_WIDTH**2 + SCREEN_HEIGHT**2)**0.5) + 50
transition_center = (0, 0)
# Surfaces for transition
current_screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
next_screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

while running:
    clock.tick(FPS)
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e or event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                if not transition_active:
                    # Start transition
                    transition_active = True
                    transition_radius = 0
                    transition_center = (int(player.x + player.width/2), int(player.y + player.height/2))
                    
                    # Store current visual state before swap (using current player state)
                    draw_game(current_screen, player.is_white, player, platforms)
                    
                    # Swap physics state immediately
                    player.swap_mask()
                    print(f"Swapped to: {'WHITE' if player.is_white else 'BLACK'}")
    
    # Update logic (physics runs regardless of transition)
    player.update(platforms)
    
    # Draw logic
    if transition_active:
        transition_radius += transition_speed
        
        # Draw next state to next_screen
        draw_game(next_screen, player.is_white, player, platforms)
        
        # Draw current state (old state) to screen
        screen.blit(current_screen, (0, 0))
        
        # Create shaped next state
        shaped_next = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        # Draw opaque circle on transparent background
        pygame.draw.circle(shaped_next, (255, 255, 255, 255), transition_center, transition_radius)
        
        # Blend next_screen into shaped_next using MIN blending
        # Where circle is white (255,255,255), we keep next_screen content
        # Where transparent (0,0,0,0), we keep transparent
        shaped_next.blit(next_screen, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        # Blit the shaped result onto screen
        screen.blit(shaped_next, (0,0))
        
        if transition_radius > max_radius:
            transition_active = False
            
    else:
        # Normal draw
        draw_game(screen, player.is_white, player, platforms)
        
    
    pygame.display.flip()

pygame.quit()
sys.exit()