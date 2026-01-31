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
        
        # Combat State
        self.shoot_cooldown = 0
        self.slash_timer = 0.0
        self.aim_angle = 0.0 # Radians
        self.shake_intensity = 0.0
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def swap_mask(self):
        """Swap between white and black character"""
        self.is_white = not self.is_white
        
    def is_neutral_collision(self, platform):
        if platform.is_neutral:
            return True
        return (self.is_white and platform.is_white) or (not self.is_white and not platform.is_white)
    
    
    def update(self, platforms, offset=(0,0)):
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
        # Mouse Aiming Logic (Simplified to Screen Space)
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
            self.aim_angle = math.atan2(dy, dx)
        
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
        
        # Jump
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
                    if self.vel_y > 0:
                        self.y = platform_rect.top - self.height
                        self.vel_y = 0
                        self.on_ground = True
                    # Moving up (hitting platform from below)
                    elif self.vel_y < 0:
                        self.y = platform_rect.bottom
                        self.vel_y = 0
        
        # Move boundaries check REMOVED for camera
        # if self.x < 0: self.x = 0
        # if self.x + self.width > SCREEN_WIDTH: ...
        
        # Respawn if WAY too low
        if self.y > 3000: # Arbitrary "abyss" limit
             self.y = 100
             self.vel_y = 0
    
        
    def draw(self, screen, camera=None, offset=(0,0)):
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
    def __init__(self, x, y, width, height, is_white=True, is_neutral=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_white = is_white
        self.is_neutral = is_neutral
        
        # Floating Island Visuals
        self.island_points = []
        self.trees = [] 
        self.grass_lines = []
        self.hatch_lines = []
        
        self._generate_island_shape()
        self._generate_trees()
        self._generate_details()

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
        
        if self.is_neutral:
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
        
        # 2. Draw Fill (Opaque background to hide things behind)
        pygame.draw.polygon(screen, fill_color, poly_points)
        
        # 3. Draw Outline (Ink)
        pygame.draw.polygon(screen, ink_color, poly_points, 3) # Thickish pencil line
        
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
    def __init__(self, x, y, width=30, height=30, is_white=True, is_neutral=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_white = is_white
        self.is_neutral = is_neutral
        
        # Generate jagged spike triangle shape
        self.points = []
        self._generate_shape()
        
    def _generate_shape(self):
        # Assumes pointing UP for now
        # Base is at y + height
        # Tip is at y
        
        # Simple Triangle
        p1 = (self.x, self.y + self.height) # Bottom Left
        p2 = (self.x + self.width, self.y + self.height) # Bottom Right
        p3 = (self.x + self.width / 2, self.y) # Top Center (Tip)
        
        self.points = [p1, p3, p2]
        
    def get_rect(self):
        # Hitbox (smaller than visual)
        return pygame.Rect(self.x + 5, self.y + 10, self.width - 10, self.height - 10)
        
    def draw(self, screen, is_white_mode, camera=None, offset=(0,0)):
        # Similar visibility rules to Platforms
        should_be_active = self.is_neutral or (self.is_white and is_white_mode) or (not self.is_white and not is_white_mode)
        
        if not should_be_active:
            return
            
        # Color Logic
        color = RED if is_white_mode else (255, 50, 50) # Red warning color
        
        draw_pts = self.points
        if camera:
            draw_pts = [camera.apply_point(p[0], p[1]) for p in self.points]
        else:
            # FIX: Apply manual offset
            ox, oy = offset
            draw_pts = [(p[0] - ox, p[1] - oy) for p in self.points]
            
        pygame.draw.polygon(screen, color, draw_pts)

class Projectile:
    def __init__(self, x, y, vx, vy, is_white_source=True, is_player_shot=True):
        self.x = x
        self.y = y
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
        
        # Dynamic shape seed
        self.seed = random.random() * 100
    
    def update(self, offset=(0,0)):
        self.x += self.vx
        self.y += self.vy
        self.timer += 0.2
        
        ox, oy = offset
        # Bounds check (Relative to Camera View)
        # If it goes off-screen, delete it.
        # Screen view is from ox to ox + SCREEN_WIDTH
        if self.x < ox - 100 or self.x > ox + SCREEN_WIDTH + 100:
            self.marked_for_deletion = True
            
    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def draw(self, screen, camera=None, offset=(0,0)):
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
            
    def draw(self, screen, camera=None, offset=(0,0)):
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
        self.speed = 22
        self.lifetime = 12 # Quick dissipate
        self.timer = 0
        
    def update(self):
        self.timer += 1
        # Move forward
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        
    def draw(self, screen, camera=None, offset=(0,0)):
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
        slash_rect = pygame.Rect(self.x - 20, self.y - 20, 40, 40)
        return slash_rect.colliderect(rect)

