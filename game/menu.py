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
        
        # Cloud Ripple Animation
        self.anim_time = 0.0
        self.cloud_ripples = []
        # Pre-generate ripple spawn points
        for _ in range(8):
            self.cloud_ripples.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'phase': random.uniform(0, math.pi * 2),
                'speed': random.uniform(0.5, 1.5),
                'size': random.randint(100, 300)
            })
        
    def update(self, dt=1/60):
        """Update animation timers"""
        self.anim_time += dt
        
    def draw_cloud_ripples(self):
        """Draw animated white cloud ripples in the background"""
        for ripple in self.cloud_ripples:
            # Calculate pulsing size
            pulse = math.sin(self.anim_time * ripple['speed'] + ripple['phase'])
            current_size = ripple['size'] + pulse * 50
            
            # Calculate alpha (fading in and out)
            alpha = int(15 + 10 * math.sin(self.anim_time * 0.5 + ripple['phase']))
            
            # Create a surface for the soft glow
            glow_size = int(current_size * 2)
            if glow_size > 0:
                glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                
                # Draw multiple concentric circles for soft glow effect
                center = glow_size // 2
                for i in range(3):
                    radius = int(current_size * (1.0 - i * 0.3))
                    circle_alpha = alpha // (i + 1)
                    if radius > 0 and circle_alpha > 0:
                        pygame.draw.circle(glow_surf, (255, 255, 255, circle_alpha), (center, center), radius)
                
                # Blit with offset
                self.screen.blit(glow_surf, (int(ripple['x'] - center), int(ripple['y'] - center)))
        
    def draw(self):
        self.screen.fill((0, 0, 0)) # Pure Black Background
        
        # Draw cloud ripples first (behind everything)
        self.draw_cloud_ripples()
        
        if self.state == "MAIN":
            self.draw_list(self.options_main, "MONOMASK")
        elif self.state == "OPTIONS":
            self.draw_options_menu()

    def draw_list(self, options, title):
        # Draw Title
        title_surf = self.title_font.render(title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 3))
        self.screen.blit(title_surf, title_rect)
        
        start_y = self.height // 2 + 50
        gap = 70
        
        self.button_rects = [] 
        
        for i, option in enumerate(options):
            is_selected = (i == self.selected_index)
            self.draw_button(option, start_y + i * gap, is_selected, i)

    def draw_options_menu(self):
        # Draw Title
        title_surf = self.title_font.render("OPTIONS", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 3))
        self.screen.blit(title_surf, title_rect)
        
        start_y = self.height // 2 + 50
        gap = 80 # Larger gap for UI elements
        
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
