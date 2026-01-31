import pygame
import os
from .settings import *

class ParallaxBackground:
    def __init__(self):
        # Load images
        self.output_files = {} # Cache
        
        # Helper to load and scale
        def load_asset(filename):
            # Absolute path fallback
            ARTIFACT_DIR = r"C:\Users\krish\.gemini\antigravity\brain\b14e7323-2ca0-43d5-95c8-aeac77635752"
            
            # Use high-quality generated assets
            name_map = {
                # Map far/mid/near to the generated smooth textures
                "cloud_far.png": "cloud_v2_far_1769843744997.png",
                "cloud_mid.png": "cloud_v2_mid_1769843759622.png",
                "cloud_near.png": "cloud_v2_mid_1769843759622.png" # Reuse mid for near
            }
            
            real_name = name_map.get(filename, filename)
            path = os.path.join(ARTIFACT_DIR, real_name)
            
            if not os.path.exists(path):
                # Try the other ID if not found (fallback)
                ALT_DIR = r"C:\Users\krish\.gemini\antigravity\brain\d3a64e91-0ff2-4b4e-b9ec-434f71c388e2"
                path = os.path.join(ALT_DIR, real_name)
            
            if not os.path.exists(path):
                print(f"Warning: Asset {real_name} not found")
                return None
                
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except Exception as e:
                print(f"Error loading {path}: {e}")
                return None

        # 1. Base Background: SOLID FILL (No Image) to fix Checkerboard
        self.base_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.base_bg.fill((245, 245, 245)) # Very light grey/white smoke color

        self.cloud_far = load_asset("cloud_far.png")
        if self.cloud_far: self.cloud_far.set_alpha(100) # Very faint

        self.cloud_mid = load_asset("cloud_mid.png")
        if self.cloud_mid: self.cloud_mid.set_alpha(80) # Subtle

        self.cloud_near = load_asset("cloud_near.png")
        if self.cloud_near: self.cloud_near.set_alpha(60) # Barely visible overlay
        
        # Scroll Offsets
        self.scroll_far = 0.0
        self.scroll_mid = 0.0
        self.scroll_near = 0.0
        
        # Parallax Factors
        self.factor_far = 0.1
        self.factor_mid = 0.3
        self.factor_near = 0.5
        
        # Constant Wind
        self.wind_speed = 0.5

    def update(self, velocity_x):
        """
        Update scroll positions based on player velocity + wind.
        """
        # Apply combined movement: Player Movement + Constant Wind
        delta_far = (velocity_x * self.factor_far) + (self.wind_speed * 0.2)
        delta_mid = (velocity_x * self.factor_mid) + (self.wind_speed * 0.5)
        delta_near = (velocity_x * self.factor_near) + (self.wind_speed * 1.0)
        
        self.scroll_far -= delta_far
        self.scroll_mid -= delta_mid
        self.scroll_near -= delta_near
        
        # Wrap around (Modulo width)
        self.scroll_far %= SCREEN_WIDTH
        self.scroll_mid %= SCREEN_WIDTH
        self.scroll_near %= SCREEN_WIDTH

    def draw(self, surface):
        # 1. Base Layer (Static)
        surface.blit(self.base_bg, (0, 0))
        
        # Helper to tile horizontally
        def draw_tiled(img, scroll_x):
            if img:
                # scroll_x is [0, WIDTH) due to modulo
                # We draw at scroll_x and scroll_x - WIDTH to ensure coverage as we scroll left/right
                
                # Logic:
                # If scroll is 0, we draw at 0 and -Width (invisible)
                # If scroll is 100, we draw at 100 and -1180.
                
                # Actually, standard way:
                # x1 = scroll_x
                # x2 = scroll_x - SCREEN_WIDTH
                
                # Draw at x1
                surface.blit(img, (scroll_x, 0))
                # Draw at x2 (Left side filler)
                surface.blit(img, (scroll_x - SCREEN_WIDTH, 0))

        # 2. Cloud Layers
        draw_tiled(self.cloud_far, self.scroll_far)
        draw_tiled(self.cloud_mid, self.scroll_mid)
        draw_tiled(self.cloud_near, self.scroll_near)
