import pygame
import math
import random
from .settings import *

class Player:
    def __init__(self, x, y):
        self.width = 50
        self.height = 50
        self.x = x
        self.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.jump_strength = 15
        self.gravity = 0.8
        self.on_ground = False
        self.is_white = True
        
        # Animation State
        self.anim_timer = 0.0
        self.pos_history = [] # For Echo effect
        
        # Fluid Transition State (0.0 = Pure Peace, 1.0 = Pure Tension)
        self.tension_value = 0.0 
        self.facing = 1 # Default facing right
        
        # Combat State
        self.shoot_cooldown = 0
        self.slash_timer = 0.0
        self.aim_angle = 0.0 # Radians
        self.shake_intensity = 0.0
        
        # Death State
        self.fell_into_void = False
        self.current_platform = None
        
        # Audio Flags
        self.just_jumped = False
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def swap_mask(self):
        """Swap between white and black character"""
        self.is_white = not self.is_white
        
    def is_neutral_collision(self, platform):
        if platform.is_neutral:
            return True
        return (self.is_white and platform.is_white) or (not self.is_white and not platform.is_white)
    
    
    def update(self, platforms, offset=(0,0), mouse_pos=None, aim_sensitivity=1.0):
        ox, oy = offset
        # Update animation timer
        self.anim_timer += 0.1
        
        # Decay shake
        self.shake_intensity *= 0.85
        if self.shake_intensity < 0.5:
            self.shake_intensity = 0
        
        # Update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        # Update slash timer
        if self.slash_timer > 0:
            self.slash_timer -= 1
        
        # Smoothly interpolate tension value
        target_tension = 0.0 if self.is_white else 1.0
        # Lerp factor (speed of transition)
        lerp_speed = 0.5  # Very fast, still smooth transition
        self.tension_value += (target_tension - self.tension_value) * lerp_speed
        
        # Update Position History (Keep last 10 frames)
        self.pos_history.append((self.x, self.y))
        if len(self.pos_history) > 10:
            self.pos_history.pop(0)

        # Mouse Aiming Logic (Screen Space to World Space)
        # Mouse Aiming Logic (Screen Space to World Space)
        # Mouse Aiming Logic (Simplified to Screen Space)
        if mouse_pos:
            mx, my = mouse_pos
        else:
            mx, my = pygame.mouse.get_pos()
        ox, oy = offset
        
        # Player Centroid in Screen Space
        # This matches exactly what is drawn on screen
        screen_cx = (self.x - ox) + self.width / 2
        screen_cy = (self.y - oy) + self.height / 2
        
        # Vector from Player to Mouse (Screen)
        dx = mx - screen_cx
        dy = my - screen_cy
        
        dist_sq = dx*dx + dy*dy
        # Only update aim if mouse is outside a small deadzone (prevents jitter)
        if dist_sq > 400: # 20 pixels squared
            target_angle = math.atan2(dy, dx)
            # Apply sensitivity via lerp - higher = more responsive
            lerp_factor = min(1.0, 0.3 * aim_sensitivity)
            # Smooth angle interpolation (handle wraparound)
            angle_diff = target_angle - self.aim_angle
            # Normalize to -pi to pi
            while angle_diff > math.pi: angle_diff -= 2 * math.pi
            while angle_diff < -math.pi: angle_diff += 2 * math.pi
            self.aim_angle += angle_diff * lerp_factor
        
        # Update Facing based on aim (Screen relative)
        if dx > 0:
            self.facing = 1
        else:
            self.facing = -1

        # Horizontal movement
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -self.speed
            # self.facing = -1 # Overridden by mouse aim
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = self.speed
            # self.facing = 1 # Overridden by mouse aim
        
        # Jump / Vertical Movement
        if DEV_NO_GRAVITY:
            # Free Flight Mode (No Gravity, Free Vertical Movement)
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.vel_y = -self.speed
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.vel_y = self.speed
            else:
                self.vel_y = 0
        else:
            # Normal Jump
            if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
                self.vel_y = -self.jump_strength
            
            # Apply gravity (same in both modes for consistent jump height)
            current_gravity = self.gravity
                
            self.vel_y += current_gravity
        
        # Cap falling speed
        if self.vel_y > 20:
            self.vel_y = 20
        
        # Move horizontally
        self.x += self.vel_x
        
        # Horizontal collision check
        player_rect = self.get_rect()
        for platform in platforms:
            # Check if this platform should collide
            # Interaction Mode: Like lands on Like OR Neutral lands on everything
            should_collide = self.is_neutral_collision(platform)
            
            if should_collide:
                platform_rect = platform.get_rect()
                if player_rect.colliderect(platform_rect):
                    # Moving right
                    if self.vel_x > 0:
                        self.x = platform_rect.left - self.width
                    # Moving left
                    elif self.vel_x < 0:
                        self.x = platform_rect.right
        
        # Move vertically
        self.y += self.vel_y
        
        # Vertical collision check
        self.on_ground = False
        player_rect = self.get_rect()
        
        for platform in platforms:
            # Check if this platform should collide
            should_collide = self.is_neutral_collision(platform)
            
            if should_collide:
                platform_rect = platform.get_rect()
                
                if player_rect.colliderect(platform_rect):
                    # Falling down (landing on platform)
                    # Falling down (landing on platform)
                    if self.vel_y > 0:
                        self.y = platform_rect.top - self.height
                        self.vel_y = 0
                        self.on_ground = True
                        self.current_platform = platform
                    # Moving up (hitting platform from below)
                    elif self.vel_y < 0:
                        self.y = platform_rect.bottom
                        self.vel_y = 0
                        
        # Stability Check: Look 2 pixels below to confirm ground
        # (Prevents flickering on_ground state due to gravity cycles)
        if not self.on_ground and self.vel_y >= 0:
             self.y += 2
             ground_check_rect = self.get_rect()
             self.y -= 2
             
             for platform in platforms:
                 if self.is_neutral_collision(platform):
                     if ground_check_rect.colliderect(platform.get_rect()):
                         self.on_ground = True
                         break
        
        # Move boundaries check REMOVED for camera
        # if self.x < 0: self.x = 0
        # if self.x + self.width > SCREEN_WIDTH: ...
        
        # Void death check
        if self.y > 3000: # Fell into the abyss
            self.fell_into_void = True
    
        
    def draw(self, screen, camera=None, offset=(0,0), scale=1.0):
        # Visual Config: Samurai Prototype (Standard Resolution)
        ox, oy = offset
        
        # Colors:
        fill_color = BLACK_MATTE if self.is_white else CREAM
        border_color = CREAM if self.is_white else BLACK_MATTE
        sword_color = GRAY
        
        # Calculate Screen Position
        # If camera exists, offset coordinates
        if camera:
            draw_pos = camera.apply_point(self.x, self.y)
            draw_x, draw_y = draw_pos
        else:
            # FIX: Use manual offset if camera is not used
            draw_x = self.x - ox
            draw_y = self.y - oy
        
        # Update center coordinates based on DRAW position
        cx = draw_x + self.width / 2
        cy = draw_y + self.height / 2
        
        t = self.anim_timer
        tension = self.tension_value
        
        # --- Helper: Shiver Effect ---
        def shiver_point(x, y, intensity):
            if intensity <= 0.01:
                return (x, y)
            # "Tiny fluctuations"
            shake_amp = 3.0 * intensity
            dx = (random.random() - 0.5) * shake_amp
            dy = (random.random() - 0.5) * shake_amp
            return (x + dx, y + dy)

        # --- BODY (Floating Robes) ---
        hover_y = math.sin(t * 0.1) * 3
        
        shoulder_y = cy - self.height * 0.25 + hover_y
        feet_y = cy + self.height * 0.4 + hover_y
        
        body_top_w = self.width * 0.3
        body_bottom_w = self.width * 0.7 
        
        # Facing direction
        dir_x = self.facing
        
        # Robe construction
        robe_pts = []
        robe_pts.append(shiver_point(cx + body_top_w/2, shoulder_y, tension)) 
        
        # Bottom Edge (with wave physics)
        num_robe_points = 20
        
        for i in range(num_robe_points + 1):
            prog = i / num_robe_points
            base_x = (cx + body_bottom_w/2) - (body_bottom_w * prog)
            
            # Physics for cloth
            ripple = math.sin(prog * 10 + t * 0.2) * 3
            # In tension, cloth gets more jagged/tattered
            tatter = abs(math.sin(prog * 15 - t * 0.3)) * 8
            
            wave_y = ripple * (1.0 - tension) + tatter * tension
            
            # Tilt based on movement
            tilt_x = -self.vel_x * 2 * prog
            
            pt_x = base_x + tilt_x
            pt_y = feet_y + wave_y
            
            robe_pts.append(shiver_point(pt_x, pt_y, tension))
            
        robe_pts.append(shiver_point(cx - body_top_w/2, shoulder_y, tension))
        
        pygame.draw.polygon(screen, fill_color, robe_pts)
        
        # --- HEAD ---
        # To make the border shiver, we draw the circle as a polygon
        head_radius = self.width * 0.22
        head_cy = shoulder_y - head_radius * 0.6
        head_cx = cx
        
        head_pts = []
        num_head_segments = 24
        for i in range(num_head_segments):
            angle = (i / num_head_segments) * 2 * math.pi
            px = head_cx + math.cos(angle) * head_radius
            py = head_cy + math.sin(angle) * head_radius
            head_pts.append(shiver_point(px, py, tension))
            
        pygame.draw.polygon(screen, fill_color, head_pts)
        
        # --- HAT (Conical) ---
        hat_w = self.width * 1.3
        hat_h = self.height * 0.18
        hat_base_y = head_cy
        
        # Main shaking of the hat object
        obj_shake_x = (random.random() - 0.5) * 5 * tension
        obj_shake_y = (random.random() - 0.5) * 2 * tension
        
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
             hat_pts.append(shiver_point(lx, ly, tension))
             
        # Top point
        hat_pts.append(shiver_point(p3[0], p3[1], tension))
        
        pygame.draw.polygon(screen, fill_color, hat_pts)
        
        # Hat Detail: Horizontal Band
        # Just a line
        band_y = hat_base_y - (hat_h * 0.3) + obj_shake_y
        band_w = hat_w * 0.6
        bx1 = cx - band_w/2 + obj_shake_x
        bx2 = cx + band_w/2 + obj_shake_x
        
        # Shiver line endpoints
        bp1 = shiver_point(bx1, band_y, tension)
        bp2 = shiver_point(bx2, band_y, tension)
        
        pygame.draw.line(screen, border_color, bp1, bp2, 2)
        
        # --- AIM RETICLE ---
        # Always draw reticle (needed since system cursor is hidden)
        aim_r = self.width * 1.0 # Radius from center
        reticle_x = cx + math.cos(self.aim_angle) * aim_r
        reticle_y = cy + math.sin(self.aim_angle) * aim_r
        
        # Ground Clamp: Visual check to keep reticle above floor
        # If we are strictly ON the ground, don't draw reticle below feet
        if self.on_ground:
             feet_level = draw_y + self.height
             if reticle_y > feet_level:
                 reticle_y = feet_level
        
        reticle_color = BLACK_MATTE if self.is_white else RED
        pygame.draw.circle(screen, reticle_color, (int(reticle_x), int(reticle_y)), 3)

        # --- KATANA ---
        if self.is_white:
            # Peace Mode: Sheathed on Hip
            hip_x = cx - (10 * dir_x)
            hip_y = shoulder_y + 10
            sheath_tip_x = hip_x - (40 * dir_x)
            sheath_tip_y = shoulder_y + 35
            
            sp1 = shiver_point(hip_x, hip_y, tension)
            sp2 = shiver_point(sheath_tip_x, sheath_tip_y, tension)
            
            pygame.draw.line(screen, sword_color, sp1, sp2, 4)
            pygame.draw.circle(screen, sword_color, (int(sp1[0]), int(sp1[1])), 4)
        else:
            # Tension Mode: Drawn or Slashing
            if self.slash_timer > 0:
                # SLASH ANIMATION
                slash_dist = 85 
                start_angle = self.aim_angle - 0.8 
                end_angle = self.aim_angle + 0.8
                
                # Draw Arc (as a set of lines)
                arc_points = []
                num_seg = 10 
                for i in range(num_seg + 1):
                     prog = i / num_seg
                     ang = start_angle + (end_angle - start_angle) * prog
                     # Jagged rage shake
                     r_offset = (random.random() - 0.5) * 5
                     ax = cx + math.cos(ang) * (slash_dist + r_offset)
                     ay = cy + math.sin(ang) * (slash_dist + r_offset)
                     arc_points.append((ax, ay))
                
                pygame.draw.lines(screen, WHITE, False, arc_points, 8) 
                
                # Draw Sword at end of swing state
                sword_x = cx + math.cos(end_angle) * 60 
                sword_y = cy + math.sin(end_angle) * 60
                pygame.draw.line(screen, sword_color, (cx, cy), (sword_x, sword_y), 4)
                
            else:
                # READY POSE (Wand-like aiming)
                # Hand position orbits slightly to match aim side
                hand_dist = 20
                hand_x = cx + math.cos(self.aim_angle) * hand_dist * 0.5 
                hand_y = shoulder_y + 15 + math.sin(self.aim_angle) * hand_dist * 0.5
                
                # Sword Tip points towards aim
                sword_len = 50
                tip_x = hand_x + math.cos(self.aim_angle) * sword_len
                tip_y = hand_y + math.sin(self.aim_angle) * sword_len
                
                sp1 = shiver_point(hand_x, hand_y, tension)
                sp2 = shiver_point(tip_x, tip_y, tension)
                
                pygame.draw.line(screen, sword_color, sp1, sp2, 3)

    def melee_attack(self):
        """Triggers a melee slash"""
        if self.shoot_cooldown > 0 or self.slash_timer > 0:
            print(f"Melee REJECT: CD={self.shoot_cooldown} Timer={self.slash_timer}")
            return None
            
        self.shoot_cooldown = 10 # Faster melee attacks
        self.slash_timer = 12 # Animation duration
        self.shake_intensity = 15.0 # Screen shake kick
        
        # Spawn Shockwaves (Multi-wavefront)
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        
        waves = []
        for i in range(8):
            # Generate from the slash arc (approx radius 85)
            # We stagger them slightly for a "thick" wave effect
            # Dist 60 to 140 covers the slash area + forward motion
            dist = 60 + (i * 12) 
            sx = cx + math.cos(self.aim_angle) * dist
            sy = cy + math.sin(self.aim_angle) * dist
            waves.append(SlashWave(sx, sy, self.aim_angle))
        
        return waves

    def shoot(self):
        """Creates a projectile moving in the facing direction"""
        if not self.is_white: # Only in Peace Mode
            return None
            
        if self.shoot_cooldown > 0:
            return None
            
        self.shoot_cooldown = 5 # 5 frames @ 60 FPS = ~12 shots/sec (Very satisfying)
        
        # Spawn from "hand" position (approximate)
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        
        # Spawn at reticle position
        aim_r = self.width * 1.0
        spawn_x = cx + math.cos(self.aim_angle) * aim_r
        spawn_y = cy + math.sin(self.aim_angle) * aim_r
        
        # Ground Clamp: Enforce shooting AT the surface if aiming down
        if self.on_ground:
             feet_level = self.y + self.height
             if spawn_y > feet_level:
                 spawn_y = feet_level
                 
        # Recalculate velocity towards the modified spawn point (Target)
        # This ensures the bullet goes where the reticle IS.
        dx = spawn_x - cx
        dy = spawn_y - cy
        shoot_angle = math.atan2(dy, dx)
        
        speed = 15
        vel_x = math.cos(shoot_angle) * speed
        vel_y = math.sin(shoot_angle) * speed
        
        # Spawn at BODY CENTER (cx, cy), not at reticle position
        # This prevents spawning inside the ground.
        return Projectile(cx, cy, vel_x, vel_y, self.is_white)

class Platform:
    def __init__(self, x, y, width, height, is_white=True, is_neutral=False, is_slider=False, is_mystical=False, slider_range=1000, is_pillar=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_white = is_white
        self.is_neutral = is_neutral
        self.is_pillar = is_pillar
        
        # Slider Logic
        self.is_slider = is_slider
        if self.is_slider:
            self.base_y = y
            self.target_y = y - slider_range # Move up by slider_range
            self.slide_speed = 3 # Speed of movement
            
        # Mystical Cave Logic
        self.is_mystical = is_mystical
        
        # Floating Island Visuals
        self.island_points = []
        self.trees = [] 
        self.grass_lines = []
        self.hatch_lines = []
        self.crystals = [] # New list for crystal shards
        
        self._generate_island_shape()
        
        if self.is_mystical:
            self._generate_crystals()
            self._generate_cave_ceiling() 
            self._generate_cave_background()
        else:
            self._generate_trees()
            self._generate_details()

    def update(self, player_on_top):
        """Update platform. Returns vertical delta if player should move with platform."""
        if not self.is_slider:
            return 0  # No movement

        dy = 0  # Track how much the platform moved
        
        if player_on_top:
            # Move Up
            if self.y > self.target_y:
                dy = -self.slide_speed
                self.y += dy
                self._shift_visuals(dy)
                
                if self.y < self.target_y: 
                    self.y = self.target_y
                    self._generate_island_shape()
        else:
            # Move Down (Return to base)
            if self.y < self.base_y:
                dy = self.slide_speed
                self.y += dy
                self._shift_visuals(dy)
                
                if self.y > self.base_y: 
                    self.y = self.base_y
        
        return dy  # Return movement delta for player sync

    def _shift_visuals(self, dy):
        # Shift all absolute coordinate structures
        self.island_points = [(p[0], p[1] + dy) for p in self.island_points]
        
        # Shift trees
        new_trees = []
        for tree_parts in self.trees:
             new_parts = []
             for branch in tree_parts:
                 b = branch.copy()
                 b['p1'] = (b['p1'][0], b['p1'][1] + dy)
                 b['p2'] = (b['p2'][0], b['p2'][1] + dy)
                 new_parts.append(b)
             new_trees.append(new_parts)
        self.trees = new_trees
        
        # Shift grass
        self.grass_lines = [((g[0][0], g[0][1] + dy), (g[1][0], g[1][1] + dy)) for g in self.grass_lines]
        
        # Shift hatches
        self.hatch_lines = [((h[0][0], h[0][1] + dy), (h[1][0], h[1][1] + dy)) for h in self.hatch_lines]
        
        # Shift crystals
        new_crystals = []
        for crystal in self.crystals:
             c = crystal.copy()
             new_pts = [(p[0], p[1] + dy) for p in c['points']]
             c['points'] = new_pts
             new_crystals.append(c)
        self.crystals = new_crystals
        
        if self.is_mystical:
            # Shift Ceiling
            self.ceiling_points = [(p[0], p[1] + dy) for p in self.ceiling_points]
            
            # Shift Stalactites
            new_stals = []
            for stal in self.stalactites:
                 s = stal.copy()
                 new_pts = [(p[0], p[1] + dy) for p in s['points']]
                 s['points'] = new_pts
                 new_stals.append(s)
            self.stalactites = new_stals
            
            # Shift Background Lines
            new_bg = []
            for line in self.cave_bg_lines:
                l = line.copy()
                l['p1'] = (l['p1'][0], l['p1'][1] + dy)
                l['p2'] = (l['p2'][0], l['p2'][1] + dy)
                new_bg.append(l)
            self.cave_bg_lines = new_bg

    def _generate_details(self):
        """Generates grass and shading details for the sketch look"""
        # 1. Grass (Top edge)
        self.grass_lines = []
        if self.width > 20:
            num_grass = int(self.width / 5)
            for i in range(num_grass):
                gx = self.x + random.randint(0, self.width)
                gh = random.randint(3, 8)
                # Random tilt
                tilt = random.randint(-2, 2)
                self.grass_lines.append(((gx, self.y), (gx + tilt, self.y - gh)))
                
        # 2. Hatching (Shading inside)
        self.hatch_lines = []
        # Diagonal lines from bottom-left to top-right coverage
        # We generally want them near the bottom/shadowed areas
        # Simple bounding box hatching for now, masked by polygon later if needed?
        # Let's just add random "scratch" lines inside the body
        num_scratches = int(self.width * self.height / 500)
        for _ in range(num_scratches):
            sx = random.uniform(self.x + 5, self.x + self.width - 5)
            sy = random.uniform(self.y + 5, self.y + self.height * 1.5) # Allow going deep
            length = random.uniform(5, 15)
            
            # constrain roughly to shape?
            # For now just random scratches
            p1 = (sx, sy)
            p2 = (sx + length, sy - length) # Diagonal /
            self.hatch_lines.append((p1, p2))

    def _generate_crystals(self):
        """Generates small white spikes for mystical platforms (x > 3000)"""
        self.crystals = []
        
        # User wants spikes from global x=3000 onwards.
        # Platform x starts at self.x.
        
        start_global_x = 3000
        
        # Step size for spikes
        # Use random steps for organic feel
        
        # Determine local start offset
        local_start = max(0, start_global_x - self.x)
        
        current_x = local_start
        while current_x < self.width - 20:
             
             global_pos = self.x + current_x
             if global_pos >= start_global_x:
                 # Generate Spike
                 cw = random.randint(10, 25) 
                 ch = random.randint(20, 45) 
                 
                 cx = self.x + current_x
                 cy = self.y # Base
                 
                 # Shape: Crystal/Spike
                 # Similar to Spike class crystal shape
                 p1 = (cx - cw/2, cy)
                 p2 = (cx + cw/2, cy)
                 p3 = (cx + random.randint(-5, 5), cy - ch) # Tip
                 
                 # Maybe add extra point for jaggedness like Spike class?
                 # Keep it simple for optimization as there might be many
                 
                 self.crystals.append({
                     'points': [p1, p2, p3],
                     'type': 'WHITE_SPIKE'
                 })
             
             current_x += random.randint(30, 60) # Random spacing

    def _generate_cave_ceiling(self):
        """Generates a ceiling mirroring the floor, with stalactites"""
        self.ceiling_points = []
        self.stalactites = []
        
        cave_height = 1000 # Match background height
        ceiling_y = self.y - cave_height
        
        # 1. Generate Ceiling Shape (Jagged, facing down)
        # Similar logic to island shape but inverted
        num_points = int(self.width / 15)
        if num_points < 3: num_points = 3
        
        center_x = self.x + self.width / 2
        
        # Track lowest point for collision
        max_y_val = -99999
        
        for i in range(num_points + 1):
            t = i / num_points
            current_x = self.x + (self.width * t) # Left to Right
            
            # Curve: Deepest in middle (closer to floor)
            # NORMALIZED: Reduced depth multiplier from 150 back to 60 (User request: not too bold)
            dist_from_center = abs(current_x - center_x) / (self.width / 2)
            base_y_offset = 60 * (1.0 - dist_from_center * 0.5)
            
            # NORMALIZED: Reduced jitter
            jitter = random.uniform(-10, 20)
            
            current_y = ceiling_y + base_y_offset + jitter
            self.ceiling_points.append((current_x, current_y))
            
            if current_y > max_y_val:
                max_y_val = current_y
                
        # Store collision Y (slightly above the lowest visual point to be forgiving?)
        # Or exactly at lowest point. solid means solid.
        self.ceiling_hit_y = max_y_val
            
        # 2. Stalactites REMOVED as per user request (No spikes)


    def _generate_cave_background(self):
        """Generates sketchy hatch lines for the cave background"""
        self.cave_bg_lines = []
        
        cave_height = 1000 # Increased by 500px as requested
        ceil_base_y = self.y - cave_height
        
        # Density of scratches
        area = self.width * cave_height
        num_scratches = int(area / 100) # 1 scratch per 100px^2 (approx)
        
        for _ in range(num_scratches):
            sx = random.uniform(self.x, self.x + self.width)
            sy = random.uniform(ceil_base_y, self.y)
            
            # Length and Angle
            length = random.uniform(5, 20)
            angle = random.uniform(0.5, 1.0) * math.pi # Mostly vertical/diagonal
            if random.random() < 0.5: angle = -angle # Cross hatch
            
            ex = sx + math.cos(angle) * length
            ey = sy + math.sin(angle) * length
            
            # Color intensity (Gray scale)
            intensity = random.randint(20, 50) # Very faint
            color = (intensity, intensity, intensity)
            
            self.cave_bg_lines.append({
                'p1': (sx, sy),
                'p2': (ex, ey),
                'color': color,
                'width': 1
            })

    def _generate_lantern_cave(self):
        """Generates a cave with hanging lanterns (700px height)"""
        self.ceiling_points = []
        self.cave_bg_lines = []
        self.lanterns = []
        
        cave_height = 700  # User specified 700px
        ceiling_y = self.y - cave_height
        
        # 1. Generate Ceiling Shape (smooth arch)
        num_points = int(self.width / 20)
        if num_points < 5: num_points = 5
        
        center_x = self.x + self.width / 2
        
        for i in range(num_points + 1):
            t = i / num_points
            current_x = self.x + (self.width * t)
            
            # Gentle arch shape
            dist_from_center = abs(current_x - center_x) / (self.width / 2)
            base_y_offset = 40 * (1.0 - dist_from_center * 0.3)
            jitter = random.uniform(-5, 10)
            
            current_y = ceiling_y + base_y_offset + jitter
            self.ceiling_points.append((current_x, current_y))
        
        self.ceiling_hit_y = max([p[1] for p in self.ceiling_points])
        
        # 2. Generate Cave Background (dark with subtle scratches)
        area = self.width * cave_height
        num_scratches = int(area / 150)
        
        for _ in range(num_scratches):
            sx = random.uniform(self.x, self.x + self.width)
            sy = random.uniform(ceiling_y, self.y)
            
            length = random.uniform(5, 15)
            angle = random.uniform(0.3, 0.9) * math.pi
            if random.random() < 0.5: angle = -angle
            
            ex = sx + math.cos(angle) * length
            ey = sy + math.sin(angle) * length
            
            intensity = random.randint(15, 35)
            color = (intensity, intensity, intensity)
            
            self.cave_bg_lines.append({
                'p1': (sx, sy),
                'p2': (ex, ey),
                'color': color,
                'width': 1
            })
        
        # 3. Generate Lanterns
        num_lanterns = max(3, int(self.width / 200))
        lantern_spacing = self.width / (num_lanterns + 1)
        
        for i in range(num_lanterns):
            lx = self.x + lantern_spacing * (i + 1)
            
            # Chain attaches to ceiling, find ceiling Y at this X
            ceil_y_at_x = ceiling_y + 50  # Approximate
            for j, pt in enumerate(self.ceiling_points):
                if j < len(self.ceiling_points) - 1:
                    if self.ceiling_points[j][0] <= lx <= self.ceiling_points[j+1][0]:
                        ceil_y_at_x = (self.ceiling_points[j][1] + self.ceiling_points[j+1][1]) / 2
                        break
            
            chain_length = random.randint(80, 150)
            ly = ceil_y_at_x + chain_length
            
            # Random glow phase for animation variation
            glow_phase = random.uniform(0, 2 * math.pi)
            
            self.lanterns.append({
                'x': lx,
                'y': ly,
                'chain_top_y': ceil_y_at_x,
                'chain_length': chain_length,
                'glow_phase': glow_phase,
                'size': random.randint(25, 35)  # Lantern body size
            })

    def _generate_trees(self):
        """Generates silhouette trees/bushes on top of the platform"""
        self.trees = []
        
        # Chance to have trees
        if random.random() < 0.3: return
        
        num_trees = random.randint(1, 3)
        for _ in range(num_trees):
            tx = random.uniform(self.x + 10, self.x + self.width - 10)
            th = random.uniform(30, 80) # Tree height
            
            # Build recursive branches
            def make_branch(x, y, h, angle, depth):
                if depth == 0: return []
                
                # End point
                ex = x + math.cos(angle) * h
                ey = y + math.sin(angle) * h
                
                branches = [{'p1': (x,y), 'p2': (ex,ey), 'w': max(1, depth)}]
                
                # Split
                if depth > 1:
                    # 2 branches
                    angle1 = angle - random.uniform(0.3, 0.8)
                    angle2 = angle + random.uniform(0.3, 0.8)
                    h_next = h * 0.7
                    
                    branches.extend(make_branch(ex, ey, h_next, angle1, depth - 1))
                    branches.extend(make_branch(ex, ey, h_next, angle2, depth - 1))
                    
                return branches
                
            # Trunk up
            tree_struct = make_branch(tx, self.y, th, -math.pi/2, 3) # Upwards
            self.trees.append(tree_struct)

    def _generate_island_shape(self):
        """Generates the jagged bottom for the floating island look"""
        self.island_points = []
        
        # Top surface (flat)
        # self.island_points.append((self.x, self.y)) # Top-Left
        # self.island_points.append((self.x + self.width, self.y)) # Top-Right
        
        # Bottom jagged edge
        # We start from Top-Right and go down/left back to Top-Left
        
        # Right Side (tapering down)
        depth = self.height * 1.5 # How deep the island goes
        if depth < 20: depth = 20
        
        # Bottom Points
        num_points = int(self.width / 15) # Density of jags
        if num_points < 3: num_points = 3
        
        center_x = self.x + self.width / 2
        
        # Generate points along the bottom
        for i in range(num_points + 1):
            # 0 to 1
            t = i / num_points
            
            # X coordinate: goes from Right (x+w) to Left (x)
            current_x = (self.x + self.width) - (self.width * t)
            
            # Y coordinate: parabolic curve + noise
            # Curve: Deepest in middle
            dist_from_center = abs(current_x - center_x) / (self.width / 2) # 0 (center) to 1 (edge)
            base_y = self.y + depth * (1.0 - dist_from_center * 0.5) 
            
            # Noise
            jitter_y = random.uniform(-5, 15)
            # Taper edges
            if dist_from_center > 0.8:
                base_y = self.y + random.uniform(5, 15) # Near top
            
            current_y = base_y + jitter_y
            self.island_points.append((current_x, current_y))
            
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def check_spike_collision(self, player_rect):
        """Checks if player rect collides with any mystical floor spikes"""
        if not self.is_mystical: return False
        
        # Optimization: Fast bounding box check first?
        # Platform rect check is already done probably.
        
        for crystal in self.crystals:
            # Construct rect from points
            # points are [(x,y), (x,y), (x,y)]
            xs = [p[0] for p in crystal['points']]
            ys = [p[1] for p in crystal['points']]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            spike_rect = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
            
            # Simple interaction check
            # Shrink player rect slightly for fairness?
            hit_rect = player_rect.inflate(-15, -10) # Smaller hit box
            
            if spike_rect.colliderect(hit_rect):
                return True
        return False

    def draw(self, screen, is_white_mode, camera=None, offset=(0,0)):
        # SKETCH STYLE DRAWING
        
        # Visibility check
        should_be_active = self.is_neutral or (self.is_white and is_white_mode) or (not self.is_white and not is_white_mode)
        
        # For Sketch style:
        # If NOT active, maybe we draw it faint/dotted? 
        # Or stick to invisible. Let's stick to invisible for clarity.
        if not should_be_active:
            return

        # Colors
        # Neutral platforms: Always GRAY (safe zones)
        # Regular platforms: Black on White (Peace) or White on Black (Tension)
        ox, oy = offset
        rect = self.get_rect()
        rect.x -= ox
        rect.y -= oy
        
        if self.is_mystical:
            # Mystical Cave Theme
            ink_color = (80, 70, 100) # Dark Slate
            fill_color = (20, 15, 25) # Very Dark Cave Rock
        elif self.is_neutral:
            ink_color = (100, 100, 100)  # Dark gray outline
            fill_color = (180, 180, 180)  # Light gray fill
        elif is_white_mode:
            ink_color = BLACK_MATTE
            fill_color = CREAM # Paper color
        else:
            ink_color = CREAM
            fill_color = BLACK_MATTE
            
        # Helper for camera apply
        def apply_pt(pt):
            if camera: return camera.apply_point(pt[0], pt[1])
            # FIX: Apply manual offset
            return (pt[0] - ox, pt[1] - oy)
            
        # 1. Define Visual Polygon (Top + Jagged Bottom)
        # Top-Left, Top-Right
        tl = (self.x, self.y)
        tr = (self.x + self.width, self.y)
        
        # Combine into closed loop
        raw_poly = [tl, tr] + self.island_points
        
        # Apply Camera
        poly_points = [apply_pt(p) for p in raw_poly]
        
        if self.is_mystical:
            # Mystical Cave Theme
            ink_color = (80, 70, 100) # Dark Slate
            fill_color = (20, 15, 25) # Very Dark Cave Rock
        elif self.is_neutral:
            ink_color = (100, 100, 100)  # Dark gray outline
            fill_color = (180, 180, 180)  # Light gray fill
        elif is_white_mode:
            ink_color = BLACK_MATTE
            fill_color = CREAM # Paper color
        else:
            ink_color = CREAM
            fill_color = BLACK_MATTE
            
        # Helper for camera apply
        def apply_pt(pt):
            if camera: return camera.apply_point(pt[0], pt[1])
            # FIX: Apply manual offset
            return (pt[0] - ox, pt[1] - oy)
            
        # 1. Define Visual Polygon (Top + Jagged Bottom)
        # Top-Left, Top-Right
        tl = (self.x, self.y)
        tr = (self.x + self.width, self.y)
        
        # Combine into closed loop
        raw_poly = [tl, tr] + self.island_points
        
        # Apply Camera
        poly_points = [apply_pt(p) for p in raw_poly]
        
        # 2. Draw Fill (Opaque background)
        pygame.draw.polygon(screen, fill_color, poly_points)
        
        # 3. Draw Outline (Ink)
        pygame.draw.polygon(screen, ink_color, poly_points, 3) 
        
        # 4. Mystical Elements
        if self.is_mystical:
            time_val = pygame.time.get_ticks() / 1000.0
            
            # --- CEILING & BACKDROP ---
            # 1. Background Fill (Darkness behind)
            
            # Let's draw the "Cave Wall" (Background)
            # A dark rect covering the whole area? NO - SKETCH STYLE
            # Draw faint background lines
            for line in self.cave_bg_lines:
                p1 = apply_pt(line['p1'])
                p2 = apply_pt(line['p2'])
                l_col = line['color']
                pygame.draw.line(screen, l_col, p1, p2, 1)
            
            # Border lines REMOVED as per user request ("dont make a rectangle outline")
            
            
            # Render Ceiling (Restored as per user request "similar to platform sketch")
            # We want a rock mass hanging from the top.
            # Ceiling points are the "bottom edge" of the ceiling mass.
            # We need to close the loop by going up to the "roof" of the world (or some upper bound).
            
            # Use 'ceil_base_y' from generation logic (y - cave_height)
            # Actually, _generate_cave_background uses logic: ceil_base_y = self.y - cave_height
            # But we don't store cave_height on self. Let's assume consistent?
            # Better: Find min Y of ceiling points and go up from there?
            # Or just use the min Y from points as the "top"?
            # Wait, ceiling_points ARE the jagged edge.
            # To look like a platform, it needs thickness upwards.
            
            if hasattr(self, 'ceiling_points') and self.ceiling_points:
                # Find the 'flat top' of this hanging rock (visually above visible area)
                # Let's say 100px thick above the highest point
                # FIX: Use 50px buffer above min_y
                min_y = min([p[1] for p in self.ceiling_points])
                roof_y = min_y - 50 
                
                # Create closed polygon:
                # 1. Roof Top-Left
                # 2. Roof Top-Right
                # 3. Ceiling Points (Right to Left reversed? No, points are L->R)
                # So: TL -> TR -> Points(R->L) -> Close
                
                c_tl = (self.x, roof_y)
                c_tr = (self.x + self.width, roof_y)
                
                # Reverse points to trace back to left
                jagged_bottom = list(reversed(self.ceiling_points))
                
                raw_ceil_poly = [c_tl, c_tr] + jagged_bottom
                ceil_poly_pts = [apply_pt(p) for p in raw_ceil_poly]
                
                pygame.draw.polygon(screen, fill_color, ceil_poly_pts)
                pygame.draw.polygon(screen, ink_color, ceil_poly_pts, 3)
            
            # Stalactites REMOVED
            
            # Draw Floor Spikes (Dynamic Colors)
            for crystal in self.crystals:
                 pts = [apply_pt(p) for p in crystal['points']]
                 
                 # Logic: If White Mode -> Black Spikes (Contrast)
                 #        If Black Mode -> White Spikes (Contrast)
                 if is_white_mode:
                     s_fill = (0, 0, 0)
                     s_outline = (255, 255, 255) # Optional: White outline for style? Or just Black
                     # User said "make thode spikes black in color".
                     # Let's keep it simple: Black fill, maybe no outline or White outline?
                     # Let's do Black Fill, White Outline for visibility against potentially grey elements
                     pygame.draw.polygon(screen, (0, 0, 0), pts) 
                     pygame.draw.polygon(screen, (255, 255, 255), pts, 1)
                 else:
                     # Black Mode / Dark Cave -> White Spikes
                     pygame.draw.polygon(screen, (255, 255, 255), pts)
                     pygame.draw.polygon(screen, (0, 0, 0), pts, 2)
            
            return # Skip trees/grass for mystical
            
        # 4. Draw Details (Grass)
        for g in self.grass_lines:
            gp1 = apply_pt(g[0])
            gp2 = apply_pt(g[1])
            pygame.draw.line(screen, ink_color, gp1, gp2, 2)
            
        # 5. Draw Texture (Hatching)
        # Only draw if inside polygon? simple check: y > self.y
        for h in self.hatch_lines:
            hp1 = apply_pt(h[0])
            hp2 = apply_pt(h[1])
            # Simple Y check to keep "under" surface
            if h[0][1] >= self.y and h[1][1] >= self.y:
                pygame.draw.line(screen, ink_color, hp1, hp2, 1)

        # 6. Draw Trees
        # Trees should match ink color
        for tree_parts in self.trees:
            for branch in tree_parts:
                p1 = apply_pt(branch['p1'])
                p2 = apply_pt(branch['p2'])
                # Tree style: varying width
                w = branch['w']
                pygame.draw.line(screen, ink_color, p1, p2, w)
                
                # Leaf/Bush details at ends?
                if 'w' in branch and branch['w'] <= 1:
                     # Draw little sketchy circle/leaves
                     pygame.draw.circle(screen, ink_color, (int(p2[0]), int(p2[1])), 2)

class Spike:
    def __init__(self, x, y, width=30, height=30, is_white=True, is_neutral=False, is_mystical=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_white = is_white
        self.is_neutral = is_neutral
        self.is_mystical = is_mystical
        
        # Generate shape
        self.points = []
        if self.is_mystical:
            self._generate_crystal_shape()
        else:
            self._generate_shape()
        
    def _generate_shape(self):
        # ... standard triangle ...
        p1 = (self.x, self.y + self.height) # Bottom Left
        p2 = (self.x + self.width, self.y + self.height) # Bottom Right
        p3 = (self.x + self.width / 2, self.y) # Top Center (Tip)
        self.points = [p1, p3, p2]

    def _generate_crystal_shape(self):
        # Irregular crystal shard
        # Base points
        p1 = (self.x, self.y + self.height)
        p2 = (self.x + self.width, self.y + self.height)
        
        # Tip point (randomized x, fixed top y)
        tip_x = self.x + self.width * random.uniform(0.3, 0.7)
        tip_y = self.y
        p3 = (tip_x, tip_y)
        
        # Optional extra side point for jaggedness
        if random.random() < 0.5:
            # 4-point crystal
            mid_x = self.x + self.width * (0.8 if tip_x < self.x + self.width/2 else 0.2)
            mid_y = self.y + self.height * random.uniform(0.3, 0.7)
            self.points = [p1, (mid_x, mid_y), p3, p2] if mid_x < tip_x else [p1, p3, (mid_x, mid_y), p2]
            # Ensure proper winding order? Simple sort by angle or just hardcode loop
            # Let's stick to simple triangle for robustness or just 3 points but randomized
            self.points = [p1, p3, p2] # Keeping it simple for now to avoid convex issues
            
            # Widen the base or shift tip more?
            # Actually, `Platform` crystals are just triangles often.
            # Let's make it taller/thinner or slanted?
            # No, user wants "same design".
            pass
        
        self.points = [p1, p3, p2]
        
    def get_rect(self):
        return pygame.Rect(self.x + 5, self.y + 10, self.width - 10, self.height - 10)
        
    def draw(self, screen, is_white_mode, camera=None, offset=(0,0), scale=1.0):
        # Similar visibility rules to Platforms
        should_be_active = self.is_neutral or (self.is_white and is_white_mode) or (not self.is_white and not is_white_mode)
        
        if not should_be_active:
            return
            
        draw_pts = self.points
        if camera:
            draw_pts = [camera.apply_point(p[0], p[1]) for p in self.points]
        else:
            ox, oy = offset
            draw_pts = [(p[0] - ox, p[1] - oy) for p in self.points]
            
        # Color Logic
        if self.is_mystical:
            # Crystal Style: High Contrast
            # If White Mode (Peace) -> Black Spikes
            # If Black Mode (Tension) -> White Spikes
            if is_white_mode:
                pygame.draw.polygon(screen, (0, 0, 0), draw_pts) # Black fill
                pygame.draw.polygon(screen, (255, 255, 255), draw_pts, 1) # White outline
            else:
                pygame.draw.polygon(screen, (255, 255, 255), draw_pts) # White fill
                pygame.draw.polygon(screen, (0, 0, 0), draw_pts, 2) # Black outline
        else:
            # Standard Red Spikes
            color = RED if is_white_mode else (255, 50, 50)
            pygame.draw.polygon(screen, color, draw_pts)

class Projectile:
    def __init__(self, x, y, vx, vy, is_white_source=True, is_player_shot=True):
        self.x = x
        self.y = y
        self.start_x = x  # Track starting position
        self.start_y = y
        self.vx = vx
        self.vy = vy
        self.radius = 5
        # Color logic:
        # If source is White (Peace), Projectile is Dark (Black Matte)
        # If source is Black (Tension), Projectile is Light (Cream)
        self.is_white_source = is_white_source # Determines color/affinity
        self.is_player_shot = is_player_shot # Determines who it hurts
        
        # Color: If source is White(Peace), projectile is Black (Ink).
        # If source is Black(Tension), projectile is White (Light).
        self.color = BLACK_MATTE if is_white_source else CREAM
        
        self.marked_for_deletion = False
        self.timer = 0
        
        # Max travel distance (prevents sniping from across the map)
        self.max_distance = 400  # Pixels
        
        # Dynamic shape seed
        self.seed = random.random() * 100
    
    def update(self, offset=(0,0)):
        self.x += self.vx
        self.y += self.vy
        self.timer += 0.2
        
        # Check distance traveled
        dx = self.x - self.start_x
        dy = self.y - self.start_y
        distance = (dx * dx + dy * dy) ** 0.5
        if distance > self.max_distance:
            self.marked_for_deletion = True
            return
        
        ox, oy = offset
        # Bounds check (Relative to Camera View)
        # If it goes off-screen, delete it.
        # Screen view is from ox to ox + SCREEN_WIDTH
        if self.x < ox - 100 or self.x > ox + SCREEN_WIDTH + 100:
            self.marked_for_deletion = True
            
    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def draw(self, screen, camera=None, offset=(0,0), scale=1.0):
        # Generate points in WORLD SPACE first, then apply camera/offset
        num_points = 20
        points = []
        
        # Center in World Space
        cx, cy = self.x, self.y
        
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            
            # Wobble logic
            wobble = math.sin(angle * 5 + self.timer) * 3
            wobble += math.cos(angle * 3 - self.timer * 2) * 2
            
            r = self.radius + wobble
            
            px = cx + math.cos(angle) * r
            py = cy + math.sin(angle) * r
            points.append((px, py))
            
        # Apply transformation ONLY ONCE
        if camera:
            points = [camera.apply_point(p[0], p[1]) for p in points]
        else:
            ox, oy = offset
            points = [(p[0] - ox, p[1] - oy) for p in points]
            
        pygame.draw.polygon(screen, self.color, points)
        
        # Trail/Tail particles?
        # Maybe complex for now, let's stick to the blob.

class SplatBlast:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.particles = []
        self.timer = 0
        self.lifetime = 30 # Longer lifetime for fluid feel
        
        # 1. Main Splash Burst (Large blobs)
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 12)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(4, 10)
            self.particles.append({
                'x': 0, 
                'y': 0, 
                'vx': vx, 
                'vy': vy, 
                'size': size,
                'decay': 0.9, # Slow decay
                'drag': 0.85  # Fast drag (fluid stopping)
            })
            
        # 2. High Velocity Droplets (Tiny, fast)
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(10, 20)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(2, 4)
            self.particles.append({
                'x': 0, 
                'y': 0, 
                'vx': vx, 
                'vy': vy, 
                'size': size,
                'decay': 0.95, 
                'drag': 0.9
            })
            
    def update(self):
        self.timer += 1
        
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            
            # Physics
            p['vx'] *= p['drag']
            p['vy'] *= p['drag']
            
            # Gravity? Maybe slight gravity for "drip"
            p['vy'] += 0.5
            
            # Shrink
            p['size'] *= p['decay']
            
    def draw(self, screen, camera=None, offset=(0,0), scale=1.0):
        ox, oy = offset
        for p in self.particles:
            if p['size'] < 1:
                continue
            
            # World Space P
            wx = self.x + p['x']
            wy = self.y + p['y']
            
            if camera:
                draw_x, draw_y = camera.apply_point(wx, wy)
            else:
                draw_x = wx - ox
                draw_y = wy - oy
            
            # Draw circle or maybe a small polygon for jaggedness?
            # Circle is "fluid" enough
            pygame.draw.circle(screen, self.color, (int(draw_x), int(draw_y)), int(p['size']))

class SlashWave:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 12  # Reduced range
        self.lifetime = 8  # Shorter range
        self.timer = 0
        
    def update(self):
        self.timer += 1
        # Move forward
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        
    def draw(self, screen, camera=None, offset=(0,0), scale=1.0):
        # Draw a "Distorted Wavefront" (Semi-circle with noise)
        ox, oy = offset
        
        # 1. Define curvature
        # The wave is 'bowed' out.
        # We model this as an arc of a circle centered BEHIND the wave front.
        radius = 60 
        
        # Center of the imaginary circle (World Space)
        back_dist = radius
        ccx = self.x - math.cos(self.angle) * back_dist
        ccy = self.y - math.sin(self.angle) * back_dist
        
        # 2. Generate arc points
        points = []
        num_pts = 20
        arc_angle = 1.2 # Radian spread (+/-)
        
        for i in range(num_pts + 1):
            # Normalized t from -1 to 1
            t = (i / num_pts) * 2 - 1 
            
            # Current angle on the arc
            a = self.angle + t * arc_angle
            
            # Distortion (The "Wave" effect)
            # Sine wave perturbation
            freq = 8.0
            amp = 4.0
            # Phase shift by time for motion along the wave
            noise = math.sin(t * freq + self.timer * 0.5) * amp
            
            # Apply secondary jitter?
            jitter = (random.random() - 0.5) * 3
            
            current_r = radius + noise + jitter
            
            px = ccx + math.cos(a) * current_r
            py = ccy + math.sin(a) * current_r
            
            points.append((px, py))
        if len(points) > 1:
            if camera:
                points = [camera.apply_point(p[0], p[1]) for p in points]
            else:
                points = [(p[0] - ox, p[1] - oy) for p in points]
                
            pygame.draw.lines(screen, WHITE, False, points, 3)

    def check_collision(self, rect):
        # precise collision is hard for an arc, simplified to circle overlap
        # Slash is approx 40-60 pixels in front.
        # Let's say it's a point at (x,y) with radius 30?
        slash_rect = pygame.Rect(self.x - 15, self.y - 15, 30, 30)  # Smaller hitbox
        return slash_rect.colliderect(rect)


class BlackHole:
    """Level exit portal - a wavy flowing dotted sphere effect"""
    def __init__(self, x, y, radius=60, target_level=2):
        self.x = x
        self.y = y
        self.radius = radius
        self.target_level = target_level
        
        # Animation state
        self.rotation = 0.0
        self.pulse_timer = 0.0
        self.active = True
        
        # Create wavy sphere lines - horizontal latitude lines that flow
        self.sphere_lines = []
        num_latitudes = 24  # Number of horizontal rings (increased for density)
        dots_per_line = 80  # Dots per ring (increased for density)
        
        for lat in range(num_latitudes):
            lat_angle = (lat / num_latitudes) * math.pi  # 0 to PI (top to bottom)
            ring_radius = math.sin(lat_angle) * self.radius  # Varies with latitude
            y_offset = math.cos(lat_angle) * self.radius * 0.6  # Y position for 3D effect
            
            line_dots = []
            for dot in range(dots_per_line):
                dot_angle = (dot / dots_per_line) * math.pi * 2
                # Add wave offset that varies per latitude for flowing effect
                wave_offset = random.uniform(0, math.pi * 2)
                wave_amplitude = random.uniform(3, 8)
                line_dots.append({
                    'base_angle': dot_angle,
                    'wave_offset': wave_offset,
                    'wave_amp': wave_amplitude,
                    'size': random.randint(1, 3)
                })
            
            self.sphere_lines.append({
                'ring_radius': ring_radius,
                'y_offset': y_offset,
                'dots': line_dots,
                'flow_speed': random.uniform(0.3, 0.8)
            })
        
    def get_rect(self):
        return pygame.Rect(self.x - self.radius//2, self.y - self.radius//2, self.radius, self.radius)
    
    def update(self, dt):
        self.rotation += dt * 2  # Rotate animation
        self.pulse_timer += dt
        
    def check_collision(self, player_rect):
        """Check if player entered the black hole"""
        # Use center-to-center distance for circular collision
        player_center = player_rect.center
        dx = player_center[0] - self.x
        dy = player_center[1] - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        return distance < self.radius * 0.6  # Core collision
    
    def draw(self, screen, is_white_mode, camera=None, offset=(0, 0)):
        ox, oy = offset
        
        # Calculate screen position
        screen_x = int(self.x - ox)
        screen_y = int(self.y - oy)
        
        # Pulsing effect
        pulse = 0.9 + 0.1 * math.sin(self.pulse_timer * 3)
        
        # Dot color based on mode
        if is_white_mode:
            dot_color = (30, 30, 40)  # Dark dots on light background
            core_color = (10, 10, 15)
        else:
            dot_color = (220, 220, 230)  # Light dots on dark background
            core_color = (5, 5, 10)
        
        # Draw wavy sphere lines
        for line in self.sphere_lines:
            ring_r = line['ring_radius'] * pulse
            y_off = line['y_offset'] * pulse
            
            for dot_data in line['dots']:
                # Calculate angle with rotation and wave
                wave = math.sin(self.pulse_timer * line['flow_speed'] * 5 + dot_data['wave_offset']) * dot_data['wave_amp']
                current_angle = dot_data['base_angle'] + self.rotation
                
                # 3D projection - dots move along the latitude ring
                dot_x = screen_x + int(math.cos(current_angle) * ring_r)
                dot_y = screen_y + int(y_off + math.sin(current_angle * 3 + self.pulse_timer * 2) * wave)
                
                # Only draw dots on the "front" half of the sphere (simple depth check)
                depth = math.sin(current_angle)
                if depth > -0.3:  # Show front-ish dots
                    # Size varies with depth for 3D effect
                    size = max(1, int(dot_data['size'] * (0.5 + depth * 0.5)))
                    # Alpha/brightness varies with depth
                    if is_white_mode:
                        brightness = max(20, int(40 * (0.3 + depth * 0.7)))
                        color = (brightness, brightness, brightness + 10)
                    else:
                        brightness = max(150, int(255 * (0.5 + depth * 0.5)))
                        color = (brightness, brightness, min(255, brightness + 20))
                    
                    pygame.draw.circle(screen, color, (dot_x, dot_y), size)
        
        # Draw dark center core
        core_radius = int(self.radius * 0.3 * pulse)
        pygame.draw.circle(screen, core_color, (screen_x, screen_y), core_radius)
        
        # Draw subtle glow at center
        glow_radius = max(3, int(5 * pulse))
        if is_white_mode:
            pygame.draw.circle(screen, (60, 50, 80), (screen_x, screen_y), glow_radius)
        else:
            pygame.draw.circle(screen, (180, 170, 200), (screen_x, screen_y), glow_radius)


class Shard:
    """A triangular shard from the player's shattered body"""
    def __init__(self, x, y, color, speed_mult=1.0):
        self.x = x
        self.y = y
        self.color = color
        
        # Random velocity (explode outwards)
        angle = random.uniform(0, 6.28)
        speed = random.uniform(2, 8) * speed_mult
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(2, 5) # Initial upward pop
        
        self.gravity = 0.5
        
        # Triangle shape offsets
        size = random.randint(5, 12)
        self.points = [
            (random.uniform(-size, size), random.uniform(-size, size)),
            (random.uniform(-size, size), random.uniform(-size, size)),
            (random.uniform(-size, size), random.uniform(-size, size))
        ]
        
        self.angle = 0
        self.rot_speed = random.uniform(-0.2, 0.2)
        
        self.alpha = 255
        self.fade_speed = random.uniform(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.angle += self.rot_speed
        
        self.alpha -= self.fade_speed
        if self.alpha < 0: self.alpha = 0

    def draw(self, screen, camera=None, offset=(0,0)):
        if self.alpha <= 0: return

        ox, oy = offset
        if camera:
            cx, cy = camera.apply_point(self.x, self.y)
        else:
            cx, cy = self.x - ox, self.y - oy

        # Rotate points
        rotated_pts = []
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        
        for px, py in self.points:
            # Rotate
            rx = px * cos_a - py * sin_a
            ry = px * sin_a + py * cos_a
            # Translate
            rotated_pts.append((cx + rx, cy + ry))
            
        # Draw with alpha manually since direct polygon alpha is tricky
        # Just drawing solid for now as per previous plan, maybe implement temp surface if fading looks bad
        # Re-using the temp surface approach from previous attempt logic
        
        min_x = min([p[0] for p in rotated_pts])
        max_x = max([p[0] for p in rotated_pts])
        min_y = min([p[1] for p in rotated_pts])
        max_y = max([p[1] for p in rotated_pts])
        w = int(max_x - min_x) + 2
        h = int(max_y - min_y) + 2
        
        if w > 0 and h > 0:
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            surf_pts = [(p[0] - min_x, p[1] - min_y) for p in rotated_pts]
            color_with_alpha = (*self.color, int(self.alpha))
            pygame.draw.polygon(s, color_with_alpha, surf_pts)
            screen.blit(s, (min_x, min_y))

