import pygame
import sys
import random
from .settings import *
from .sprites import Player, Platform, SplatBlast, Spike
from .utils import draw_game, draw_distortion, CrumbleEffect, Camera
from .background import ParallaxBackground

def run():
    # Initialize Pygame
    pygame.init()

    # Game setup
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("MonoMask")
    clock = pygame.time.Clock()
    
    # Initialize Background
    background = ParallaxBackground()

    def reset_game():
        # Create player (starts as WHITE character)
        player = Player(100, 100)
    
        # Fixed Level Layout (Based on Reference Image approximation)
        # Sequence of platforms going Right and Up
        
        map_width = 3000
        map_height = 2000
        
        # Base floor level reference (Screen Height is ~768 usually, but map is 2000)
        # Let's keep action near the middle-bottom 
        base_y = map_height - 300
        
        # FULL Reference Map Layout - Every platform from the image
        # Map is wide (6000px) to capture the long horizontal flow
        
        map_width = 6000
        map_height = 2000
        base_y = map_height - 200
        
        platforms_data = [
             {'x': 50, 'y': base_y, 'w': 500, 'type': 'neutral'},
             {'x': 700, 'y': base_y-100, 'w': 100, 'type': 'white'},
             {'x': 900, 'y': base_y-200, 'w': 100, 'type': 'black'},
             {'x': 1100, 'y': base_y-290, 'w': 1000, 'type': 'neutral'},
             {'x': 2200, 'y': base_y-400, 'w': 200, 'type': 'white'},
             {'x': 2400, 'y': base_y-500, 'w': 200, 'type': 'black'},
             {'x': 2600, 'y': base_y-290, 'w': 200, 'type': 'black'},
        ]
        
        platforms = []
        spikes = []
        
        # Player Start
        player.x = 150
        player.y = base_y - 100
        
        for p_data in platforms_data:
            is_white = (p_data['type'] == 'white')
            is_neutral = (p_data['type'] == 'neutral')
            # If black, both are false
            if p_data['type'] == 'black':
                is_white = False
                is_neutral = False
                
            plat = Platform(p_data['x'], p_data['y'], p_data['w'], 30, is_white=is_white, is_neutral=is_neutral)
            platforms.append(plat)
            
            # NO SPIKES GENERATED
            
        
        projectiles = []
        effects = []
        return player, platforms, spikes, projectiles, effects

    player, platforms, spikes, projectiles, effects = reset_game()

    # Main game loop
    running = True
    
    # Tension Mechanics State
    tension_duration = 0.0
    overload_timer = 0.0
    game_over = False
    crumble_effect = None
    
    # Transition State
    transition_active = False
    transition_radius = 0
    transition_speed = 80 # Very fast
    max_radius = int((SCREEN_WIDTH**2 + SCREEN_HEIGHT**2)**0.5) + 50
    transition_center = (0, 0)
    
    # Camera
    camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    # Surfaces
    canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)) # Used for final compositing
    old_screen_capture = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)) # Snapshot of old state
    next_state_capture = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)) # Render of new state

    while running:
        dt = clock.tick(FPS) / 1000.0
        
        # Toggle Input Logic
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r:
                        # Restart
                        player, platforms, spikes, projectiles, effects = reset_game()
                        tension_duration = 0.0
                        overload_timer = 0.0
                        game_over = False
                        crumble_effect = None
                        transition_active = False
                else:
                    if event.key == pygame.K_e or event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                        if not transition_active:
                            # START TRANSITION
                            transition_active = True
                            transition_radius = 0
                            # Get player center in SCREEN coordinates (camera-adjusted)
                            player_rect = player.get_rect()
                            player_screen_x = player_rect.centerx + camera.camera.x
                            player_screen_y = player_rect.centery + camera.camera.y
                            transition_center = (int(player_screen_x), int(player_screen_y))
                            
                            # Capture OLD state (including distortion)
                            # Passing background=background to ensure consistent capture
                            draw_game(old_screen_capture, player.is_white, player, platforms, projectiles, effects, background, spikes, camera)
                            # Note: We capture with current intensity
                            intensity = min(1.0, tension_duration / 12.0)
                            draw_distortion(old_screen_capture, intensity)
                            
                            # Perform Swap
                            player.swap_mask()
                            
                    # Shooting Input (Key: X)
                    if event.key == pygame.K_x:
                        proj = player.shoot()
                        if proj:
                            projectiles.append(proj)
            
            # Shooting / Melee Input (Mouse: Left Click)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left Click
                    if player.is_white:
                        # Peace Mode: Shoot
                        proj = player.shoot()
                        if proj:
                            projectiles.append(proj)
                    else:
                        # Tension Mode: Melee
                        new_effects = player.melee_attack()
                        if new_effects:
                            effects.extend(new_effects)
        
        if not game_over:
            # Update Background Parallax
            # Only update if player is moving
            background.update(player.vel_x)

            # Tension Logic based on state
            if not player.is_white: # Mask Off (Black/Tension)
                tension_duration += dt
            else: # Mask On (White/Peace)
                tension_duration -= dt * 10.0 # Fast Decay
                
            # Clamp tension
            tension_duration = max(0.0, tension_duration)
            
            # Calculate Intensity (0.0 to 1.0)
            intensity = min(1.0, tension_duration / 12.0)
            
            # Overload Logic
            if intensity >= 1.0:
                overload_timer += dt
                if overload_timer > 3.0:
                    game_over = True
            else:
                overload_timer = 0.0
            
            # Update logic
            player.update(platforms)
            
            # Projectile Logic
            for proj in projectiles[:]:
                proj.update()
                if proj.marked_for_deletion:
                    projectiles.remove(proj)
                    continue
                
                # Collision Check
                proj_rect = proj.get_rect()
                hit = False
                
                for platform in platforms:
                    # Check if platform is active/solid
                    if player.is_neutral_collision(platform):
                        if proj_rect.colliderect(platform.get_rect()):
                            hit = True
                            # Spawn splat
                            effects.append(SplatBlast(proj.x, proj.y, proj.color))
                            break
                
                if hit:
                    projectiles.remove(proj)

            # Effects Logic
            for eff in effects[:]:
                eff.update()
                if eff.timer > eff.lifetime:
                    effects.remove(eff)
            
            # Spike Logic
            player_rect = player.get_rect()
            for spike in spikes:
                if player.is_neutral_collision(spike):
                     spike_rect = spike.get_rect()
                     if player_rect.colliderect(spike_rect):
                         # Fatal collision
                         game_over = True
                         crumble_effect = CrumbleEffect(screen)
                         break

            
            # Calculate Screen Shake
            shake_x = 0
            shake_y = 0
            
            # Combine sources of shake
            total_intensity = intensity
            shake_amp = 10 * total_intensity
            
            if overload_timer > 0:
                shake_amp += overload_timer * 5 
                
            # Add Player Trauma/Shake (e.g. from Katana)
            shake_amp += getattr(player, 'shake_intensity', 0)
            
            if shake_amp > 0:
                shake_x = int((random.random() - 0.5) * 2 * shake_amp)
                shake_y = int((random.random() - 0.5) * 2 * shake_amp)
            
            # Update Camera
            camera.update(player)
            
            # --- DRAW SEQUENCE ---
            
            if transition_active:
                transition_radius += transition_speed
                
                # 1. Draw NEW state to next_state_capture
                draw_game(next_state_capture, player.is_white, player, platforms, projectiles, effects, background, spikes, camera)
                # Apply NEW distortion (likely 0 if swapping to White, or building up if Black)
                draw_distortion(next_state_capture, intensity)
                
                # 2. Prepare Mask
                mask_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.circle(mask_surf, (255, 255, 255, 255), transition_center, int(transition_radius))
                
                # 3. Mask the NEW state
                # Use BLEND_RGBA_MIN to keep only the circle part of next_state_capture
                # We need a copy because we modify it
                masked_next = next_state_capture.copy()
                masked_next.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                
                # 4. Composite: Start with OLD state, draw masking circle logic?
                # Actually simpler:
                # Draw Old State (Background)
                canvas.blit(old_screen_capture, (0,0))
                # Draw Masked New State (Foreground)
                canvas.blit(masked_next, (0,0))
                
                if transition_radius > max_radius:
                    transition_active = False
            else:
                # Standard Draw
                draw_game(canvas, player.is_white, player, platforms, projectiles, effects, background, spikes, camera)
                draw_distortion(canvas, intensity)

            # Final Blit to Screen with Shake
            # Fill with current BG color to hide borders if shake exposes them
            current_bg = CREAM if player.is_white else BLACK_MATTE
            screen.fill(current_bg) 
            screen.blit(canvas, (shake_x, shake_y))
            
        else:
            # Game Over State (Pixel Crumble)
            if crumble_effect is None:
                crumble_effect = CrumbleEffect(screen)
            
            crumble_effect.update()
            crumble_effect.draw(screen)
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()
