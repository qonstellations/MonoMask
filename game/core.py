import pygame
import sys
import random
from .settings import *
from .sprites import Player, Platform
from .utils import draw_game, draw_distortion, CrumbleEffect

def run():
    # Initialize Pygame
    pygame.init()

    # Game setup
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("MonoMask")
    clock = pygame.time.Clock()

    def reset_game():
        # Create player (starts as WHITE character)
        player = Player(100, 100)
    
        # Create platforms for "Level 1"
        platforms = [
            # 1. Start Zone (Safe)
            Platform(50, 600, 200, 30, is_neutral=True),
            
            # 2. The "White" Path (Must be White)
            Platform(300, 550, 150, 30, is_white=True),
            
            # 3. The "Black" Step (Must swap to Black)
            Platform(500, 450, 150, 30, is_white=False),
            
            # 4. Mid-air Swap Challenge
            Platform(700, 350, 150, 30, is_white=True),
            
            # 5. The "Neutral" Rest Stop
            Platform(900, 250, 100, 30, is_neutral=True),
            
            # 6. Final Leap (Requires Black)
            Platform(1100, 150, 150, 30, is_white=False),
            
            # 7. GOAL Platform (Neutral, high up)
            Platform(900, 50, 300, 30, is_neutral=True),
        ]
        return player, platforms

    player, platforms = reset_game()

    # Main game loop
    running = True
    
    # Tension Mechanics State
    tension_duration = 0.0
    overload_timer = 0.0
    game_over = False
    crumble_effect = None
    
    # Canvas for shaking
    canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    while running:
        dt = clock.tick(FPS) / 1000.0
        
        # Toggle Input Logic
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r:
                        # Restart
                        player, platforms = reset_game()
                        tension_duration = 0.0
                        overload_timer = 0.0
                        game_over = False
                        crumble_effect = None
                else:
                    if event.key == pygame.K_e or event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        player.swap_mask() # Toggle
        
        if not game_over:
            # Tension Logic based on state
            if not player.is_white: # Mask Off (Black)
                tension_duration += dt
            else: # Mask On (White)
                tension_duration -= dt * 10.0 # Fast Decay (10x faster -> 2s to clear)
                
            # Clamp tension
            tension_duration = max(0.0, tension_duration)
            
            # Calculate Intensity (0.0 to 1.0)
            # Reaches max intensity after 12 seconds + 3s hold = 15s total limits
            intensity = min(1.0, tension_duration / 12.0)
            
            # Overload Logic
            if intensity >= 1.0:
                overload_timer += dt
                if overload_timer > 3.0:
                    game_over = True
            else:
                overload_timer = 0.0
            
            # Update logic
            player.update(platforms)
            
            # Calculate Screen Shake
            shake_x = 0
            shake_y = 0
            if intensity > 0:
                shake_amp = 10 * intensity
                # Extra Violent Shake if overloading
                if overload_timer > 0:
                    shake_amp += overload_timer * 5 # Increases to +15 extra amplitude
                    
                shake_x = int((random.random() - 0.5) * 2 * shake_amp)
                shake_y = int((random.random() - 0.5) * 2 * shake_amp)
            
            # Draw Sequence
            # 1. Draw game state to canvas
            draw_game(canvas, player.is_white, player, platforms)
            
            # 2. Draw visual distortion on canvas
            draw_distortion(canvas, intensity)
            
            # 3. Blit canvas to screen with shake offset
            screen.fill(BLACK) # Clear borders exposed by shake
            screen.blit(canvas, (shake_x, shake_y))
            
        else:
            # Game Over State (Pixel Crumble)
            if crumble_effect is None:
                # Initialize crumble with the last frame
                crumble_effect = CrumbleEffect(screen)
            
            crumble_effect.update()
            crumble_effect.draw(screen)
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()
