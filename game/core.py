import pygame
import sys
import random
from .settings import *
from .sprites import Player, Platform, Projectile, SplatBlast, Spike, SlashWave
from .utils import draw_game, draw_distortion, CrumbleEffect, Camera
from .background import ParallaxBackground
from .enemy import MirrorRonin

def run():
    # Initialize Pygame
    pygame.init()

    # Game setup
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("MonoMask")
    pygame.mouse.set_visible(False) # Hide system cursor, use in-game reticle
    clock = pygame.time.Clock()
    
    # Initialize Background
    background = ParallaxBackground()
    
    # Camera object (optional, currently using manual offset)
    camera = None

    def reset_game():
        # Create player (starts as WHITE character)
        player = Player(100, 100)
    
        # Fixed Level Layout (Based on Reference Image approximation)
        # Sequence of platforms going Right and Up
        
        map_width = 6000
        map_height = 2000
        base_y = map_height - 200
        
        platforms_data = [
              # Tutorial platforms data 
             {'x': 50, 'y': base_y, 'w': 500, 'type': 'neutral'},
             {'x': 700, 'y': base_y-100, 'w': 100, 'type': 'white'},
             {'x': 900, 'y': base_y-200, 'w': 100, 'type': 'black'},
             {'x': 1100, 'y': base_y-290, 'w': 1000, 'type': 'neutral'},
             {'x': 2200, 'y': base_y-400, 'w': 200, 'type': 'white'},
             {'x': 2400, 'y': base_y-500, 'w': 200, 'type': 'black'},
             {'x': 2600, 'y': base_y-290, 'w': 200, 'type': 'black'},
             {'x': 2900, 'y': base_y-200, 'w': 1500, 'type': 'neutral'},
             {'x': 4500, 'y': base_y-300, 'w': 150, 'type': 'black'},
             {'x': 4700, 'y': base_y-400, 'w': 150, 'type': 'neutral'},
             {'x': 4450, 'y': base_y-500, 'w': 150, 'type': 'black'},
             {'x': 4350, 'y': base_y-600, 'w': 150, 'type': 'white'},
             {'x': 4550, 'y': base_y-700, 'w': 150, 'type': 'black'},
             {'x': 4800, 'y': base_y-650, 'w': 120, 'type': 'black'},
             {'x': 5100, 'y': base_y-600, 'w': 200, 'type': 'neutral'},
             {'x': 5400, 'y': base_y-700, 'w': 50, 'type': 'black'},
             {'x': 5600, 'y': base_y-800, 'w': 50, 'type': 'black'},
             {'x': 5800, 'y': base_y-900, 'w': 50, 'type': 'black'},
             {'x': 6000, 'y': base_y-1000, 'w': 100, 'type': 'white'},
             {'x': 6200, 'y': base_y-700, 'w': 50, 'type': 'black'},
             {'x': 6500, 'y': base_y-400, 'w': 50, 'type': 'black'},
             {'x': 6700, 'y': base_y-200, 'w': 300, 'type': 'neutral'},
             {'x': 7150, 'y': base_y-300, 'w': 200, 'type': 'white'},
             {'x': 7400, 'y': base_y-400, 'w': 200, 'type': 'white'},
             {'x': 7700, 'y': base_y-200, 'w': 1000, 'type': 'neutral'},

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
            
        # Spawn Enemies
        # Helper function to spawn based on level data
        def spawn_enemies_for_level(plat_data):
            spawned = []
            if not plat_data:
                return spawned
                
            # User Request: Spawn on the LAST platform by default
            last_plat = plat_data[-1]
            
            # center x of platform
            spawn_x = last_plat['x'] + last_plat['w'] // 2 - 25 # -25 for half enemy width
            spawn_y = last_plat['y'] - 60 # Above platform
            
        # Spawn enemy on the last platform
        last_plat = platforms_data[-1]
        enemy_x = last_plat['x'] + last_plat['w'] // 2 - 25  # Center of platform
        enemy_y = last_plat['y'] - 60  # Above platform
        enemies = [MirrorRonin(enemy_x, enemy_y)]
        
        projectiles = []
        effects = []
        return player, platforms, spikes, projectiles, effects, enemies

    player, platforms, spikes, projectiles, effects, enemies = reset_game()

    # Main game loop
    running = True
    
    # Tension Mechanics State
    tension_duration = 0.0
    overload_timer = 0.0
    game_over = False
    crumble_effect = None
    
    # Forced Mode State (Mental Drain)
    forced_black_mode_timer = 0.0
    
    # Camera State
    scroll_x = 0
    scroll_y = 0 # No vertical scroll yet
    
    # Transition State
    transition_active = False
    transition_radius = 0
    transition_speed = 80 # Very fast
    max_radius = int((SCREEN_WIDTH**2 + SCREEN_HEIGHT**2)**0.5) + 50
    transition_center = (0, 0)
    
    # Pause Menu State
    paused = False
    menu_state = "PAUSE" # PAUSE, OPTIONS
    pause_menu_options = ["Continue", "Restart", "Options", "Main Menu"]
    options_menu_options = ["Toggle Fullscreen", "Reticle Sensitivity", "Back"]
    pause_selected = 0  # Currently highlighted option
    
    # Sensitivity setting (1.0 = default, 0.5 = slow, 2.0 = fast)
    reticle_sensitivity = 1.0
    
    # Camera
    # camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    is_fullscreen = False
    
    # Surfaces
    canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)) # Used for final compositing
    old_screen_capture = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)) # Snapshot of old state
    next_state_capture = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)) # Render of new state

    while running:
        dt = clock.tick(FPS) / 1000.0
        
        # Update Forced Timer
        if forced_black_mode_timer > 0:
            forced_black_mode_timer -= dt
            if forced_black_mode_timer < 0:
                forced_black_mode_timer = 0
        
        # Toggle Input Logic
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r:
                        # Restart
                        player, platforms, spikes, projectiles, effects, enemies = reset_game()
                        tension_duration = 0.0
                        overload_timer = 0.0
                        forced_black_mode_timer = 0.0
                        scroll_x = 0
                        scroll_y = 0
                        game_over = False
                        crumble_effect = None
                        crumble_effect = None
                        transition_active = False
                else:
                    # ESC Key - Toggle Pause Menu
                    # ESC Key - Toggle Pause Menu
                    if event.key == pygame.K_ESCAPE:
                        if menu_state == "OPTIONS":
                            menu_state = "PAUSE"
                            pause_selected = 0
                        else:
                            paused = not paused
                            menu_state = "PAUSE"
                            pause_selected = 0  # Reset selection
                    
                    # Pause Menu Navigation
                    elif paused:
                        # Shared Navigation
                        num_options = len(pause_menu_options) if menu_state == "PAUSE" else len(options_menu_options)
                        
                        if event.key == pygame.K_UP or event.key == pygame.K_w:
                            pause_selected = (pause_selected - 1) % num_options
                        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                            pause_selected = (pause_selected + 1) % num_options
                        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                            # Execute selected option
                            
                            if menu_state == "PAUSE":
                                selected_option = pause_menu_options[pause_selected]
                                if selected_option == "Continue":
                                    paused = False
                                elif selected_option == "Restart":
                                    player, platforms, spikes, projectiles, effects, enemies = reset_game()
                                    tension_duration = 0.0
                                    overload_timer = 0.0
                                    forced_black_mode_timer = 0.0
                                    scroll_x = 0
                                    scroll_y = 0
                                    game_over = False
                                    crumble_effect = None
                                    transition_active = False
                                    paused = False
                                elif selected_option == "Options":
                                    menu_state = "OPTIONS"
                                    pause_selected = 0
                                elif selected_option == "Main Menu":
                                    pygame.quit()
                                    return "main_menu"
                                    
                            elif menu_state == "OPTIONS":
                                selected_option = options_menu_options[pause_selected]
                                if selected_option == "Toggle Fullscreen":
                                    # Toggle Logic
                                    is_fullscreen = not is_fullscreen
                                    if is_fullscreen:
                                        # Native Fullscreen
                                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                                    else:
                                        # Windowed Default
                                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                                    
                                    # Recreate surfaces at new resolution
                                    new_w, new_h = screen.get_size()
                                    canvas = pygame.Surface((new_w, new_h))
                                    old_screen_capture = pygame.Surface((new_w, new_h))
                                    next_state_capture = pygame.Surface((new_w, new_h))
                                    
                                elif selected_option == "Back":
                                    menu_state = "PAUSE"
                                    pause_selected = 0
                        
                        # Handle left/right for sensitivity adjustment
                        if menu_state == "OPTIONS" and options_menu_options[pause_selected] == "Reticle Sensitivity":
                            if event.key == pygame.K_LEFT:
                                reticle_sensitivity = max(0.2, reticle_sensitivity - 0.1)
                            elif event.key == pygame.K_RIGHT:
                                reticle_sensitivity = min(3.0, reticle_sensitivity + 0.1)
                    
                    # Only process game inputs if NOT paused
                    elif not paused:
                        if event.key == pygame.K_e or event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                            # Prevent Swap if Forced
                            if forced_black_mode_timer > 0:
                                # Play "Locked" sound or visual shake?
                                # For now just ignore
                                pass
                            elif not transition_active:
                                # START TRANSITION
                                transition_active = True
                                transition_radius = 0
                                # Get player center in SCREEN coordinates (camera-adjusted)
                                player_rect = player.get_rect()
                                player_screen_x = player_rect.centerx - scroll_x
                                player_screen_y = player_rect.centery - scroll_y
                                transition_center = (int(player_screen_x), int(player_screen_y))
                                
                                # Capture OLD state (including distortion)
                                # Passing background=background to ensure consistent capture
                                draw_game(old_screen_capture, player.is_white, player, 
                                         platforms=platforms, 
                                         projectiles=projectiles, 
                                         effects=effects, 
                                         background=background, 
                                         spikes=spikes, 
                                         camera=camera, 
                                         enemies=enemies, 
                                         offset=camera_offset)
                                # Note: We capture with current intensity
                                intensity = min(1.0, tension_duration / 12.0)
                                draw_distortion(old_screen_capture, intensity)
                                
                                # Perform Swap
                                player.swap_mask()
                                
                                # Sanity Reset: If switching to White (Calm), 
                                # ensure tension is below the Forced Trigger (8.0)
                                # otherwise it will instantly swap back next frame.
                                if player.is_white:
                                    tension_duration = min(tension_duration, 7.0)
                                
                        # Shooting Input (Key: X)
                        if event.key == pygame.K_x:
                            proj = player.shoot()
                            if proj:
                                projectiles.append(proj)
            
            # Shooting / Melee Input (Mouse: Left Click) - Only when not paused
            if event.type == pygame.MOUSEBUTTONDOWN and not paused:
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
            # Calculate values needed for drawing even when paused
            intensity = min(1.0, tension_duration / 12.0)
            
            # Camera Logic (needed for drawing)
            current_sw, current_sh = screen.get_size()
            
            if not paused:
                # --- ALL GAME UPDATES (Only when not paused) ---
                
                # Update Background Parallax
                background.update(player.vel_x)

                # Tension Logic based on state
                active_ronins = 0
                
                if not player.is_white: # Mask Off (Black/Tension)
                    tension_duration += dt
                    drain_status = "BUILDING (Black Mode)"
                else: # Mask On (White/Peace)
                    # Check for "Mental Drain" from active enemies
                    for e in enemies:
                        if isinstance(e, MirrorRonin) and not e.marked_for_deletion:
                            dist = abs(e.x - player.x)
                            if dist < 500: # Only drain if close (Proximity effect)
                                active_ronins += 1
                                
                    if active_ronins > 0:
                        tension_duration += dt * 0.4 * active_ronins
                        if tension_duration > 8.0:
                            tension_duration = 8.0
                        drain_status = "BUILDING (Enemy)"
                    else:
                        drain_rate = 5.0
                        tension_duration -= dt * drain_rate
                        drain_status = f"DRAINING (Rate {drain_rate})"
                    
                # Clamp tension
                tension_duration = max(0.0, min(tension_duration, 12.0))
                
                # Recalculate Intensity after update
                intensity = min(1.0, tension_duration / 12.0)
                
                # Forced Switch Logic (Trigger at 8.0 Tension)
                if player.is_white and tension_duration >= 8.0:
                     if not transition_active:
                         transition_active = True
                         transition_radius = 0
                         transition_center = player.get_rect().center
                         
                         draw_game(old_screen_capture, player.is_white, player, 
                                  platforms=platforms, 
                                  projectiles=projectiles, 
                                  effects=effects, 
                                  background=background,
                                  spikes=spikes,
                                  camera=camera,
                                  enemies=enemies, 
                                  offset=camera_offset)
                         draw_distortion(old_screen_capture, intensity)
                         
                         player.swap_mask()
                         forced_black_mode_timer = 5.0
                         tension_duration = 8.0 
                         
                # Overload Logic
                if tension_duration >= 12.0 and not player.is_white:
                    overload_timer += dt
                    if overload_timer > 3.0:
                        game_over = True
                else:
                    overload_timer = 0.0
                
                # Camera Logic - Update scroll
                target_scroll_x = player.x - current_sw / 2 + player.width / 2
                scroll_x += (target_scroll_x - scroll_x) * 0.1
                
                target_scroll_y = player.y - current_sh / 2 + player.height / 2
                scroll_y += (target_scroll_y - scroll_y) * 0.1
                
                if scroll_x < 0:
                    scroll_x = 0
                if scroll_y < 0: 
                    scroll_y = 0
                
                camera_offset = (int(scroll_x), int(scroll_y))
                
                # Mouse position
                mouse_pos_canvas = pygame.mouse.get_pos()
                
                # Update player
                player.update(platforms, offset=camera_offset, mouse_pos=mouse_pos_canvas, aim_sensitivity=reticle_sensitivity)
                
                # Check for void death - instant respawn
                if player.fell_into_void:
                    player, platforms, spikes, projectiles, effects, enemies = reset_game()
                    tension_duration = 0.0
                    overload_timer = 0.0
                    forced_black_mode_timer = 0.0
                    scroll_x = 0
                    scroll_y = 0
                    transition_active = False
                    continue  # Skip rest of update this frame
                
                # Projectile Logic
                for proj in projectiles[:]:
                    proj.update(offset=camera_offset)
                    if proj.marked_for_deletion:
                        projectiles.remove(proj)
                        continue
                    
                    proj_rect = proj.get_rect() 
                    hit = False
                    
                    for platform in platforms:
                        if player.is_neutral_collision(platform):
                            if proj_rect.colliderect(platform.get_rect()):
                                hit = True
                                impact_x = proj.x - proj.vx
                                impact_y = proj.y - proj.vy
                                effects.append(SplatBlast(impact_x, impact_y, proj.color))
                                break
                    
                    if hit:
                        projectiles.remove(proj)
                        continue

                    if not proj.is_player_shot:
                        if proj.get_rect().colliderect(player.get_rect()):
                            projectiles.remove(proj)
                            effects.append(SplatBlast(proj.x, proj.y, proj.color))
                            # Only increase tension in white mode (peace)
                            # In black mode (tension), just take damage/knockback
                            if player.is_white:
                                tension_duration += 3.0
                            player.shake_intensity = 15.0
                            dx = player.x - proj.x
                            if dx == 0: dx = 1
                            direction = dx / abs(dx)
                            player.vel_x = direction * 8
                            player.vel_y = -4
                            continue

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
                             game_over = True
                             crumble_effect = CrumbleEffect(screen)
                             break

                # Enemy Logic
                for enemy in enemies[:]:
                    enemy.update(player, platforms, offset=camera_offset)
                    if enemy.marked_for_deletion:
                        enemies.remove(enemy)
                        continue
                    
                    enemy_rect = enemy.get_rect()
                    for proj in projectiles[:]:
                        if proj.get_rect().colliderect(enemy_rect):
                            if player.is_white and proj.is_player_shot:
                                 enemy.take_damage("projectile")
                                 projectiles.remove(proj)
                                 effects.append(SplatBlast(proj.x, proj.y, proj.color))
                    
                    if not player.is_white:
                        for eff in effects:
                            if isinstance(eff, SlashWave): 
                                if eff.check_collision(enemy.get_rect()):
                                    enemy.take_damage("melee")
                                    effects.append(SplatBlast(enemy.x, enemy.y, WHITE))
                                    
                                    if enemy.health <= 0:
                                        print("ENEMY KILLED! Healing Tension.")
                                        enemy.marked_for_deletion = True
                                        tension_duration -= 5.0
                                        tension_duration = max(0.0, tension_duration)
                                    break
                    
                    if hasattr(enemy, 'pending_projectiles') and enemy.pending_projectiles:
                        projectiles.extend(enemy.pending_projectiles)
                        enemy.pending_projectiles = []
                        
                    if enemy.get_rect().colliderect(player.get_rect()):
                        tension_duration += 2.0
                        dx = player.x - enemy.x
                        if dx == 0: dx = 1
                        direction = dx / abs(dx)
                        player.vel_x = direction * 10
                        player.vel_y = -5
                        player.shake_intensity = 10.0
                        enemy.vel_x = -direction * 10
            
            # Calculate Screen Shake (can happen even when paused, but won't change much)
            shake_x = 0
            shake_y = 0
            
            if not paused:
                total_intensity = intensity
                shake_amp = 10 * total_intensity
                
                if overload_timer > 0:
                    shake_amp += overload_timer * 5 
                    
                shake_amp += getattr(player, 'shake_intensity', 0)
                
                if shake_amp > 0:
                    shake_x = int((random.random() - 0.5) * 2 * shake_amp)
                    shake_y = int((random.random() - 0.5) * 2 * shake_amp)
            
            # Update Camera
            # camera.update(player)
            
            # --- DRAW SEQUENCE ---
            
            if transition_active:
                transition_radius += transition_speed
                
                # 1. Draw NEW state to next_state_capture
                draw_game(next_state_capture, player.is_white, player, 
                         platforms=platforms, 
                         projectiles=projectiles, 
                         effects=effects, 
                         background=background, 
                         spikes=spikes, 
                         camera=camera, 
                         enemies=enemies, 
                         offset=camera_offset)
                # Apply NEW distortion (likely 0 if swapping to White, or building up if Black)
                draw_distortion(next_state_capture, intensity)
                
                # 2. Prepare Mask
                mask_w, mask_h = canvas.get_size()
                mask_surf = pygame.Surface((mask_w, mask_h), pygame.SRCALPHA)
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
                draw_game(canvas, player.is_white, player, 
                         platforms=platforms, 
                         projectiles=projectiles, 
                         effects=effects, 
                         background=background, 
                         spikes=spikes, 
                         camera=camera, 
                         enemies=enemies, 
                         offset=camera_offset)
                draw_distortion(canvas, intensity)

            # Final Blit to Screen with Shake
            # Fill with current BG color to hide borders if shake exposes them
            current_bg = CREAM if player.is_white else BLACK_MATTE
            screen.fill(current_bg) 
            
            # Canvas is now at native resolution, no scaling needed
            screen.blit(canvas, (shake_x, shake_y))
            
            # FPS Counter (Top Right, game-style)
            fps_font = pygame.font.Font(None, 28)
            current_fps = int(clock.get_fps())
            fps_color = (0, 255, 0) if current_fps >= 55 else (255, 255, 0) if current_fps >= 30 else (255, 0, 0)
            fps_text = fps_font.render(f"FPS: {current_fps}", True, fps_color)
            fps_rect = fps_text.get_rect(topright=(screen.get_width() - 10, 10))
            screen.blit(fps_text, fps_rect)
            
            # DEBUG HUD
            debug_font = pygame.font.Font(None, 24)
            d_stat = locals().get('drain_status', 'N/A')
            dbg_str = f"Tension: {tension_duration:.2f} | Active: {locals().get('active_ronins', '?')} | Status: {d_stat} | Global: {len(enemies)}"
            dbg_text = debug_font.render(dbg_str, True, (0, 255, 0) if not player.is_white else (255, 0, 0))
            screen.blit(dbg_text, (10, 80))
            
            # UI Overlays (Forced Mode Warning)
            if forced_black_mode_timer > 0:
                 f_font = pygame.font.Font(None, 40)
                 alert = f_font.render(f"LOCKED IN RAGE: {forced_black_mode_timer:.1f}s", True, WHITE)
                 screen.blit(alert, (SCREEN_WIDTH//2 - 150, 100))
                 
            # --- PAUSE MENU OVERLAY ---
            if paused:
                # Get actual screen dimensions
                sw, sh = screen.get_size()
                
                # Dim the screen
                overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180)) # Semi-transparent black
                screen.blit(overlay, (0, 0))
                
                # Draw Menu
                menu_font = pygame.font.Font(None, 50)
                title_font = pygame.font.Font(None, 80)
                
                # Title
                title_text = "PAUSED" if menu_state == "PAUSE" else "OPTIONS"
                title_surf = title_font.render(title_text, True, WHITE)
                screen.blit(title_surf, (sw//2 - title_surf.get_width()//2, 150))
                
                # Options
                options_to_draw = pause_menu_options if menu_state == "PAUSE" else options_menu_options
                
                start_y = 250
                gap_y = 60
                
                for i, option in enumerate(options_to_draw):
                    color = WHITE
                    text = option
                    
                    # Special handling for sensitivity display
                    if option == "Reticle Sensitivity":
                        text = f"Reticle Sensitivity: {reticle_sensitivity:.1f}x"
                    
                    if i == pause_selected:
                        color = (255, 200, 50) # Highlight Color (Gold)
                        if option == "Reticle Sensitivity":
                            text = f"< {text} >"
                        else:
                            text = f"> {text} <"
                        
                    opt_surf = menu_font.render(text, True, color)
                    screen.blit(opt_surf, (sw//2 - opt_surf.get_width()//2, start_y + i * gap_y))

        elif game_over:
            # Game Over State (Pixel Crumble)
            if crumble_effect is None:
                crumble_effect = CrumbleEffect(screen)
            
            crumble_effect.update()
            crumble_effect.draw(screen)
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()
