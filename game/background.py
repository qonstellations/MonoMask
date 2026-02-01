import pygame
import os
from .settings import *
from .settings_manager import resource_path

class ParallaxBackground:
    def __init__(self):
        # Load images
        self.output_files = {} # Cache
        
        # Store original images for rescaling
        self.cloud_far_original = None
        self.cloud_mid_original = None
        self.cloud_near_original = None
        
        # Cached scaled images and their target size
        self._cached_size = (0, 0)
        self._scaled_cloud_far = None
        self._scaled_cloud_mid = None
        self._scaled_cloud_near = None
        
        # Helper to load (but NOT scale yet - we'll scale on first draw)
        def load_asset(filename):
            # Use high-quality generated assets
            name_map = {
                # Map far/mid/near to the generated smooth textures
                "cloud_far.jpeg": "cloud_far.jpeg",
                "cloud_mid.jpeg": "cloud_mid.jpeg",
                "cloud_near.jpeg": "cloud_mid.jpeg" # Reuse mid for near
            }
            
            real_name = name_map.get(filename, filename)
            path = resource_path(os.path.join("assets", real_name))
            
            if not os.path.exists(path):
                print(f"Warning: Asset {real_name} not found at {path}")
                return None
                
            try:
                img = pygame.image.load(path).convert_alpha()
                return img  # Return original, don't scale yet
            except Exception as e:
                print(f"Error loading {path}: {e}")
                return None

        # 1. Base Background: SOLID FILL (No Image) to fix Checkerboard
        self.base_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.base_bg.fill((245, 245, 245)) # Very light grey/white smoke color

        # Load originals
        self.cloud_far_original = load_asset("cloud_far.jpeg")
        self.cloud_mid_original = load_asset("cloud_mid.jpeg")
        self.cloud_near_original = load_asset("cloud_near.jpeg")
        
        # Create initial scaled versions at default resolution
        self.cloud_far = None
        self.cloud_mid = None
        self.cloud_near = None
        self._update_scaled_cache(SCREEN_WIDTH, SCREEN_HEIGHT)
        
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
    
    def _update_scaled_cache(self, target_w, target_h):
        """Pre-scale and pre-composite all cloud images. Only call when resolution changes."""
        if self._cached_size == (target_w, target_h):
            return  # Already cached at this size
        
        self._cached_size = (target_w, target_h)
        
        # Create a single pre-composited surface with all cloud layers baked in
        # This eliminates per-frame alpha blending overhead
        self._composited_clouds = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
        self._composited_clouds.fill((245, 245, 245, 255))  # Base color (opaque)
        
        # Scale and composite far layer
        if self.cloud_far_original:
            scaled = pygame.transform.smoothscale(self.cloud_far_original, (target_w, target_h))
            scaled.set_alpha(100)
            self._composited_clouds.blit(scaled, (0, 0))
        
        # Scale and composite mid layer
        if self.cloud_mid_original:
            scaled = pygame.transform.smoothscale(self.cloud_mid_original, (target_w, target_h))
            scaled.set_alpha(80)
            self._composited_clouds.blit(scaled, (0, 0))
        
        # Scale and composite near layer
        if self.cloud_near_original:
            scaled = pygame.transform.smoothscale(self.cloud_near_original, (target_w, target_h))
            scaled.set_alpha(60)
            self._composited_clouds.blit(scaled, (0, 0))
        
        # Convert to non-alpha surface for faster blitting during gameplay
        self._composited_clouds = self._composited_clouds.convert()

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

    def draw(self, surface, scale=1.0):
        # Get actual surface dimensions
        surf_w, surf_h = surface.get_size()
        
        # Update cached scaled images if resolution changed (only happens once per resolution change)
        self._update_scaled_cache(surf_w, surf_h)
        
        # Use average scroll for the composited layer (simplified parallax)
        # Or use mid layer scroll as the primary visual
        avg_scroll = (self.scroll_far + self.scroll_mid + self.scroll_near) / 3
        normalized_scroll = (avg_scroll / SCREEN_WIDTH) * surf_w
        normalized_scroll = normalized_scroll % surf_w
        
        # Draw the pre-composited clouds (just 2 blits, no alpha blending)
        surface.blit(self._composited_clouds, (normalized_scroll, 0))
        surface.blit(self._composited_clouds, (normalized_scroll - surf_w, 0))
