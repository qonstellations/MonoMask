import pygame
import sys
import traceback
from game.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from game import run as run_game
from game.menu import MainMenu
from game.settings_manager import load_settings, save_settings

def main():
    pygame.init()
    pygame.mixer.init()
    
    # Load User Settings
    settings = load_settings()
    
    # Apply Initial Video Settings
    # Use Native Fullscreen (Manual scaling in core/menu)
    if settings["fullscreen"]:
        flags = pygame.FULLSCREEN
        screen = pygame.display.set_mode((0, 0), flags)
    else:
        flags = 0
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        
    pygame.display.set_caption("MonoMask")
    clock = pygame.time.Clock()
    
    # State: MENU, GAME
    state = "MENU"
    
    # Menu Canvas (Fixed size, scaled to screen)
    menu_canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    menu = MainMenu(menu_canvas, settings)
    
    running = True
    while running:
        if state == "MENU":
            # Event Loop for Menu
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Pass input to Menu
                action = menu.handle_input(event)
                
                if action == "new_game":
                    state = "GAME"
                    # Reset to Tutorial/Level 1
                    start_new_game = True
                elif action == "continue":
                    state = "GAME"
                    # Load from save
                    start_new_game = False
                elif action == "quit":
                    running = False
                elif action == "toggle_fullscreen":
                    # Simple Toggle Implementation
                    is_full = screen.get_flags() & pygame.FULLSCREEN
                    
                    if not is_full:
                        # Add Fullscreen flag (Native)
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        # Return to Windowed
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0)
                    
                    # Menu always draws to canvas, no update needed
            
            # Update Menu Animation (dt from 60 FPS cap)
            dt = clock.get_time() / 1000.0  # Convert ms to seconds
            menu.update(dt)
            
            # Draw Menu to Canvas
            menu.draw()
            
            # Scale Canvas to Screen
            target_size = screen.get_size()
            if target_size != (SCREEN_WIDTH, SCREEN_HEIGHT):
                pygame.transform.smoothscale(menu_canvas, target_size, screen)
            else:
                screen.blit(menu_canvas, (0, 0))
            
            pygame.display.flip()
            
            # Cap menu FPS
            clock.tick(60)
            
            # Ensure system cursor is visible in menu
            if not pygame.mouse.get_visible():
                pygame.mouse.set_visible(True)
                
        elif state == "GAME":
            # Run Game Loop (Blocking until return)
            # Pass screen AND settings
            # Run Game Loop (Blocking until return)
            # Pass screen AND settings AND start_new_game flag
            result = run_game(screen, settings, start_new_game=start_new_game)
            
            # Handle Return
            if result == "main_menu":
                state = "MENU"
                
                # Resync screen mode with settings (game might have toggled fullscreen)
                if settings["fullscreen"]:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0)
                
                # Reinit menu with canvas (not screen)
                menu = MainMenu(menu_canvas, settings) 
            elif result == "quit":
                running = False
                
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Log to file
        with open("crash_log_global.txt", "w") as f:
            traceback.print_exc(file=f)
        
        # Print to console
        traceback.print_exc()
        print("\nCRASH DETECTED! Log written to crash_log_global.txt")
        pygame.quit()
        sys.exit()