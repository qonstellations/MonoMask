import pygame
from .settings import *

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
    
    info_text = font.render(f"White/Black: Lands on SAME color | GOLD: Neutral (Lands on BOTH)", True, (255, 255, 0))
    surface.blit(info_text, (10, 50))

    # Goal Text
    goal_font = pygame.font.Font(None, 50)
    goal_text = goal_font.render("GOAL ->", True, GOLD)
    surface.blit(goal_text, (950, 10))
