import pygame
import os
from .settings import *

class ParallaxBackground:
    def __init__(self):
        # Load images
        self.output_files = {} # Cache
        
        # Helper to load and scale
        def load_asset(filename):
            # Resolve path relative to this file (__file__ is inside game/)
            # Go up one level to get to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ARTIFACT_DIR = os.path.join(base_dir, "assets")
            
            # Use high-quality generated assets
            name_map = {
                # Map far/mid/near to the generated smooth textures
                "cloud_far.jpeg": "cloud_far.jpeg",
                "cloud_mid.jpeg": "cloud_mid.jpeg",
                "cloud_near.jpeg": "cloud_mid.jpeg" # Reuse mid for near
            }
            
            real_name = name_map.get(filename, filename)
            path = os.path.join(ARTIFACT_DIR, real_name)
            
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

        self.cloud_far = load_asset("cloud_far.jpeg")
        if self.cloud_far: self.cloud_far.set_alpha(100) # Very faint

        self.cloud_mid = load_asset("cloud_mid.jpeg")
        if self.cloud_mid: self.cloud_mid.set_alpha(80) # Subtle

        self.cloud_near = load_asset("cloud_near.jpeg")
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
        # 1. Parallax Component (Only if moving forward)
        para_vel = velocity_x if velocity_x > 0 else 0
        
        # 2. Wind Component (Always active)
        wind = self.wind_speed
        
        # Apply combined movement
        delta_far = (para_vel * self.factor_far) + (wind * 0.2)
        delta_mid = (para_vel * self.factor_mid) + (wind * 0.5)
        delta_near = (para_vel * self.factor_near) + (wind * 1.0)
        
        self.scroll_far -= delta_far
        self.scroll_mid -= delta_mid
        self.scroll_near -= delta_near
        
        # Wrap around (Modulo width)
        self.scroll_far %= SCREEN_WIDTH
        self.scroll_mid %= SCREEN_WIDTH
        self.scroll_near %= SCREEN_WIDTH

    def draw(self, surface):
        # Get actual surface dimensions
        surf_w, surf_h = surface.get_size()
        
        # 1. Base Layer (Fill entire surface)
        surface.fill((245, 245, 245)) # Very light grey/white smoke color
        
        # Helper to tile horizontally with dynamic scaling
        def draw_tiled(img, scroll_x):
            if img:
                # Scale image to surface size if needed
                img_w, img_h = img.get_size()
                if img_w != surf_w or img_h != surf_h:
                    scaled_img = pygame.transform.smoothscale(img, (surf_w, surf_h))
                else:
                    scaled_img = img
                
                # Normalize scroll to new width
                normalized_scroll = (scroll_x / SCREEN_WIDTH) * surf_w
                normalized_scroll = normalized_scroll % surf_w
                
                # Draw at x1
                surface.blit(scaled_img, (normalized_scroll, 0))
                # Draw at x2 (Left side filler)
                surface.blit(scaled_img, (normalized_scroll - surf_w, 0))

        # 2. Cloud Layers
        draw_tiled(self.cloud_far, self.scroll_far)
        draw_tiled(self.cloud_mid, self.scroll_mid)
        draw_tiled(self.cloud_near, self.scroll_near)
