import pygame
import random
from .settings import *

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        """Returns a new Rect moved by the camera offset"""
        return entity.get_rect().move(self.camera.topleft)

    def apply_rect(self, rect):
        """Returns a new Rect moved by the camera offset"""
        return rect.move(self.camera.topleft)
        
    def apply_point(self, x, y):
        """Returns (x, y) moved by the camera offset"""
        return (int(x + self.camera.x), int(y + self.camera.y))

    def update(self, target):
        """Updates the camera to center on the target (player)"""
        # We want the target to be at the center of the screen
        x = -target.get_rect().centerx + int(SCREEN_WIDTH / 2)
        y = -target.get_rect().centery + int(SCREEN_HEIGHT / 2)

        # Smooth camera movement (Lerp)
        # For now, instant snap or simple check
        
        # Limit scrolling to map size? 
        # User implies "move in any direction" -> maybe infinite or very large?
        # Let's keep it bounded to the map size for sanity, but map size will be huge.
        # But here we just set the offset.
        
        # Simple lerp
        self.camera = pygame.Rect(x, y, self.width, self.height)

# Helper function to draw the game state
# Helper function to draw the game state
def draw_game(surface, is_white_mode, player, platforms, projectiles=None, effects=None, background=None, spikes=None, camera=None, enemies=None, doors=None, offset=(0,0)):
    # Background (Inverted: White Mode = White BG)
    bg_color = CREAM if is_white_mode else BLACK_MATTE
    surface.fill(bg_color)
    
    # Define an apply function that handles no-camera case safely
    def apply_rect(rect):
        if camera:
            return camera.apply_rect(rect)
        return rect
        
    if is_white_mode and background:
        background.draw(surface)
    
    # Draw platforms
    for platform in platforms:
        # We need a way to pass camera to platform.draw OR we manually apply camera here.
        # Platform logic for drawing is complex (polygons).
        # Best to pass camera to platform.draw or calculate offset points.
        # Let's update Platform.draw to accept camera, or offset the context?
        # Easier: Pass camera to draw()
        platform.draw(surface, is_white_mode, camera=camera, offset=offset)

    # Draw doors
    if doors:
        for door in doors:
            door.draw(surface, is_white_mode, camera=camera, offset=offset)

    # Draw enemies
    if enemies:
        for enemy in enemies:
            enemy.draw(surface, is_white_mode, camera=camera, offset=offset)

    # Draw spikes
    if spikes:
        for spike in spikes:
            spike.draw(surface, is_white_mode, camera=camera, offset=offset)
            
    # Draw projectiles
    if projectiles:
        for proj in projectiles:
            # Projectile draw is simple polygon/blob.
            # We can just hacking pass offset?
            # Or add draw(camera)
            proj.draw(surface, camera=camera, offset=offset)
            
    # Draw effects
    if effects:
        for eff in effects:
            eff.draw(surface, camera=camera, offset=offset)
    
    # Draw player
    player.draw(surface, camera=camera, offset=offset)

    
    # Draw UI (Fixed on screen, NO OFFSET)
    font = pygame.font.Font(None, 36)
    # Text color inverse of background
    text_color = BLACK if is_white_mode else WHITE
    
    mode_text = 'WHITE (Peace)' if is_white_mode else 'BLACK (Tension)'
    text = font.render(f"E/SHIFT: Swap | Mode: {mode_text}", True, text_color)
    surface.blit(text, (10, 10))
    
    # Optional: Visual warning for drain
    # Can't access logic state here easily without passing it, but good enough for now.
    
    info_text = font.render(f"You are the {mode_text.split()[0]} color", True, text_color)
    surface.blit(info_text, (10, 50))

    # Goal Text
    goal_font = pygame.font.Font(None, 50)
    goal_text = goal_font.render("GOAL ->", True, GRAY)
    surface.blit(goal_text, (950, 10))

def draw_distortion(surface, intensity):
    """Draws tension distortion (noise/rects) based on intensity (0.0 to 1.0)"""
    if intensity <= 0:
        return
        
    width, height = surface.get_size()
    num_glitches = int(10 * intensity)
    
    for _ in range(num_glitches):
        # Random narrow rectangles
        rect_w = random.randint(5, 50)
        rect_h = random.randint(1, 5)
        rect_x = random.randint(0, width)
        rect_y = random.randint(0, height)
        
        # Color: Either dark or light interference
        color = BLACK if random.random() > 0.5 else WHITE
        
        pygame.draw.rect(surface, color, (rect_x, rect_y, rect_w, rect_h))
        
    # Border noise
    border_thickness = int(20 * intensity)
    if border_thickness > 0:
        pygame.draw.rect(surface, BLACK, (0, 0, width, border_thickness)) # Top
        pygame.draw.rect(surface, BLACK, (0, height-border_thickness, width, border_thickness)) # Bottom
        pygame.draw.rect(surface, BLACK, (0, 0, border_thickness, height)) # Left
        pygame.draw.rect(surface, BLACK, (width-border_thickness, 0, border_thickness, height)) # Right

class CrumbleEffect:
    def __init__(self, surface):
        """Initializes the crumble effect by chopping the surface into blocks"""
        self.particles = []
        width, height = surface.get_size()
        block_size = 20 # 20x20 pixels
        
        for y in range(0, height, block_size):
            for x in range(0, width, block_size):
                # Clamp block size to surface bounds
                actual_w = min(block_size, width - x)
                actual_h = min(block_size, height - y)
                
                if actual_w <= 0 or actual_h <= 0:
                    continue
                
                # Capture block
                rect = pygame.Rect(x, y, actual_w, actual_h)
                block_surf = surface.subsurface(rect).copy()
                
                # Random velocity
                vel_x = random.uniform(-2, 2)
                vel_y = random.uniform(-1, 2) # Initial slight pop up
                
                self.particles.append({
                    'sys': block_surf,
                    'x': float(x),
                    'y': float(y),
                    'vx': vel_x,
                    'vy': vel_y
                })
        
        self.gravity = 0.5
        
    def update(self):
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += self.gravity # Apply gravity

    def draw(self, surface):
        surface.fill(CREAM) # Clear background to White (Peace default)
        for p in self.particles:
            surface.blit(p['sys'], (int(p['x']), int(p['y'])))
            
        # Draw Text on top
        width, height = surface.get_size()
        font = pygame.font.Font(None, 100)
        text = font.render("MIND FRACTURED", True, (80, 80, 80))
        text_rect = text.get_rect(center=(width//2, height//2))
        surface.blit(text, text_rect)
        
        hint_font = pygame.font.Font(None, 40)
        hint = hint_font.render("Press R to Restart", True, (150, 150, 150))
        hint_rect = hint.get_rect(center=(width//2, height//2 + 80))
        surface.blit(hint, hint_rect)
