import pygame
import sys
import random
from .settings import *
from .sprites import Player, Platform, Projectile, SplatBlast, Spike, SlashWave, Portal
from .utils import draw_game, draw_distortion, CrumbleEffect, Camera
from .background import ParallaxBackground
from .enemy import MirrorRonin

def run():
    # Initialize Pygame
    pygame.init()
    pygame.mixer.init()  # Initialize audio mixer

    # Game setup
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("MonoMask")
    pygame.mouse.set_visible(False) # Hide system cursor, use in-game reticle
    clock = pygame.time.Clock()
    
    # Load Peace Mode Music
    try:
        pygame.mixer.music.load("assets/Drifting Memories.mp3")
        pygame.mixer.music.set_volume(0.5)  # 50% volume
        music_loaded = True
    except:
        print("Warning: Could not load peace mode music")
        music_loaded = False
    
    # Load Mode Switch Sound Effect
    try:
        shadow_sound = pygame.mixer.Sound("assets/shadow.mp3")
        shadow_sound.set_volume(0.7)  # 70% volume
    except:
        print("Warning: Could not load shadow sound effect")
        shadow_sound = None
    
    # Music state
    music_playing = False
    
    # Initialize Background
    background = ParallaxBackground()
    
    # Camera object (optional, currently using manual offset)
    camera = None

    def reset_game(level="TUTORIAL"):
        # Create player (starts as WHITE character)
        player = Player(100, 100)
    
        # Fixed Level Layout (Based on Reference Image approximation)
        # Sequence of platforms going Right and Up
        
        map_width = 6000
        map_height = 2000
        base_y = map_height - 200
        
        # Define level data based on current level
        if level == "TUTORIAL":
            platforms_data = [
                # ========== SECTION 1: BASICS (Learning to move) ==========
                # Starting area - large, safe
                {'x': 50, 'y': base_y, 'w': 400, 'type': 'neutral'},
                # Easy first jump (small gap, same height)
                {'x': 500, 'y': base_y-100, 'w': 290, 'type': 'neutral'},
                # Second easy jump
                {'x': 890, 'y': base_y-180, 'w': 150, 'type': 'neutral'},
                # Gentle rise (short gap, slight height)
                {'x': 1200, 'y': base_y-50, 'w': 500, 'type': 'neutral'},
                
                # ========== SECTION 2: INTRODUCE WHITE PLATFORMS ==========
                # Safe landing before white intro
                {'x': 1800, 'y': base_y-120, 'w': 350, 'type': 'neutral'},
                # First white platform (easy jump)
                {'x': 2200, 'y': base_y-80, 'w': 250, 'type': 'white'},
                # Second white platform (practice)
                {'x': 2550, 'y': base_y-20, 'w': 250, 'type': 'white'},
                # Back to neutral for breathing room
                {'x': 2900, 'y': base_y-50, 'w': 400, 'type': 'neutral'},
                
                # ========== SECTION 3: INTRODUCE BLACK PLATFORMS ==========
                # Black platform intro
                {'x': 3400, 'y': base_y-100, 'w': 150, 'type': 'black'},
                # Second black platform
                {'x': 3650, 'y': base_y-130, 'w': 150, 'type': 'black'},
                # Neutral rest area
                {'x': 3900, 'y': base_y-50, 'w': 450, 'type': 'neutral'},
                
                # ========== SECTION 4: MIXED PLATFORMING ==========
                # Alternating white and black
                {'x': 4420, 'y': base_y-150, 'w': 80, 'type': 'white'},
                {'x': 4150, 'y': base_y-280, 'w': 200, 'type': 'black'},
                {'x': 4450, 'y': base_y-400, 'w': 250, 'type': 'white'},
                # Large neutral landing
                {'x': 4800, 'y': base_y-100, 'w': 600, 'type': 'neutral'},
                
                # ========== SECTION 5: MODERATE CHALLENGE ==========
                # Rising platforms with gaps
                {'x': 5500, 'y': base_y-200, 'w': 150, 'type': 'neutral'},
                {'x': 5750, 'y': base_y-280, 'w': 150, 'type': 'white'},
                {'x': 6000, 'y': base_y-360, 'w': 150, 'type': 'black'},
                {'x': 6250, 'y': base_y-440, 'w': 150, 'type': 'neutral'},
                # Descending back down
                {'x': 6500, 'y': base_y-350, 'w': 150, 'type': 'white'},
                {'x': 6750, 'y': base_y-260, 'w': 150, 'type': 'black'},
                {'x': 7000, 'y': base_y-170, 'w': 200, 'type': 'neutral'},
                
                # ========== SECTION 6: LONGER JUMPS ==========
                # Bigger gaps requiring commitment
                {'x': 7400, 'y': base_y-150, 'w': 250, 'type': 'neutral'},
                {'x': 7700, 'y': base_y-200, 'w': 220, 'type': 'white'},
                {'x': 8000, 'y': base_y-250, 'w': 200, 'type': 'black'},
                {'x': 8300, 'y': base_y-200, 'w': 350, 'type': 'neutral'},
                
                # ========== SECTION 7: FINAL APPROACH ==========
                # Staircase up to the portal
                {'x': 8750, 'y': base_y-250, 'w': 250, 'type': 'white'},
                {'x': 9050, 'y': base_y-320, 'w': 250, 'type': 'black'},
                {'x': 9350, 'y': base_y-390, 'w': 250, 'type': 'white'},
                {'x': 9650, 'y': base_y-460, 'w': 250, 'type': 'black'},
                
                # ========== PORTAL AREA ==========
                # Final safe zone with portal
                {'x': 9950, 'y': base_y-460, 'w': 700, 'type': 'neutral'},
            ]
        else:  # LEVEL_1
            platforms_data = [
                # Level 1 - The original harder level
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
            
        # Portal for tutorial level (at end of last platform)
        portal = None
        if level == "TUTORIAL":
            last_plat = platforms_data[-1]
            portal_x = last_plat['x'] + last_plat['w'] - 80  # Near end of last platform
            portal_y = last_plat['y'] - 60  # Above platform
            portal = Portal(portal_x, portal_y)
        
        # Spawn Enemies
        enemies = []
        if level == "TUTORIAL":
            # Spawn enemy on the last platform of tutorial
            last_plat = platforms_data[-1]
            enemy_x = last_plat['x'] + last_plat['w'] // 2 - 25
            enemy_y = last_plat['y'] - 60
            enemies = [MirrorRonin(enemy_x, enemy_y)]
        elif level == "LEVEL_1":
            # Spawn enemy on the last platform
            last_plat = platforms_data[-1]
            enemy_x = last_plat['x'] + last_plat['w'] // 2 - 25
            enemy_y = last_plat['y'] - 60
            
            # Spawn enemy on the big middle platform (index 7)
            middle_plat = platforms_data[7]
            middle_enemy_x = middle_plat['x'] + middle_plat['w'] // 2 - 25
            middle_enemy_y = middle_plat['y'] - 60
            
            enemies = [MirrorRonin(enemy_x, enemy_y), MirrorRonin(middle_enemy_x, middle_enemy_y)]
        
        projectiles = []
        effects = []
        return player, platforms, spikes, projectiles, effects, enemies, portal

    # Level State
    current_level = "TUTORIAL"
    player, platforms, spikes, projectiles, effects, enemies, portal = reset_game(current_level)
    
    # Loading Screen State
    loading_screen_active = False
    loading_timer = 0.0
    loading_spinner_angle = 0.0
    next_level = None
    
    # Blackhole Suction Animation State
    blackhole_suction_active = False
    blackhole_suction_timer = 0.0
    blackhole_suction_duration = 2.0  # 2 seconds of suction animation
    blackhole_player_scale = 1.0  # Player shrinks during suction
    blackhole_player_rotation = 0.0  # Player spins into blackhole

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
                        player, platforms, spikes, projectiles, effects, enemies, portal = reset_game(current_level)
                        tension_duration = 0.0
                        overload_timer = 0.0
                        forced_black_mode_timer = 0.0
                        scroll_x = 0
                        scroll_y = 0
                        game_over = False
                        crumble_effect = None
                        transition_active = False
                        blackhole_suction_active = False
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
                                    player, platforms, spikes, projectiles, effects, enemies, portal = reset_game(current_level)
                                    tension_duration = 0.0
                                    overload_timer = 0.0
                                    forced_black_mode_timer = 0.0
                                    scroll_x = 0
                                    scroll_y = 0
                                    game_over = False
                                    crumble_effect = None
                                    transition_active = False
                                    blackhole_suction_active = False
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
                                         offset=camera_offset,
                                         portal=portal)
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
        
        # ========== LOADING SCREEN HANDLING ==========
        if loading_screen_active:
            loading_timer += dt
            loading_spinner_angle += dt * 5  # Spin the symbol
            
            # Loading screen duration
            loading_duration = 3.0  # 3 seconds
            
            # Draw loading screen
            screen.fill((0, 0, 0))  # Black background
            
            sw, sh = screen.get_size()
            
            # "LEVEL 1" text at top
            level_font = pygame.font.Font(None, 120)
            level_text = level_font.render("LEVEL 1", True, (255, 255, 255))
            level_rect = level_text.get_rect(center=(sw // 2, sh // 4))
            screen.blit(level_text, level_rect)
            
            # Subtitle
            sub_font = pygame.font.Font(None, 40)
            sub_text = sub_font.render("The Journey Begins", True, (150, 150, 150))
            sub_rect = sub_text.get_rect(center=(sw // 2, sh // 4 + 60))
            screen.blit(sub_text, sub_rect)
            
            # Spinning Yin-Yang style symbol
            import math as m
            cx, cy = sw // 2, sh // 2 + 50
            radius = 60
            
            # Draw rotating symbol (white and black halves)
            for i in range(32):
                angle = (i / 32) * 2 * m.pi + loading_spinner_angle
                next_angle = ((i + 1) / 32) * 2 * m.pi + loading_spinner_angle
                
                # Alternate colors
                color = (255, 255, 255) if i < 16 else (100, 100, 100)
                
                # Triangle from center to edge
                x1 = cx + m.cos(angle) * radius
                y1 = cy + m.sin(angle) * radius
                x2 = cx + m.cos(next_angle) * radius
                y2 = cy + m.sin(next_angle) * radius
                
                pygame.draw.polygon(screen, color, [(cx, cy), (x1, y1), (x2, y2)])
            
            # Inner circle
            pygame.draw.circle(screen, (30, 30, 30), (cx, cy), 20)
            
            # Loading bar
            bar_width = 400
            bar_height = 10
            bar_x = sw // 2 - bar_width // 2
            bar_y = sh * 3 // 4
            
            # Background bar
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            
            # Progress bar
            progress = min(1.0, loading_timer / loading_duration)
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, int(bar_width * progress), bar_height))
            
            # "Loading..." text
            load_font = pygame.font.Font(None, 30)
            load_text = load_font.render("Loading...", True, (200, 200, 200))
            load_rect = load_text.get_rect(center=(sw // 2, bar_y + 40))
            screen.blit(load_text, load_rect)
            
            pygame.display.flip()
            
            # Transition to next level after loading
            if loading_timer >= loading_duration:
                loading_screen_active = False
                current_level = next_level
                player, platforms, spikes, projectiles, effects, enemies, portal = reset_game(current_level)
                tension_duration = 0.0
                overload_timer = 0.0
                forced_black_mode_timer = 0.0
                scroll_x = 0
                scroll_y = 0
                transition_active = False
                blackhole_suction_active = False
            
            continue  # Skip normal game loop during loading
        
        if not game_over:
            # Calculate values needed for drawing even when paused
            intensity = min(1.0, tension_duration / 12.0)
            
            # Camera Logic (needed for drawing)
            current_sw, current_sh = screen.get_size()
            
            if not paused:
                # --- ALL GAME UPDATES (Only when not paused) ---
                
                # Update Background Parallax
                background.update(player.vel_x)
                
                # Music Control - Play only in Peace Mode
                if music_loaded:
                    if player.is_white:
                        # Check if music should be playing but stopped
                        if not pygame.mixer.music.get_busy():
                            # Start/restart peace music (loop infinitely)
                            pygame.mixer.music.play(-1)
                            music_playing = True
                    elif music_playing:
                        # Fade out music when entering tension mode
                        pygame.mixer.music.fadeout(500)  # 500ms fade
                        music_playing = False
                        # Play shadow sound effect as mode switch indicator
                        if shadow_sound:
                            shadow_sound.play()

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
                                  offset=camera_offset,
                                  portal=portal)
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
                    player, platforms, spikes, projectiles, effects, enemies, portal = reset_game(current_level)
                    tension_duration = 0.0
                    overload_timer = 0.0
                    forced_black_mode_timer = 0.0
                    scroll_x = 0
                    scroll_y = 0
                    transition_active = False
                    blackhole_suction_active = False
                    continue  # Skip rest of update this frame
                
                # Portal Update and Collision (Tutorial Level only)
                if portal and not blackhole_suction_active and not loading_screen_active:
                    portal.update()
                    
                    # Check collision
                    if portal.check_collision(player.get_rect()):
                        # Start blackhole suction animation
                        blackhole_suction_active = True
                        blackhole_suction_timer = 0.0
                        blackhole_player_scale = 1.0
                        blackhole_player_rotation = 0.0
                        next_level = "LEVEL_1"
                
                # Blackhole Suction Animation Logic
                if blackhole_suction_active:
                    blackhole_suction_timer += dt
                    
                    # Progress from 0 to 1
                    progress = blackhole_suction_timer / blackhole_suction_duration
                    
                    # Player shrinks and spins
                    blackhole_player_scale = max(0.0, 1.0 - progress)
                    blackhole_player_rotation += dt * 15  # Spin faster and faster
                    
                    # Move player towards portal center
                    if portal:
                        pull_strength = 200 * dt * (1 + progress)  # Accelerating pull
                        dx = portal.x - (player.x + player.width / 2)
                        dy = portal.y - (player.y + player.height / 2)
                        dist = max(1, (dx*dx + dy*dy)**0.5)
                        player.x += (dx / dist) * pull_strength
                        player.y += (dy / dist) * pull_strength
                    
                    # End suction, start loading screen
                    if blackhole_suction_timer >= blackhole_suction_duration:
                        blackhole_suction_active = False
                        loading_screen_active = True
                        loading_timer = 0.0
                        loading_spinner_angle = 0.0
                
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
                         offset=camera_offset,
                         portal=portal)
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
                         offset=camera_offset,
                         portal=portal)
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
            
            # DEBUG HUD - Top Right (below mode info)
            debug_font = pygame.font.Font(None, 24)
            d_stat = locals().get('drain_status', 'N/A')
            dbg_str = f"Tension: {tension_duration:.2f} | Active: {locals().get('active_ronins', '?')} | Status: {d_stat} | Global: {len(enemies)}"
            dbg_text = debug_font.render(dbg_str, True, (0, 255, 0) if not player.is_white else (255, 0, 0))
            dbg_rect = dbg_text.get_rect(topright=(screen.get_width() - 10, 100))
            screen.blit(dbg_text, dbg_rect)
            
            # UI Overlays (Forced Mode Warning)
            if forced_black_mode_timer > 0:
                 f_font = pygame.font.Font(None, 40)
                 alert = f_font.render(f"LOCKED IN RAGE: {forced_black_mode_timer:.1f}s", True, WHITE)
                 screen.blit(alert, (SCREEN_WIDTH//2 - 150, 100))
            
            # Tutorial Hint Text (only at start of tutorial level) - Top Left
            # Styled key legend like reference image
            if current_level == "TUTORIAL" and player.x < 500:
                key_font = pygame.font.Font(None, 26)
                label_font = pygame.font.Font(None, 26)
                
                # Controls to show
                controls = [
                    ("A/D", "Move Left / Right"),
                    ("SPACE", "Jump"),
                ]
                
                # Draw each control row (no background panel)
                for i, (key, label) in enumerate(controls):
                    y_pos = 15 + i * 35
                    
                    # Key box (dark gray rounded rectangle)
                    key_text_surf = key_font.render(key, True, (255, 255, 255))
                    key_width = key_text_surf.get_width() + 16
                    key_height = 26
                    key_rect = pygame.Rect(15, y_pos, key_width, key_height)
                    
                    # Draw rounded key box
                    pygame.draw.rect(screen, (70, 70, 70), key_rect, border_radius=4)
                    pygame.draw.rect(screen, (100, 100, 100), key_rect, width=1, border_radius=4)
                    
                    # Key text centered (white)
                    screen.blit(key_text_surf, (key_rect.x + 8, key_rect.y + 4))
                    
                    # Label text (gray)
                    label_surf = label_font.render(label, True, (150, 150, 150))
                    screen.blit(label_surf, (key_rect.right + 12, y_pos + 4))
            
            # Tutorial Hint for Mask ON/OFF at platform x=2900
            if current_level == "TUTORIAL" and 2900 <= player.x <= 3300:
                key_font = pygame.font.Font(None, 26)
                label_font = pygame.font.Font(None, 26)
                
                # Draw single control hint
                key = "SHIFT / E"
                label = "Mask ON/OFF"
                y_pos = 15
                
                # Key box (dark gray rounded rectangle)
                key_text_surf = key_font.render(key, True, (255, 255, 255))
                key_width = key_text_surf.get_width() + 16
                key_height = 26
                key_rect = pygame.Rect(15, y_pos, key_width, key_height)
                
                # Draw rounded key box
                pygame.draw.rect(screen, (70, 70, 70), key_rect, border_radius=4)
                pygame.draw.rect(screen, (100, 100, 100), key_rect, width=1, border_radius=4)
                
                # Key text centered (white)
                screen.blit(key_text_surf, (key_rect.x + 8, key_rect.y + 4))
                
                # Label text (gray)
                label_surf = label_font.render(label, True, (150, 150, 150))
                screen.blit(label_surf, (key_rect.right + 12, y_pos + 4))
            
            # Tutorial Hint for Fire at white platform (x=9350-9600)
            if current_level == "TUTORIAL" and 9350 <= player.x <= 9600:
                key_font = pygame.font.Font(None, 26)
                label_font = pygame.font.Font(None, 26)
                
                # CLICK RIGHT - Fire Shurikens (with key box)
                key = "CLICK RIGHT"
                label = "Fire Shuriken"
                y_pos = 15
                
                # Key box (dark gray rounded rectangle)
                key_text_surf = key_font.render(key, True, (255, 255, 255))
                key_width = key_text_surf.get_width() + 16
                key_height = 26
                key_rect = pygame.Rect(15, y_pos, key_width, key_height)
                
                # Draw rounded key box
                pygame.draw.rect(screen, (70, 70, 70), key_rect, border_radius=4)
                pygame.draw.rect(screen, (100, 100, 100), key_rect, width=1, border_radius=4)
                
                # Key text centered (white)
                screen.blit(key_text_surf, (key_rect.x + 8, key_rect.y + 4))
                
                # Label text (gray)
                label_surf = label_font.render(label, True, (150, 150, 150))
                screen.blit(label_surf, (key_rect.right + 12, y_pos + 4))
                 
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
