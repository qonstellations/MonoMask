import pygame
from .settings import *

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
        current_gravity = self.gravity
        if not self.is_white:
            current_gravity *= 1.3 # Heavier feel
            
        self.vel_y += current_gravity
        
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
