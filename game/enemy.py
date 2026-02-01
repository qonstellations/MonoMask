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
            
        # Edge Detection (Don't fall off platforms)
        if self.on_ground and self.vel_x != 0:
            # Look ahead
            look_ahead = 20 # Look a bit ahead of the center
            if self.vel_x < 0:
                check_x = self.x + self.vel_x
            else:
                check_x = self.x + self.width + self.vel_x
                
            # Check point below
            check_point = (check_x, self.y + self.height + 2)
            
            ground_found = False
            for platform in platforms:
                if platform.get_rect().collidepoint(check_point):
                    ground_found = True
                    break
            
            if not ground_found:
                self.vel_x = 0
        
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



class Minion:
    """Small square enemy that chases the player. Dies in 1 hit."""



class ShadowSelf:
    """The Inner Demon - A massive corrupted reflection of the protagonist.
    4x larger with cracked hat, glaring red eyes, tattered robes, and burning flames."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.spawn_x = x
        self.width = 200   # 4x protagonist (50 * 4)
        self.height = 200
        self.vel_x = 0
        self.vel_y = 0
        self.speed_white = 1.0  # Slower but menacing
        self.speed_black = 2.5  # Chase speed
        self.gravity = 0.8
        self.on_ground = False
        
        # Combat State
        self.health = 200  # Increased from 100 for better durability
        self.marked_for_deletion = False
        self.is_dead = False # Compatible with check
        self.attack_timer = 0
        self.spawn_timer = 0 # For spawning minions
        self.facing = 1
        self.activated = False
        self.melee_damage_cooldown = 0
        self.newly_spawned_minions = [] # Buffer for core loop to pick up
        
        # Visual State
        self.anim_timer = 0.0
        self.rage_intensity = 1.0  # Always in rage mode
        
        # Flame particles
        self.flame_particles = []
        for _ in range(30):
            self.flame_particles.append({
                'x': random.uniform(-self.width/2, self.width/2),
                'y': random.uniform(-self.height*0.3, self.height*0.5),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-3, -1),
                'life': random.uniform(0.5, 1.0),
                'size': random.uniform(8, 20)
            })
        
        # Ink drip particles
        self.ink_drips = []
        for _ in range(15):
            self.ink_drips.append({
                'x': random.uniform(-self.width/2, self.width/2),
                'y': self.height * 0.4,
                'vy': random.uniform(1, 3),
                'life': random.uniform(0.5, 1.0),
                'size': random.uniform(3, 8)
            })
        
        self.pending_projectiles = []

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def take_damage(self, source_type):
        damage = 0
        if isinstance(source_type, int) or isinstance(source_type, float):
            damage = source_type
        elif source_type == "projectile":
            damage = 5 # Increased from 1
        elif source_type == "melee":
            if self.melee_damage_cooldown > 0:
                return
            damage = 10 # Increased from 2.5
            self.melee_damage_cooldown = 30
            
        self.health -= damage
        print(f"ShadowSelf took {damage} dmg. Health: {self.health}") # Debug
        
        if self.health <= 0:
            self.health = 0
            self.marked_for_deletion = True
            self.is_dead = True
            
        if self.health <= 0:
            self.marked_for_deletion = True

    def update(self, player, platforms, offset=(0,0)):
        self.anim_timer += 0.1
        
        # Decrement damage cooldown
        if self.melee_damage_cooldown > 0:
            self.melee_damage_cooldown -= 1
        self.on_ground = False
        
        # Update flame particles
        for p in self.flame_particles:
            p['y'] += p['vy']
            p['x'] += p['vx'] + math.sin(self.anim_timer * 0.5 + p['x']) * 0.5
            p['life'] -= 0.02
            if p['life'] <= 0:
                # Reset particle
                p['x'] = random.uniform(-self.width/2, self.width/2)
                p['y'] = random.uniform(-self.height*0.2, self.height*0.5)
                p['vx'] = random.uniform(-1, 1)
                p['vy'] = random.uniform(-3, -1)
                p['life'] = random.uniform(0.5, 1.0)
                p['vx'] = random.uniform(-1, 1)
                p['vy'] = random.uniform(-3, -1)
                p['life'] = random.uniform(0.5, 1.0)
                p['size'] = random.uniform(8, 20)
                
        # Spawn Logic Removed (User Request)
        
        # Update ink drips
        for d in self.ink_drips:
            d['y'] += d['vy']
            d['life'] -= 0.01
            if d['life'] <= 0 or d['y'] > self.height * 0.8:
                d['x'] = random.uniform(-self.width/2, self.width/2)
                d['y'] = self.height * 0.3
                d['vy'] = random.uniform(1, 3)
                d['life'] = random.uniform(0.5, 1.0)
                d['size'] = random.uniform(3, 8)
        
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
        if not self.activated and dist_to_player < 800:
            self.activated = True
        
        if self.activated:
            if player.is_white:
                self.behavior_white(player)
            else:
                self.behavior_black(player)
        else:
            self.vel_x = 0
            self.facing = -1
            
        # Edge Detection
        if self.on_ground and self.vel_x != 0:
            if self.vel_x < 0:
                check_x = self.x + self.vel_x
            else:
                check_x = self.x + self.width + self.vel_x
                
            check_point = (check_x, self.y + self.height + 2)
            
            ground_found = False
            for platform in platforms:
                if platform.get_rect().collidepoint(check_point):
                    ground_found = True
                    break
            
            if not ground_found:
                self.vel_x = 0
            
        self.x += self.vel_x

    def behavior_white(self, player):
        # Slow menacing approach + ranged attacks
        dist_x = self.x - player.x
        
        if abs(dist_x) > 300:
            if dist_x > 0:
                self.vel_x = -self.speed_white
            else:
                self.vel_x = self.speed_white
        else:
            self.vel_x = 0
            
        self.facing = -1 if dist_x > 0 else 1
        
        # Attack Logic - faster than regular enemy
        self.attack_timer += 1
        if self.attack_timer > 90:  # 1.5 seconds
            self.attack_timer = 0
            cx, cy = self.x + self.width/2, self.y + self.height/2
            px, py = player.x + player.width/2, player.y + player.height/2
            angle = math.atan2(py - cy, px - cx)
            
            # Fire 3 projectiles in a spread (SHURIKENS)
            for spread in [-0.2, 0, 0.2]:
                a = angle + spread
                speed = 12
                vx = math.cos(a) * speed
                vy = math.sin(a) * speed
                proj = Projectile(cx, cy, vx, vy, is_white_source=True, is_player_shot=False, visual_type="SHURIKEN")
                self.pending_projectiles.append(proj)

    def behavior_black(self, player):
        # Aggressive chase
        dist_x = self.x - player.x
        
        if abs(dist_x) > 60:
            if dist_x > 0:
                self.vel_x = -self.speed_black
            else:
                self.vel_x = self.speed_black
        else:
            self.vel_x = 0
            
        self.facing = -1 if dist_x > 0 else 1

    def draw(self, screen, is_white_mode, camera=None, offset=(0,0), scale=1.0):
        ox, oy = offset
        
        cx = (self.x - ox) + self.width / 2
        cy = (self.y - oy) + self.height / 2
        
        t = self.anim_timer
        
        # Colors based on player mode (inverted for contrast)
        if is_white_mode:
            fill_color = (20, 20, 20)  # Dark body
            border_color = (240, 240, 230)  # Cream border
            flame_color = (40, 40, 40)  # Black flames
            flame_glow = (60, 60, 60)
        else:
            fill_color = (240, 240, 230)  # Cream body
            border_color = (20, 20, 20)  # Dark border
            flame_color = (255, 255, 250)  # White flames
            flame_glow = (200, 200, 190)
        
        eye_color = (255, 50, 50)  # Red eye always
        
        # --- Helper: Shiver Effect (like protagonist) ---
        def shiver_point(x, y, intensity=0.8):
            shake_amp = 4.0 * intensity
            dx = (random.random() - 0.5) * shake_amp
            dy = (random.random() - 0.5) * shake_amp
            return (x + dx, y + dy)
        
        # --- DRAW BURNING FLAMES (Behind character) ---
        for p in self.flame_particles:
            px = cx + p['x']
            py = cy + p['y'] - self.height * 0.2
            size = p['size'] * p['life']
            
            # Draw flame shape (triangle pointing up)
            flame_pts = [
                (px, py - size),
                (px - size * 0.6, py + size * 0.5),
                (px + size * 0.6, py + size * 0.5)
            ]
            flame_pts = [shiver_point(pt[0], pt[1], 0.5) for pt in flame_pts]
            pygame.draw.polygon(screen, flame_color, flame_pts)
            # Inner glow
            inner_pts = [
                (px, py - size * 0.6),
                (px - size * 0.3, py + size * 0.3),
                (px + size * 0.3, py + size * 0.3)
            ]
            pygame.draw.polygon(screen, flame_glow, inner_pts)
        
        # --- BODY (Floating Robes - EXACTLY like protagonist) ---
        hover_y = math.sin(t * 0.1) * 5
        
        shoulder_y = cy - self.height * 0.25 + hover_y
        feet_y = cy + self.height * 0.4 + hover_y
        
        body_top_w = self.width * 0.3
        body_bottom_w = self.width * 0.7
        
        # Robe construction (same as protagonist)
        robe_pts = []
        robe_pts.append(shiver_point(cx + body_top_w/2, shoulder_y))
        
        # Bottom Edge with wave physics (exactly like protagonist)
        num_robe_points = 20
        for i in range(num_robe_points + 1):
            prog = i / num_robe_points
            base_x = (cx + body_bottom_w/2) - (body_bottom_w * prog)
            
            # Physics for cloth
            ripple = math.sin(prog * 10 + t * 0.2) * 5
            tatter = abs(math.sin(prog * 15 - t * 0.3)) * 10
            wave_y = ripple * 0.5 + tatter * 0.5
            
            # Tilt based on movement
            tilt_x = -self.vel_x * 2 * prog
            
            pt_x = base_x + tilt_x
            pt_y = feet_y + wave_y
            
            robe_pts.append(shiver_point(pt_x, pt_y))
        
        robe_pts.append(shiver_point(cx - body_top_w/2, shoulder_y))
        
        pygame.draw.polygon(screen, fill_color, robe_pts)
        
        # --- HEAD (same as protagonist) ---
        head_radius = self.width * 0.22
        head_cy = shoulder_y - head_radius * 0.6
        head_cx = cx
        
        head_pts = []
        num_head_segments = 24
        for i in range(num_head_segments):
            angle = (i / num_head_segments) * 2 * math.pi
            px = head_cx + math.cos(angle) * head_radius
            py = head_cy + math.sin(angle) * head_radius
            head_pts.append(shiver_point(px, py))
        
        pygame.draw.polygon(screen, fill_color, head_pts)
        
        # --- HAT (Conical - same as protagonist) ---
        hat_w = self.width * 1.3
        hat_h = self.height * 0.18
        hat_base_y = head_cy
        
        # Object shake
        obj_shake_x = (random.random() - 0.5) * 5
        obj_shake_y = (random.random() - 0.5) * 2
        
        # Define base points
        p1 = (cx - hat_w/2 + obj_shake_x, hat_base_y + obj_shake_y)
        p2 = (cx + hat_w/2 + obj_shake_x, hat_base_y + obj_shake_y)
        p3 = (cx + obj_shake_x, hat_base_y - hat_h + obj_shake_y)
        
        hat_pts = []
        # Bottom edge (subdivided)
        steps = 10
        for i in range(steps + 1):
            t_val = i / steps
            lx = p1[0] + (p2[0] - p1[0]) * t_val
            ly = p1[1] + (p2[1] - p1[1]) * t_val
            hat_pts.append(shiver_point(lx, ly))
        
        # Top point
        hat_pts.append(shiver_point(p3[0], p3[1]))
        
        pygame.draw.polygon(screen, fill_color, hat_pts)
        
        # Hat Detail: Horizontal Band (same as protagonist)
        band_y = hat_base_y - (hat_h * 0.3) + obj_shake_y
        band_w = hat_w * 0.6
        bx1 = cx - band_w/2 + obj_shake_x
        bx2 = cx + band_w/2 + obj_shake_x
        
        bp1 = shiver_point(bx1, band_y)
        bp2 = shiver_point(bx2, band_y)
        
        pygame.draw.line(screen, border_color, bp1, bp2, 3)
        
        # --- SINGLE RED EYE (Centered, glowing) ---
        eye_cx = head_cx + obj_shake_x
        eye_cy = head_cy - head_radius * 0.1 + obj_shake_y
        eye_radius = 20  # Large single eye
        
        # Outer glow
        for i in range(5):
            glow_r = eye_radius + 15 - i * 3
            glow_alpha = min(255, 60 + i * 40)
            pygame.draw.circle(screen, (glow_alpha, 10, 10), 
                             (int(eye_cx), int(eye_cy)), glow_r)
        
        # Main eye (bright red)
        pygame.draw.circle(screen, eye_color, (int(eye_cx), int(eye_cy)), eye_radius)
        
        # Inner hot core
        pygame.draw.circle(screen, (255, 150, 80), (int(eye_cx), int(eye_cy)), int(eye_radius * 0.5))
        
        # White glint
        pygame.draw.circle(screen, (255, 255, 255), (int(eye_cx - 5), int(eye_cy - 5)), 4)
        
        # --- MORE FLAMES (In front, for layering) ---
        for p in self.flame_particles[:15]:
            px = cx + p['x'] * 0.7
            py = cy + p['y'] * 0.4 - self.height * 0.1
            size = p['size'] * p['life'] * 0.6
            
            if size > 3:
                flame_pts = [
                    (px, py - size),
                    (px - size * 0.5, py + size * 0.4),
                    (px + size * 0.5, py + size * 0.4)
                ]
                flame_pts = [shiver_point(pt[0], pt[1], 0.3) for pt in flame_pts]
                pygame.draw.polygon(screen, flame_color, flame_pts)

