import pygame
import sys
import math
import random
from .settings import *
from .settings_manager import save_settings

class MainMenu:
    def __init__(self, screen, settings):
        # Ensure font module is active
        if not pygame.font.get_init():
            pygame.font.init()
            
        self.screen = screen
        self.settings = settings
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.state = "MAIN" # MAIN, OPTIONS
        
        # Fonts
        try:
            self.title_font = pygame.font.SysFont("Impact", 120)
            self.menu_font = pygame.font.SysFont("Menlo", 40)
            self.ui_font = pygame.font.SysFont("Menlo", 30) # Smaller for values
        except:
            self.title_font = pygame.font.SysFont(None, 120)
            self.menu_font = pygame.font.SysFont(None, 40)
            self.ui_font = pygame.font.SysFont(None, 30)
            
        # Menu Options
        self.options_main = ["NEW GAME", "CONTINUE", "OPTIONS", "QUIT"]
        self.options_sub = ["FULLSCREEN", "RETICLE SENSITIVITY", "BACK"]
        
        self.selected_index = 0
        self.button_rects = []
        
        # Input Debounce (prevents super fast slider movement)
        self.input_timer = 0
        
        # Animated Dotted Background
        self.anim_time = 0.0
        self.dot_grid = []
        self.dot_spacing = 8  # Pixels between dots
        self.scroll_x = 0.0
        self.scroll_y = 0.0
        
        # Pre-generate dot grid with noise values
        cols = SCREEN_WIDTH // self.dot_spacing + 4
        rows = SCREEN_HEIGHT // self.dot_spacing + 4
        for y in range(rows):
            row = []
            for x in range(cols):
                # Create pseudo-random noise pattern
                noise = self._noise(x * 0.15, y * 0.15)
                row.append({
                    'base_size': 1 + noise * 3,  # Size 1-4
                    'phase': random.uniform(0, math.pi * 2),
                    'brightness': 80 + int(noise * 175)  # 80-255
                })
            self.dot_grid.append(row)
        
    def _noise(self, x, y):
        """Simple noise function for procedural generation"""
        # Combination of sin waves for organic look
        n = math.sin(x * 1.5) * math.cos(y * 1.3) * 0.5
        n += math.sin(x * 0.7 + y * 0.5) * 0.3
        n += math.sin(x * 2.1 - y * 1.8) * 0.2
        return (n + 1) / 2  # Normalize to 0-1
        
    def update(self, dt=1/60):
        """Update animation timers"""
        self.anim_time += dt
        # No scrolling - dots stay in place
        
    def draw_dotted_background(self):
        """Draw animated dotted halftone background"""
        for row_idx, row in enumerate(self.dot_grid):
            for col_idx, dot in enumerate(row):
                # Calculate fixed screen position (no scroll offset)
                x = col_idx * self.dot_spacing
                y = row_idx * self.dot_spacing
                
                # Skip if off screen
                if x < -10 or x > self.width + 10 or y < -10 or y > self.height + 10:
                    continue
                
                # Animate size with time (pulsing in place)
                pulse = math.sin(self.anim_time * 0.8 + dot['phase']) * 0.3 + 0.7
                size = max(1, int(dot['base_size'] * pulse))
                
                # Draw dot
                brightness = dot['brightness']
                color = (brightness, brightness, brightness)
                pygame.draw.circle(self.screen, color, (x, y), size)
    
    def draw_blur_panel(self, rect, alpha=180):
        """Draw a dark semi-transparent panel with soft edges"""
        # Create panel surface
        panel = pygame.Surface((rect.width + 40, rect.height + 40), pygame.SRCALPHA)
        
        # Draw multiple rectangles for soft edge effect
        for i in range(5):
            expand = (5 - i) * 8
            panel_alpha = alpha // (6 - i)
            inner_rect = pygame.Rect(20 - expand//2, 20 - expand//2, 
                                     rect.width + expand, rect.height + expand)
            pygame.draw.rect(panel, (0, 0, 0, panel_alpha), inner_rect, border_radius=15)
        
        # Core solid panel
        core_rect = pygame.Rect(20, 20, rect.width, rect.height)
        pygame.draw.rect(panel, (0, 0, 0, alpha), core_rect, border_radius=10)
        
        # Blit panel centered on the rect
        self.screen.blit(panel, (rect.x - 20, rect.y - 20))
        
    def draw(self):
        self.screen.fill((0, 0, 0)) # Pure Black Background
        
        # Draw dotted background first
        self.draw_dotted_background()
        
        if self.state == "MAIN":
            self.draw_list(self.options_main, "MONOMASK")
        elif self.state == "OPTIONS":
            self.draw_options_menu()

    def draw_list(self, options, title):
        # Calculate positions first
        title_surf = self.title_font.render(title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 3))
        
        start_y = self.height // 2 + 50
        gap = 70
        
        # Calculate buttons area rect
        buttons_height = len(options) * gap
        buttons_rect = pygame.Rect(self.width // 2 - 200, start_y - 30, 
                                   400, buttons_height + 20)
        
        # Draw blur panels behind UI elements
        self.draw_blur_panel(title_rect.inflate(60, 30))
        self.draw_blur_panel(buttons_rect)
        
        # Draw Title
        self.screen.blit(title_surf, title_rect)
        
        self.button_rects = [] 
        
        for i, option in enumerate(options):
            is_selected = (i == self.selected_index)
            self.draw_button(option, start_y + i * gap, is_selected, i)

    def draw_options_menu(self):
        # Calculate positions first
        title_surf = self.title_font.render("OPTIONS", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 3))
        
        start_y = self.height // 2 + 50
        gap = 80 # Larger gap for UI elements
        
        # Calculate options area rect (wider for sliders)
        options_height = len(self.options_sub) * gap
        options_rect = pygame.Rect(self.width // 2 - 350, start_y - 30, 
                                   700, options_height + 20)
        
        # Draw blur panels
        self.draw_blur_panel(title_rect.inflate(60, 30))
        self.draw_blur_panel(options_rect)
        
        # Draw Title
        self.screen.blit(title_surf, title_rect)
        
        self.button_rects = []
        
        for i, option in enumerate(self.options_sub):
            is_selected = (i == self.selected_index)
            
            # Base Button Text
            y_pos = start_y + i * gap
            self.draw_button(option, y_pos, is_selected, i)
            
            # --- Draw Extra UI Elements ---
            
            # Fullscreen Toggle
            if option == "FULLSCREEN":
                # Toggle Switch UI
                switch_w = 60
                switch_h = 30
                switch_x = self.width // 2 + 280
                switch_y = y_pos - switch_h // 2
                
                switch_rect = pygame.Rect(switch_x, switch_y, switch_w, switch_h)
                
                # Draw Background Capsule
                if self.settings["fullscreen"]:
                    # ON State: Filled White
                    pygame.draw.rect(self.screen, (255, 255, 255), switch_rect, border_radius=15)
                    # Knob: Black, Right Side
                    pygame.draw.circle(self.screen, (0, 0, 0), (switch_x + switch_w - 15, switch_y + 15), 12)
                else:
                    # OFF State: Outline White
                    pygame.draw.rect(self.screen, (255, 255, 255), switch_rect, 2, border_radius=15)
                    # Knob: White, Left Side
                    pygame.draw.circle(self.screen, (255, 255, 255), (switch_x + 15, switch_y + 15), 10)
            
            # Sensitivity Slider
            elif option == "RETICLE SENSITIVITY":
                # Draw Slider Bar
                slider_width = 200
                slider_x = self.width // 2 + 280
                slider_y = y_pos
                
                # Background Line
                pygame.draw.rect(self.screen, (100, 100, 100), (slider_x, slider_y, slider_width, 4))
                
                # Handle Knob
                # Range 0.2 to 3.0
                val = self.settings["sensitivity"]
                normalized = (val - 0.2) / (3.0 - 0.2)
                knob_x = slider_x + float(normalized * slider_width)
                
                pygame.draw.circle(self.screen, (255, 255, 255), (int(knob_x), int(slider_y + 2)), 10)
                
                # Draw Value Text
                val_surf = self.ui_font.render(f"{val:.1f}", True, (255, 255, 255))
                self.screen.blit(val_surf, (slider_x + slider_width + 20, slider_y - 10))

    def draw_button(self, text, y_pos, is_selected, index):
        text_color = (255, 255, 255)
        bg_color = None
                 
        if is_selected:
            text_color = (0, 0, 0)
            bg_color = (255, 255, 255)
            
        # Render Text
        surf = self.menu_font.render(text, True, text_color)
        rect = surf.get_rect(center=(self.width // 2, y_pos))
        
        # Draw Background if selected
        if bg_color:
            bg_rect = rect.inflate(40, 20)
            pygame.draw.rect(self.screen, bg_color, bg_rect)
        
        # Draw Text
        self.screen.blit(surf, rect)
        
        # Store rect
        self.button_rects.append({'rect': rect, 'action': text, 'index': index})
        
        # Grey out CONTINUE
        if text == "CONTINUE":
             s = pygame.Surface(rect.size, pygame.SRCALPHA)
             s.fill((0,0,0, 180))
             self.screen.blit(s, rect.topleft)

    def handle_input(self, event):
        options = self.options_main if self.state == "MAIN" else self.options_sub
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_index = (self.selected_index - 1) % len(options)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.selected_index = (self.selected_index + 1) % len(options)
                
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                # Trigger Action
                action = options[self.selected_index]
                return self.process_action(action)
            
            elif event.key == pygame.K_ESCAPE:
                if self.state == "OPTIONS":
                    self.state = "MAIN"
                    self.selected_index = 0
            
            # Slider Logic
            if self.state == "OPTIONS":
                current_opt = self.options_sub[self.selected_index]
                if current_opt == "RETICLE SENSITIVITY":
                    if event.key == pygame.K_LEFT:
                        self.settings["sensitivity"] = max(0.2, self.settings["sensitivity"] - 0.1)
                        save_settings(self.settings)
                    elif event.key == pygame.K_RIGHT:
                        self.settings["sensitivity"] = min(3.0, self.settings["sensitivity"] + 0.1)
                        save_settings(self.settings)
                        
        # Mouse input disabled - keyboard only

        return None
        
    def process_action(self, action):
        if action == "NEW GAME":
            return "new_game"
        elif action == "CONTINUE":
            return None 
        elif action == "OPTIONS":
            self.state = "OPTIONS"
            self.selected_index = 0
            return None
        elif action == "QUIT":
            return "quit"
            
        elif action == "FULLSCREEN":
            # Toggle Setting
            self.settings["fullscreen"] = not self.settings["fullscreen"]
            save_settings(self.settings)
            return "toggle_fullscreen"
            
        elif action == "BACK":
            self.state = "MAIN"
            self.selected_index = 0
            return None
            
        return None
