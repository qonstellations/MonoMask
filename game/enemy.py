import pygame
import math
import random
from .settings import *
from .sprites import Projectile

class MirrorRonin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.spawn_x = x  # Remember original spawn position
        self.width = 50
        self.height = 50
        self.vel_x = 0
        self.vel_y = 0
        self.speed_white = 1.5 # Flee speed (Slower, as requested)
        self.speed_black = 3.5 # Chase speed (Reduced from 6)
        self.gravity = 0.8
        self.on_ground = False
        
        # Combat State
        self.health = 5  # 2 katana hits or 5 projectile hits
        self.marked_for_deletion = False
        self.attack_timer = 0
        self.facing = 1
        self.activated = False  # Only activate AI when player gets close
        self.melee_damage_cooldown = 0  # Prevents multiple hits from same slash
        
        # Visual State
        self.anim_timer = 0.0
        
        self.pending_projectiles = []

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def take_damage(self, source_type):
        # White Mode (Peace) -> Vulnerable to Projectiles
        # Black Mode (Tension) -> Vulnerable to Melee
        if source_type == "projectile":
             # Projectiles do 1 damage (5 hits to kill)
             self.health -= 1
        elif source_type == "melee":
             # Check cooldown to prevent multi-hit from same slash
             if self.melee_damage_cooldown > 0:
                 return  # Already hit by this attack
             # Katana does 2.5 damage (2 hits to kill)
             self.health -= 2.5
             self.melee_damage_cooldown = 30  # Invincibility frames
             
        if self.health <= 0:
            self.marked_for_deletion = True

    def update(self, player, platforms, offset=(0,0)):
        self.anim_timer += 0.1
        
        # Decrement damage cooldown
        if self.melee_damage_cooldown > 0:
            self.melee_damage_cooldown -= 1
        self.on_ground = False
        
        # Basic Physics (Gravity)
        self.vel_y += self.gravity
        self.y += self.vel_y
        
        # Platform Collision (Vertical)
        my_rect = self.get_rect()
        for platform in platforms:
            if platform.get_rect().colliderect(my_rect):
                if self.vel_y > 0:
                    self.y = platform.get_rect().top - self.height
                    self.vel_y = 0
                    self.on_ground = True
        
        # AI Logic - Only activate when player gets close enough
        dist_to_player = abs(self.x - player.x)
        if not self.activated and dist_to_player < 600:
            self.activated = True
        
        if self.activated:
            if player.is_white:
                self.behavior_white(player)
            else:
                self.behavior_black(player)
        else:
            # Idle - just stand and face the direction player will come from
            self.vel_x = 0
            self.facing = -1  # Face left (toward spawn/player start)
            
        # Edge Detection (Robust - Don't fall off platforms)
        if self.on_ground and self.vel_x != 0:
            look_ahead = 25
            
            # Find current platform
            current_platform = None
            feet_y = self.y + self.height
            center_x = self.x + self.width / 2
            
            for platform in platforms:
                p_rect = platform.get_rect()
                # Check vertical alignment (with small tolerance)
                if abs(p_rect.top - feet_y) < 5:
                    # Check if we are horizontally within this platform (allowing to be on edge)
                    # Use a slightly wider check for "on platform" to catch if we are just starting to move off
                    if p_rect.left - 10 <= center_x <= p_rect.right + 10:
                        current_platform = platform
                        break
            
            if current_platform:
                p_rect = current_platform.get_rect()
                
                if self.vel_x < 0: # Moving Left
                    next_left = self.x + self.vel_x - look_ahead
                    if next_left < p_rect.left:
                        self.vel_x = 0
                        self.x = p_rect.left + look_ahead # Clamp to safe spot
                
                elif self.vel_x > 0: # Moving Right
                    next_right = self.x + self.width + self.vel_x + look_ahead
                    if next_right > p_rect.right:
                        self.vel_x = 0
                        self.x = p_rect.right - self.width - look_ahead # Clamp to safe spot
        
        # Boundary Enforcement (if set)
        if hasattr(self, 'boundary_x_min') and self.x + self.vel_x < self.boundary_x_min:
            self.vel_x = 0
            self.x = self.boundary_x_min
        if hasattr(self, 'boundary_x_max') and self.x + self.vel_x > self.boundary_x_max:
            self.vel_x = 0
            self.x = self.boundary_x_max
            
        # Apply Horizontal Move
        self.x += self.vel_x

    def behavior_white(self, player):
        # DOUBT: Evasive, Ranged
        # Move AWAY from player if close
        dist_x = self.x - player.x
        
        flee_distance = 450 # Keep a good distance
        
        if abs(dist_x) < flee_distance: 
            if dist_x > 0: # Player is to left, Run Right
                self.vel_x = self.speed_white
            else: # Player is to right, Run Left
                self.vel_x = -self.speed_white
        else:
            self.vel_x = 0
            
        # Face player always
        self.facing = -1 if dist_x > 0 else 1
        
        # Attack Logic (Shoot tracking shard)
        self.attack_timer += 1
        if self.attack_timer > 120: # 2 seconds
            self.attack_timer = 0
            # Spawn Projectile logic
            # Calculate angle to player
            cx, cy = self.x + self.width/2, self.y + self.height/2
            px, py = player.x + player.width/2, player.y + player.height/2
            angle = math.atan2(py - cy, px - cx)
            
            speed = 8
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            # Enemy projectile
            # is_white_source=True means it spawns as BLACK (Ink), which is what we want for the shadow enemy on white bg.
            # is_player_shot=False ensures it doesn't hurt the enemy.
            proj = Projectile(cx, cy, vx, vy, is_white_source=True, is_player_shot=False)
            self.pending_projectiles.append(proj)

    def behavior_black(self, player):
        # RAGE: Aggressive, Melee
        # Chase player
        dist_x = self.x - player.x
        
        if abs(dist_x) > 40: # Get close
            if dist_x > 0:
                self.vel_x = -self.speed_black
            else:
                self.vel_x = self.speed_black
        else:
            self.vel_x = 0
            # Attack!
            # For now, just contact damage?
            
        # Face player
        self.facing = -1 if dist_x > 0 else 1

    def draw(self, screen, is_white_mode, camera=None, offset=(0,0), scale=1.0):
        ox, oy = offset
        
        # Apply Camera if available
        if camera:
            # Note: MirrorRonin logic uses self.x directly usually.
            # If standardizing, we might use camera.apply_point.
            # But mostly we rely on offset here.
            # Let's verify offset vs camera usage.
            # If camera is passed, usually we use it.
            # But the 'offset' argument is already calculated from camera_offset in core.py.
            # So offset IS the camera translation basically.
            pass

        cx = (self.x - ox) + self.width / 2
        cy = (self.y - oy) + self.height / 2
        
        if is_white_mode:
            # White Mode: Shadow/Doubt (Glitchy Black Ghost)
            color = (50, 50, 50, 150) # Semi transparent
            # Draw Glitchy Rect
            off_x = random.randint(-2, 2)
            off_y = random.randint(-2, 2)
            # Create a rect surface for transparency? or just rect
            # standard rect handles alpha if surface has alpha? No, need surface.
            # Simplified:
            glitch_rect = pygame.Rect((self.x - ox) + off_x, (self.y - oy) + off_y, self.width, self.height)
            s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            s.fill(color)
            screen.blit(s, glitch_rect)
        else:
            # Black Mode: Rage/Ronin (Solid White Samurai)
            color = CREAM
            rect = pygame.Rect(self.x - ox, self.y - oy, self.width, self.height)
            pygame.draw.rect(screen, color, rect)
            # Draw Red Eyes
            eye_x = cx + (10 * self.facing)
            pygame.draw.circle(screen, (255, 50, 50), (int(eye_x), int(cy - 10)), 3)
