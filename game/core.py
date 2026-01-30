import pygame
import sys
from .settings import *
from .sprites import Player, Platform
from .utils import draw_game

def run():
    # Initialize Pygame
    pygame.init()

    # Game setup
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("MonoMask")
    clock = pygame.time.Clock()

    # Create player (starts as WHITE character)
    player = Player(100, 100)

    # Create platforms for "Level 1"
    # Logic: Like lands on Like.
    # Neutral lands on both.
    platforms = [
        # 1. Start Zone (Safe)
        Platform(50, 600, 200, 30, is_neutral=True),
        
        # 2. The "White" Path (Must be White)
        Platform(300, 550, 150, 30, is_white=True),
        
        # 3. The "Black" Step (Must swap to Black)
        Platform(500, 450, 150, 30, is_white=False),
        
        # 4. Mid-air Swap Challenge
        # Jump from Black -> Land on White
        Platform(700, 350, 150, 30, is_white=True),
        
        # 5. The "Neutral" Rest Stop
        Platform(900, 250, 100, 30, is_neutral=True),
        
        # 6. Final Leap (Requires Black)
        Platform(1100, 150, 150, 30, is_white=False),
        
        # 7. GOAL Platform (Neutral, high up)
        Platform(900, 50, 300, 30, is_neutral=True),
    ]

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
