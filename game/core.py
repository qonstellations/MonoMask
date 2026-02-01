import pygame
import sys
import traceback
import random
from .settings import *
from .sprites import Player, Platform, Projectile, SplatBlast, Spike, SlashWave, BlackHole, Shard
from .utils import draw_game, draw_distortion, CrumbleEffect, Camera
from .background import ParallaxBackground
from .enemy import MirrorRonin, ShadowSelf
from .settings_manager import save_settings # Import settings manager

def run(screen, settings):
    # Initialize Pygame Mixer (Safe to call multiple times or checks init)
    # pygame.init() is handled in main.py
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    # Game setup
    # screen is passed exclusively
    # pygame.display.set_caption("MonoMask") # Handled in main
    pygame.mouse.set_visible(False) # Hide system cursor, use in-game reticle
    clock = pygame.time.Clock()
    
    # ... (Audio Lines) ...
    
    # Sensitivity setting (Loaded from settings)
    reticle_sensitivity = settings.get("sensitivity", 1.0)
    
    # ... (Rest of Init) ...
    
    # Audio Paths & Objects
    try:
        light_bg_sound = pygame.mixer.Sound("assets/light_audio_bg.wav")
        dark_bg_sound = pygame.mixer.Sound("assets/dark_audio_bg.wav")
    except Exception as e:
        print(f"Warning: Could not load BGM: {e}")
        light_bg_sound = None
        dark_bg_sound = None

    # Reserve channels for BGM so SFX don't interrupt them
    # Channel 0: Light Theme
    # Channel 1: Dark Theme
    pygame.mixer.set_reserved(2)
    bg_chan_light = pygame.mixer.Channel(0)
    bg_chan_dark = pygame.mixer.Channel(1)
    
    # Start playing loops immediately at 0 volume
    if light_bg_sound:
        bg_chan_light.play(light_bg_sound, loops=-1)
        bg_chan_light.set_volume(0)
        
    if dark_bg_sound:
        bg_chan_dark.play(dark_bg_sound, loops=-1)
        bg_chan_dark.set_volume(0)
        
    # Volume State for Crossfading
    current_vol_light = 0.0
    current_vol_dark = 0.0
    
    # Target volumes
    TARGET_VOL_LIGHT_MAX = 0.5
    TARGET_VOL_DARK_MAX = 0.4
    TARGET_VOL_DEATH_FACTOR = 0.4 / 0.7 # Scaling factor for death volume (approx 0.57)
    
    try:
        shadow_sound = pygame.mixer.Sound("assets/shadow.mp3")
        shadow_sound.set_volume(1.0)  # Max volume for thrill
    except:
        print("Warning: Could not load shadow sound effect")
        shadow_sound = None
        
    # Load Heartbeat Sound
    try:
        heartbeat_sound = pygame.mixer.Sound("assets/heartbeat.mp3")
        heartbeat_sound.set_volume(0.9)
    except:
        print("Warning: Could not load heartbeat sound")
        heartbeat_sound = None
        
    # Load Game Over Sound
    try:
        game_over_sound = pygame.mixer.Sound("assets/game_over.wav")
        game_over_sound.set_volume(0.8)
    except:
        print("Warning: Could not load game_over.wav")
        game_over_sound = None

    # Movement Audio State
    step_timer = 0.0
    step_interval = 0.5 # Slower steps (0.5s)
    
    # Load Movement SFX
    try:
        light_step_sound = pygame.mixer.Sound("assets/light_step.wav")
        light_step_sound.set_volume(0.5) # 50% intensity
        
        dark_step_sound = pygame.mixer.Sound("assets/dark_step.wav")
        dark_step_sound.set_volume(0.5) # 50% intensity
        
        jump_sound = pygame.mixer.Sound("assets/jump.mp3")
        jump_sound.set_volume(2.0)
        
        splat_sound = pygame.mixer.Sound("assets/splat.wav")
        splat_sound.set_volume(0.6)
        
        waves_sound = pygame.mixer.Sound("assets/waves.mp3")
        waves_sound.set_volume(0.6)
    except Exception as e:
        print(f"Warning: Could not load Movement/Attack SFX: {e}")
        light_step_sound, dark_step_sound, jump_sound = None, None, None
        splat_sound, waves_sound = None, None
    
    # Heartbeat state
    heartbeat_timer = 0.0
    heartbeat_interval = 1.0 # Starts slow
    
    # Initialize Background
    background = ParallaxBackground()
    
    # Camera object (optional, currently using manual offset)
    camera = None
    
    # Current Level Tracking
    current_level = 1

    def reset_game(level=1):
        nonlocal current_level
        current_level = level
        
        # Create player (starts as WHITE character)
        player = Player(100, 100)
    
        # Fixed Level Layout (Based on Reference Image approximation)
        # Sequence of platforms going Right and Up
        
        map_width = 9000
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
        elif level == "LEVEL_1":
            # Level 1 and Level 2 - The original harder level (TODO: add unique LEVEL_2 layout)
            platforms_data = [
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
        else:  # THE INNER SANCTUM - Final Boss Level (Strategic/Puzzle-focused)
            platforms_data = [
                # ========== SECTION 1: THE AWAKENING (0-2500px) ==========
                # Introduce the concept - think before you jump
                {'x': 50, 'y': base_y, 'w': 400, 'type': 'neutral'},
                # First puzzle: White platform leads to black, must toggle mid-air or before
                {'x': 550, 'y': base_y-100, 'w': 200, 'type': 'white'},
                {'x': 850, 'y': base_y-100, 'w': 200, 'type': 'black'},  # Same height - must toggle!
                {'x': 1150, 'y': base_y-50, 'w': 300, 'type': 'neutral'},
                # Rising with alternation - plan your mode
                {'x': 1550, 'y': base_y-150, 'w': 180, 'type': 'black'},
                {'x': 1830, 'y': base_y-250, 'w': 180, 'type': 'white'},
                {'x': 2100, 'y': base_y-150, 'w': 250, 'type': 'neutral'},
                
                # ========== SECTION 2: THE DESCENT CHOICE (2500-5000px) ==========
                # Two paths visible - only one correct based on mode
                {'x': 2450, 'y': base_y-250, 'w': 150, 'type': 'white'},
                {'x': 2700, 'y': base_y-350, 'w': 150, 'type': 'black'},
                # Upper route (black) vs lower route (white) - converge later
                {'x': 3000, 'y': base_y-250, 'w': 200, 'type': 'white'},  # Lower path
                {'x': 2950, 'y': base_y-500, 'w': 200, 'type': 'black'},  # Upper path
                # Convergence
                {'x': 3300, 'y': base_y-350, 'w': 300, 'type': 'neutral'},
                # Triple mode puzzle - must switch twice
                {'x': 3700, 'y': base_y-400, 'w': 180, 'type': 'white'},
                {'x': 3980, 'y': base_y-450, 'w': 180, 'type': 'black'},
                {'x': 4260, 'y': base_y-400, 'w': 180, 'type': 'white'},
                {'x': 4540, 'y': base_y-300, 'w': 300, 'type': 'neutral'},
                
                # ========== SECTION 3: THE TOWER OF DUALITY (5000-8000px) ==========
                # Vertical climb with strategic mode switching
                {'x': 4940, 'y': base_y-400, 'w': 150, 'type': 'black'},
                {'x': 5180, 'y': base_y-550, 'w': 150, 'type': 'white'},
                {'x': 5420, 'y': base_y-700, 'w': 150, 'type': 'black'},
                {'x': 5660, 'y': base_y-850, 'w': 200, 'type': 'neutral'},  # Rest point
                # Horizontal gauntlet at height - think about timing
                {'x': 5960, 'y': base_y-900, 'w': 200, 'type': 'black'},
                {'x': 6260, 'y': base_y-900, 'w': 200, 'type': 'white'},
                {'x': 6560, 'y': base_y-900, 'w': 200, 'type': 'black'},
                # Descent requires opposite mode thinking
                {'x': 6860, 'y': base_y-750, 'w': 180, 'type': 'white'},
                {'x': 7140, 'y': base_y-600, 'w': 180, 'type': 'black'},
                {'x': 7420, 'y': base_y-450, 'w': 180, 'type': 'white'},
                {'x': 7700, 'y': base_y-300, 'w': 300, 'type': 'neutral'},
                
                # ========== SECTION 4: THE MAZE OF MINDS (8000-11000px) ==========
                # Multiple platforms visible - only correct sequence works
                {'x': 8100, 'y': base_y-350, 'w': 150, 'type': 'black'},
                {'x': 8350, 'y': base_y-450, 'w': 150, 'type': 'black'},
                {'x': 8300, 'y': base_y-250, 'w': 120, 'type': 'white'},  # Trap - leads nowhere!
                {'x': 8600, 'y': base_y-550, 'w': 200, 'type': 'neutral'},
                # Staircase illusion - must go up then down
                {'x': 8900, 'y': base_y-650, 'w': 200, 'type': 'white'},
                {'x': 9200, 'y': base_y-800, 'w': 150, 'type': 'black'},
                {'x': 9450, 'y': base_y-650, 'w': 150, 'type': 'white'},  # Drop back down
                {'x': 9700, 'y': base_y-500, 'w': 200, 'type': 'neutral'},
                # The zigzag of fate - few but meaningful
                {'x': 10000, 'y': base_y-600, 'w': 180, 'type': 'black'},
                {'x': 10280, 'y': base_y-450, 'w': 180, 'type': 'white'},
                {'x': 10560, 'y': base_y-350, 'w': 250, 'type': 'neutral'},
                
                # ========== SECTION 5: THE FINAL TRIAL (11000-14000px) ==========
                # Long jumps with mode commitment - no going back
                {'x': 10910, 'y': base_y-450, 'w': 200, 'type': 'white'},
                {'x': 11250, 'y': base_y-550, 'w': 200, 'type': 'black'},
                {'x': 11590, 'y': base_y-450, 'w': 200, 'type': 'white'},
                {'x': 11930, 'y': base_y-350, 'w': 300, 'type': 'neutral'},
                # Rising finale - each jump is a decision
                {'x': 12350, 'y': base_y-500, 'w': 180, 'type': 'black'},
                {'x': 12650, 'y': base_y-650, 'w': 180, 'type': 'white'},
                {'x': 12950, 'y': base_y-800, 'w': 180, 'type': 'black'},
                {'x': 13250, 'y': base_y-950, 'w': 200, 'type': 'neutral'},
                # Last precision challenge - but still strategic (100px platforms)
                {'x': 13580, 'y': base_y-1050, 'w': 100, 'type': 'white'},
                {'x': 13800, 'y': base_y-1150, 'w': 100, 'type': 'black'},
                {'x': 14020, 'y': base_y-1050, 'w': 100, 'type': 'white'},
                
                # ========== VICTORY: THE INNER SANCTUM ==========
                {'x': 14250, 'y': base_y-1000, 'w': 700, 'type': 'neutral'},
            ]
        elif level == "LEVEL_2":
            platforms_data = [
                {'x': 50, 'y': base_y, 'w': 400, 'type': 'neutral'},
                {'x': 600, 'y': base_y-100, 'w': 200, 'type': 'white'},
                {'x': 900, 'y': base_y-200, 'w': 200, 'type': 'black'},
                {'x': 1200, 'y': base_y-300, 'w': 50, 'type': 'neutral'}, 

                #White side
                {'x': 1400, 'y': base_y-400, 'w': 50, 'type': 'white'},
                {'x': 1600, 'y': base_y-500, 'w': 50, 'type': 'white'},
                {'x': 1800, 'y': base_y-600, 'w': 50, 'type': 'white'},
                {'x': 2000, 'y': base_y-600, 'w': 200, 'type': 'white', 'is_slider': True}, # glider 
                {'x': 2300, 'y': base_y-1600, 'w': 200, 'type': 'neutral'},
                {'x': 2500, 'y': base_y-1200, 'w': 2800, 'type': 'neutral'}, # upper platform

                {'x': 2600, 'y': base_y-1500, 'w': 200, 'type': 'white'},
                {'x': 2900, 'y': base_y-1400, 'w': 200, 'type': 'white'},
                {'x': 3200, 'y': base_y-1300, 'w': 500, 'type': 'neutral'},
                {'x': 3700, 'y': base_y-1400, 'w': 50, 'type': 'black'},
                {'x': 3800, 'y': base_y-1430, 'w': 500, 'type': 'neutral'},
                {'x': 3750, 'y': base_y-1550, 'w': 50, 'type': 'white'},
                {'x': 3200, 'y': base_y-1600, 'w': 500, 'type': 'neutral'},
                {'x': 3800, 'y': base_y-1700, 'w': 50, 'type': 'black'},
                {'x': 4000, 'y': base_y-1800, 'w': 500, 'type': 'neutral'},
                {'x': 4500, 'y': base_y-1900, 'w': 200, 'type': 'white'},
                {'x': 4750, 'y': base_y-1750, 'w': 50, 'type': 'white'},
                {'x': 4800, 'y': base_y-1600, 'w': 500, 'type': 'neutral'},
                {'x': 5300, 'y': base_y-1700, 'w': 50, 'type': 'black'},
                {'x': 5400, 'y': base_y-1800, 'w': 50, 'type': 'white'},
                {'x': 5500, 'y': base_y-1550, 'w': 100, 'type': 'white'},
                {'x': 5200, 'y': base_y-1430, 'w': 300, 'type': 'neutral', 'has_spikes': True}, # spiky platform 1
                {'x': 4500, 'y': base_y-1300, 'w': 1050, 'type': 'neutral'},
                {'x': 5640, 'y': base_y-1400, 'w': 200, 'type': 'neutral', 'has_spikes': True}, # spiky platform 2
                {'x': 5680, 'y': base_y-1100, 'w': 100, 'type': 'white'},
                {'x': 5900, 'y': base_y-900, 'w': 100, 'type': 'white'}, 
                {'x': 6100, 'y': base_y-700, 'w': 100, 'type': 'white'}, 

                #Black side
                {'x': 1400, 'y': base_y-200, 'w': 50, 'type': 'black'},
                {'x': 1650, 'y': base_y-0, 'w': 50, 'type': 'black'},
                {'x': 1900, 'y': base_y+100, 'w': 50, 'type': 'black'},
                {'x': 2150, 'y': base_y+200, 'w': 50, 'type': 'black'},
                {'x': 2400, 'y': base_y+300, 'w': 50, 'type': 'black'},
                {'x': 2600, 'y': base_y+300, 'w': 2800, 'type': 'neutral', 'is_mystical': True}, # mystical floor

                # Mystical floor maze
                {'x': 2800, 'y': base_y+300-100, 'w': 200, 'type': 'black'},
                {'x': 3100, 'y': base_y+300-200, 'w': 200, 'type': 'black'},
                {'x': 3400, 'y': base_y+300-300, 'w': 150, 'type': 'white'},
                {'x': 3250, 'y': base_y+300-400, 'w': 150, 'type': 'black'},
                {'x': 2950, 'y': base_y+300-500, 'w': 150, 'type': 'white'},
                {'x': 3250, 'y': base_y+300-600, 'w': 120, 'type': 'black'},
                {'x': 3450, 'y': base_y+300-700, 'w': 200, 'type': 'white'},
                {'x': 3920, 'y': base_y+300-300, 'w': 150, 'type': 'neutral'},
                {'x': 4200, 'y': base_y+300-400, 'w': 150, 'type': 'neutral'},
                {'x': 4400, 'y': base_y+300-200, 'w': 150, 'type': 'black'},
                {'x': 4600, 'y': base_y+300-300, 'w': 50, 'type': 'neutral'},
                {'x': 4720, 'y': base_y+300-400, 'w': 50, 'type': 'black'},
                {'x': 4500, 'y': base_y+300-450, 'w': 200, 'type': 'white'},

                {'x': 4100, 'y': base_y+300-500, 'w': 250, 'type': 'white'},
                {'x': 4420, 'y': base_y+300-600, 'w': 150, 'type': 'black'},
                {'x': 4600, 'y': base_y+300-700, 'w': 20, 'type': 'neutral'},
                {'x': 4700, 'y': base_y+300-800, 'w': 150, 'type': 'white'},
                {'x': 4900, 'y': base_y+300-650, 'w': 80, 'type': 'black'},
                {'x': 5100, 'y': base_y+300-400, 'w': 80, 'type': 'white'},
                {'x': 5300, 'y': base_y+300-250, 'w': 80, 'type': 'black'},
                {'x': 5500, 'y': base_y+300-250, 'w': 400, 'type': 'neutral'},
                {'x': 5900, 'y': base_y+300-250, 'w': 200, 'type': 'neutral', 'is_slider': True, 'slider_range': 450}, # glider 2 
                {'x': 6100, 'y': base_y+300-700, 'w': 1000, 'type': 'neutral'} # end with an enemy gurading the portal
            ]
        else:
            # Fallback to LEVEL_1 layout
            platforms_data = [
                {'x': 50, 'y': base_y, 'w': 500, 'type': 'neutral'},
                {'x': 700, 'y': base_y-100, 'w': 100, 'type': 'white'},
                {'x': 7700, 'y': base_y-200, 'w': 1000, 'type': 'neutral'},
            ]
        
        platforms = []
        spikes = []
        doors = []
        
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
                
            is_slider = p_data.get('is_slider', False)
            is_mystical = p_data.get('is_mystical', False)
            plat = Platform(p_data['x'], p_data['y'], p_data['w'], 30, is_white=is_white, is_neutral=is_neutral, is_slider=is_slider, is_mystical=is_mystical, slider_range=p_data.get('slider_range', 1000))
            platforms.append(plat)
            
        # Portal for levels with transitions
        portal = None
        if level in ["TUTORIAL", "LEVEL_1", "LEVEL_2"]:
            last_plat = platforms_data[-1]
            portal_x = last_plat['x'] + last_plat['w'] - 80  # Near end of last platform
            portal_y = last_plat['y'] - 60  # Above platform
            portal = Portal(portal_x, portal_y)
        elif level == "LEVEL_1":
            # Portal at end of LEVEL_1 to transition to The Inner Sanctum
            last_plat = platforms_data[-1]
            portal_x = last_plat['x'] + last_plat['w'] - 80
            portal_y = last_plat['y'] - 60
            portal = Portal(portal_x, portal_y)
            portal = BlackHole(portal_x, portal_y)
        
        # Spawn Enemies
        enemies = []
        if level == "TUTORIAL":
            # Spawn the ShadowSelf boss on the last platform of tutorial
            last_plat = platforms_data[-1]
            # ShadowSelf is 200x200, so position it centered on platform
            enemy_x = last_plat['x'] + last_plat['w'] // 2 - 100  # Center the 200px wide boss
            enemy_y = last_plat['y'] - 210  # Higher due to 200px height
            enemies = [ShadowSelf(enemy_x, enemy_y)]
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
        else:  # THE INNER SANCTUM
            # Strategic enemy placement - guards at decision points
            enemies = [
                MirrorRonin(3300 + 150, base_y - 350 - 60),  # At convergence point
                MirrorRonin(5660 + 100, base_y - 850 - 60),  # Tower rest point
                MirrorRonin(9700 + 100, base_y - 500 - 60),  # Maze exit
                MirrorRonin(14250 + 350, base_y - 1000 - 60),  # Final boss at sanctum
            ]
        elif level == "LEVEL_2":
            # Spawn enemy guarding the portal (last platform)
            last_plat = platforms_data[-1]
            enemy_x = last_plat['x'] + last_plat['w'] // 2 - 25
            enemy_y = last_plat['y'] - 60
            enemies = [MirrorRonin(enemy_x, enemy_y)]
        
        projectiles = []
        effects = []
        return player, platforms, spikes, projectiles, effects, enemies, portal, doors

    # Level State
    current_level = "TUTORIAL"
    player, platforms, spikes, projectiles, effects, enemies, portal, doors = reset_game(current_level)
    
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

    # Main Game Loop
    running = True
    paused = False
    
    # Death State (NO animation - just instant Game Over)
    game_over = False
    
    def trigger_death():
        nonlocal game_over
        game_over = True
    
    # Tension Mechanics State
    tension_duration = 0.0
    overload_timer = 0.0
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
    
    # Music State
    music_loaded = False
    music_playing = False
    active_music_mode = "LIGHT"  # Track current music mode for transition sounds
    
    # Console State
    console_input = ""
    console_message = ""
    
    # Camera offset for drawing
    camera_offset = (0, 0)
    # Pause Menu State
    paused = False
    menu_state = "PAUSE" # PAUSE, OPTIONS, CONSOLE
    pause_menu_options = ["Continue", "Restart", "Options", "Main Menu"]
    options_menu_options = ["Toggle Fullscreen", "Reticle Sensitivity", "Back"]
    pause_selected = 0  # Currently highlighted option
    
    # Sensitivity setting (1.0 = default, 0.5 = slow, 2.0 = fast)
    reticle_sensitivity = 1.0
    
    # Camera
    # camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    is_fullscreen = settings.get("fullscreen", False)
    
    # --- DYNAMIC RENDER RESOLUTION ---
    # Detect native resolution for fullscreen rendering
    screen_w, screen_h = screen.get_size()
    
    # Scale Factor (1.0 = base resolution)
    scale_factor = 1.0
    if screen_w > SCREEN_WIDTH or screen_h > SCREEN_HEIGHT:
        # Use native resolution
        render_w, render_h = screen_w, screen_h
        scale_factor = screen_w / SCREEN_WIDTH
    else:
        render_w, render_h = SCREEN_WIDTH, SCREEN_HEIGHT
    
    # Surfaces (at render resolution)
    SHAKE_PADDING = int(50 * scale_factor)  # Used for shake amplitude calculation
    canvas = pygame.Surface((render_w, render_h))
    old_screen_capture = pygame.Surface((render_w, render_h))
    next_state_capture = pygame.Surface((render_w, render_h))

    while running:
        dt = clock.tick(FPS) / 1000.0
        
        # --- GAME OVER LOGIC (NO ANIMATION) ---
        if game_over:
            # Input: R to Restart
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                     running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # Restart
                        player, platforms, spikes, projectiles, effects, enemies, portal, doors = reset_game(current_level)
                        game_over = False
                        paused = False
                        tension_duration = 0.0
                        overload_timer = 0.0
                        forced_black_mode_timer = 0.0
                        scroll_x = 0
                        scroll_y = 0
                        transition_active = False


            # Draw "Mind Fractured" Static Background
            half_w = SCREEN_WIDTH // 2
            pygame.draw.rect(screen, CREAM, (0, 0, half_w, SCREEN_HEIGHT))
            pygame.draw.rect(screen, BLACK_MATTE, (half_w, 0, half_w, SCREEN_HEIGHT))
            
            # Text
            font = pygame.font.Font(None, 100)
            
            text_game = font.render("GAME", True, BLACK_MATTE)
            text_rect_g = text_game.get_rect(center=(half_w - 150, SCREEN_HEIGHT/2 - 50))
            screen.blit(text_game, text_rect_g)
            
            text_over = font.render("OVER", True, CREAM)
            text_rect_o = text_over.get_rect(center=(half_w + 150, SCREEN_HEIGHT/2 - 50))
            screen.blit(text_over, text_rect_o)
            
            font_s = pygame.font.Font(None, 40)
            msg = font_s.render("Press R to Restart", True, (150, 150, 150))
            msg_rect = msg.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50))
            screen.blit(msg, msg_rect)
            
            pygame.display.flip()
            continue
        
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
                        player, platforms, spikes, projectiles, effects, enemies, portal, doors = reset_game(current_level)
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
                                    player, platforms, spikes, projectiles, effects, enemies, portal, doors = reset_game(current_level)
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
                                    # Stop all sounds before returning to menu
                                    pygame.mixer.stop()
                                    return "main_menu"
                                    
                            elif menu_state == "OPTIONS":
                                selected_option = options_menu_options[pause_selected]
                                if selected_option == "Toggle Fullscreen":
                                    # Toggle Logic
                                    settings["fullscreen"] = not settings["fullscreen"]
                                    save_settings(settings)
                                    
                                    if settings["fullscreen"]:
                                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                                    else:
                                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0)
                                    
                                    # Recalculate scale_factor and recreate canvas
                                    screen_w, screen_h = screen.get_size()
                                    if screen_w > SCREEN_WIDTH or screen_h > SCREEN_HEIGHT:
                                        render_w, render_h = screen_w, screen_h
                                        scale_factor = screen_w / SCREEN_WIDTH
                                    else:
                                        render_w, render_h = SCREEN_WIDTH, SCREEN_HEIGHT
                                        scale_factor = 1.0
                                    
                                    SHAKE_PADDING = int(50 * scale_factor)
                                    canvas = pygame.Surface((render_w, render_h))
                                    old_screen_capture = pygame.Surface((render_w, render_h))
                                    next_state_capture = pygame.Surface((render_w, render_h))
                                    
                                elif selected_option == "Back":
                                    menu_state = "PAUSE"
                                    pause_selected = 0
                        
                        # Slider Logic (Right/Left)
                        if menu_state == "OPTIONS" and options_menu_options[pause_selected] == "Reticle Sensitivity":
                             if event.key == pygame.K_LEFT:
                                 settings["sensitivity"] = max(0.2, settings["sensitivity"] - 0.1)
                                 reticle_sensitivity = settings["sensitivity"]
                                 save_settings(settings)
                             elif event.key == pygame.K_RIGHT:
                                 settings["sensitivity"] = min(3.0, settings["sensitivity"] + 0.1)
                                 reticle_sensitivity = settings["sensitivity"]
                                 save_settings(settings)
                    
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
                                if splat_sound: splat_sound.play()
            
            # Shooting / Melee Input (Mouse: Left Click) - Only when not paused
            if event.type == pygame.MOUSEBUTTONDOWN and not paused:
                if event.button == 1: # Left Click
                    if player.is_white:
                        # Peace Mode: Shoot
                        proj = player.shoot()
                        if proj:
                            projectiles.append(proj)
                            if splat_sound: splat_sound.play()
                    else:
                        # Tension Mode: Melee
                        new_effects = player.melee_attack()
                        if new_effects:
                            effects.extend(new_effects)
                            if waves_sound: waves_sound.play()
        
        if not paused:
            # --- Audio Crossfade Logic ---
            # Determine target volumes based on state
            target_light = 0.0
            target_dark = 0.0
            
            if player.is_white:
                target_light = TARGET_VOL_LIGHT_MAX
                target_dark = 0.0
            else:
                target_light = 0.0
                target_dark = TARGET_VOL_DARK_MAX
                
                # One-shot transition sound
                # We detect state change by checking if we are moving TO dark from light (i.e. if dark volume is low)
                if current_vol_dark < 0.1 and target_dark > 0.1:
                     # Playing shadow sound only once per switch
                     if shadow_sound and active_music_mode != "DARK":
                         shadow_sound.play()
                         active_music_mode = "DARK" # Reuse this var just for trigger tracking
            
            if player.is_white:
                active_music_mode = "LIGHT"
            
            # Game Over Dimming
            if game_over:
                # Fade to silence
                target_light = 0.0
                target_dark = 0.0
            
            # Lerp volumes (Smooth transition)
            if game_over:
                # Fade to 0 over 2.5s (from max 0.7)
                # Speed = 0.7 / 2.5 = 0.28
                fade_speed = 0.28 * dt
            else:
                # Standard fast switch (approx 0.6s)
                fade_speed = 1.5 * dt 
            
            # Move light volume
            if current_vol_light < target_light:
                current_vol_light = min(target_light, current_vol_light + fade_speed)
            elif current_vol_light > target_light:
                current_vol_light = max(target_light, current_vol_light - fade_speed)
                
            # Move dark volume
            if current_vol_dark < target_dark:
                current_vol_dark = min(target_dark, current_vol_dark + fade_speed)
            elif current_vol_dark > target_dark:
                current_vol_dark = max(target_dark, current_vol_dark - fade_speed)
            
            # Apply volumes
            if bg_chan_light:
                bg_chan_light.set_volume(current_vol_light)
            if bg_chan_dark:
                bg_chan_dark.set_volume(current_vol_dark)

        # ========== LOADING SCREEN HANDLING ==========
        if loading_screen_active:
            loading_timer += dt
            loading_spinner_angle += dt * 5  # Spin the symbol
            
            # Loading screen duration
            loading_duration = 3.0  # 3 seconds
            
            # Draw loading screen
            screen.fill((0, 0, 0))  # Black background
            
            sw, sh = screen.get_size()
            
            # Level title text based on next level
            level_font = pygame.font.Font(None, 120)
            sub_font = pygame.font.Font(None, 40)
            
            if next_level == "LEVEL_1":
                level_title = "LEVEL 1"
                sub_title = "The Journey Begins"
            elif next_level == "INNER_SANCTUM":
                level_title = "THE INNER SANCTUM"
                sub_title = "Face Your Inner Demons"
            else:
                level_title = "LOADING"
                sub_title = ""
            
            level_text = level_font.render(level_title, True, (255, 255, 255))
            level_rect = level_text.get_rect(center=(sw // 2, sh // 4))
            screen.blit(level_text, level_rect)
            
            # Subtitle
            sub_text = sub_font.render(sub_title, True, (150, 150, 150))
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
                player, platforms, spikes, projectiles, effects, enemies, portal, doors = reset_game(current_level)
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
                
                # Update Platforms (Sliders) and move player with them
                for plat in platforms:
                    is_on_top = (player.current_platform == plat)
                    platform_dy = plat.update(is_on_top)
                    
                    # If player is on this slider platform, move them with it
                    if is_on_top and platform_dy != 0:
                        player.y += platform_dy
                
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
                
                # --- Dynamic Heartbeat Logic ---
                if not player.is_white and heartbeat_sound:
                    # Calculate interval based on tension
                    # Range: Tension 0.0 -> ~1.2s
                    #        Tension 12.0 -> ~0.25s (Fast Panic)
                    normalized_tension = min(1.0, tension_duration / 12.0)
                    heartbeat_interval = 1.2 - (normalized_tension * 0.95)
                    
                    heartbeat_timer -= dt
                    if heartbeat_timer <= 0:
                        heartbeat_sound.play()
                        heartbeat_timer = heartbeat_interval
                else:
                    # Reset timer so it starts immediately when switching to dark mode
                    heartbeat_timer = 0.0
                
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
                        if game_over_sound:
                            game_over_sound.play()
                        pygame.mixer.music.set_volume(0.4) # Fade background to 40% on death
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
                
                # Allow negative scroll_y for high platforms
                # if scroll_y < 0: 
                #     scroll_y = 0
                
                camera_offset = (int(scroll_x), int(scroll_y))
                
                # Check spike collision (Standard Spikes)
                for spike in spikes:
                    if spike.get_rect().colliderect(player.get_rect().inflate(-10, -10)):
                        trigger_death()
                        break 
                
                # Check Mystical Platform Spikes
                for plat in platforms:
                    if plat.check_spike_collision(player.get_rect()):
                        trigger_death()
                        break

                # Mouse position
                mouse_pos_canvas = pygame.mouse.get_pos()
                
                # Update player
                player.update(platforms, offset=camera_offset, mouse_pos=mouse_pos_canvas, aim_sensitivity=reticle_sensitivity)
                
                # --- Movement Audio ---
                # 1. Jump Sound
                if player.just_jumped and jump_sound:
                    jump_sound.play()
                
                # 2. Footsteps
                if player.on_ground and abs(player.vel_x) > 0.5:
                    step_timer -= dt
                    if step_timer <= 0:
                        step_timer = step_interval
                        # Play step sound based on mode
                        # Play step sound based on mode
                        if player.is_white:
                            if light_step_sound: light_step_sound.play()
                        else:
                            if dark_step_sound: dark_step_sound.play()
                else:
                    # Reset timer so steps start immediately when walking resumes
                    # But give a tiny delay to avoid "landing step" unless we want landing sounds
                    step_timer = 0.05
                
                # --- CEILING COLLISION (Mystical Platforms) ---
                for plat in platforms:
                    if getattr(plat, 'is_mystical', False) and hasattr(plat, 'ceiling_hit_y'):
                        # Horizontal check
                        if player.x + player.width > plat.x and player.x < plat.x + plat.width:
                            # Vertical check (Head hitting ceiling)
                            # Check strictly if player is overlapping the ceiling line
                            # (Head is above, but Feet are below)
                            if player.y < plat.ceiling_hit_y and (player.y + player.height) > plat.ceiling_hit_y:
                                player.y = plat.ceiling_hit_y
                                if player.vel_y < 0:
                                    player.vel_y = 0 # Head bonk
                
                # Check for void death - instant respawn
                if player.fell_into_void:
                    player, platforms, spikes, projectiles, effects, enemies, portal, doors = reset_game(current_level)
                    tension_duration = 0.0
                    overload_timer = 0.0
                    forced_black_mode_timer = 0.0
                    scroll_x = 0
                    scroll_y = 0
                    transition_active = False
                    blackhole_suction_active = False
                    continue  # Skip rest of update this frame
                
                # Portal Update and Collision
                if portal and not blackhole_suction_active and not loading_screen_active:
                    portal.update(dt)
                    
                    # Check collision
                    if portal.check_collision(player.get_rect()):
                        # Start blackhole suction animation
                        blackhole_suction_active = True
                        blackhole_suction_timer = 0.0
                        blackhole_player_scale = 1.0
                        blackhole_player_rotation = 0.0
                        # Set next level based on current level
                        if current_level == "TUTORIAL":
                            next_level = "LEVEL_1"
                        elif current_level == "LEVEL_1":
                            next_level = "LEVEL_2"
                        else:
                            next_level = "LEVEL_1"  # Fallback
                
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
                    
                    # End suction, do fade transition
                    if blackhole_suction_timer >= blackhole_suction_duration:
                        blackhole_suction_active = False
                        
                        # Get screen dimensions
                        sw, sh = screen.get_size()
                        
                        # === FADE TO BLACK ===
                        for alpha in range(0, 256, 8):
                            overlay = pygame.Surface((sw, sh))
                            overlay.fill((0, 0, 0))
                            overlay.set_alpha(alpha)
                            screen.blit(overlay, (0, 0))
                            pygame.display.flip()
                            clock.tick(60)
                            
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    pygame.quit()
                                    sys.exit()
                        
                        # Full black screen
                        screen.fill((0, 0, 0))
                        pygame.display.flip()
                        
                        # Reset to new level
                        current_level = next_level
                        player, platforms, spikes, projectiles, effects, enemies, portal, doors = reset_game(next_level)
                        tension_duration = 0.0
                        overload_timer = 0.0
                        forced_black_mode_timer = 0.0
                        scroll_x = 0
                        scroll_y = 0
                        transition_active = False
                        
                        # === FADE FROM BLACK ===
                        for alpha in range(255, -1, -8):
                            # Draw new game state
                            bg_color = CREAM if player.is_white else BLACK_MATTE
                            canvas.fill(bg_color)
                            
                            # Draw platforms
                            for plat in platforms:
                                plat.draw(canvas, player.is_white, offset=(0, 0))
                            
                            # Draw portal
                            if portal:
                                portal.draw(canvas, player.is_white, offset=(0, 0))
                            
                            # Draw player
                            player.draw(canvas, offset=(0, 0))
                            
                            screen.blit(canvas, (0, 0))
                            
                            # Draw black overlay with decreasing opacity
                            overlay = pygame.Surface((sw, sh))
                            overlay.fill((0, 0, 0))
                            overlay.set_alpha(alpha)
                            screen.blit(overlay, (0, 0))
                            pygame.display.flip()
                            clock.tick(60)
                            
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    pygame.quit()
                                    sys.exit()
                        
                        continue  # Skip rest of this frame
                
                # Portal (Black Hole) Update and Collision Logic
                level_transition_triggered = False
                for door in doors:
                    door.update(dt)
                    
                    # Check if player collides with portal
                    if door.check_collision(player.get_rect()):
                        # Trigger level transition
                        next_level = door.target_level
                        level_transition_triggered = True
                        
                        # Get screen dimensions
                        sw, sh = screen.get_size()
                        
                        # === SIMPLE FADE TO BLACK ===
                        for alpha in range(0, 256, 8):
                            # Draw black overlay with increasing opacity
                            overlay = pygame.Surface((sw, sh))
                            overlay.fill((0, 0, 0))
                            overlay.set_alpha(alpha)
                            screen.blit(overlay, (0, 0))
                            pygame.display.flip()
                            clock.tick(60)
                            
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    pygame.quit()
                                    sys.exit()
                        
                        # Full black screen for a moment
                        screen.fill((0, 0, 0))
                        pygame.display.flip()
                        
                        # Reset to new level
                        try:
                            # Update current level and reset
                            current_level = next_level
                            player, platforms, spikes, projectiles, effects, enemies, portal, doors = reset_game(next_level)
                            console_message = f"Level {next_level} Loaded"
                        except Exception as e:
                            
                            # Log error to file
                            with open("crash_log.txt", "w") as f:
                                traceback.print_exc(file=f)
                            print(f"CRASH: {e}")
                            console_message = f"Error loading Level {next_level}. Fallback to L1."
                            
                            # Fallback to level 1
                            current_level = 1
                            player, platforms, spikes, projectiles, effects, enemies, portal, doors = reset_game(1)
                        tension_duration = 0.0
                        overload_timer = 0.0
                        forced_black_mode_timer = 0.0
                        scroll_x = 0
                        scroll_y = 0
                        transition_active = False
                        
                        break  # Exit the door loop after handling transition
                
                if level_transition_triggered:
                    continue  # Skip rest of this frame's update
                
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
                             if game_over_sound:
                                 game_over_sound.play()
                             pygame.mixer.music.set_volume(0.4) # Fade background to 40% on death
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
                shake_amp = 20 * total_intensity * scale_factor  # Increased from 10
                
                if overload_timer > 0:
                    shake_amp += overload_timer * 10 * scale_factor  # Increased from 5
                    
                shake_amp += getattr(player, 'shake_intensity', 0) * scale_factor
                
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
                # Standard Draw (apply shake to offset)
                shake_offset = (camera_offset[0] + shake_x, camera_offset[1] + shake_y)
                draw_game(canvas, player.is_white, player, 
                         platforms=platforms, 
                         projectiles=projectiles, 
                         effects=effects, 
                         background=background, 
                         spikes=spikes, 
                         camera=camera, 
                         enemies=enemies, 
                         offset=shake_offset,
                         portal=portal)
                draw_distortion(canvas, intensity)
                


            # Final Blit to Screen with Shake
            # Fill with current BG color to hide borders if shake exposes them
            current_bg = CREAM if player.is_white else BLACK_MATTE
            screen.fill(current_bg) 
            
            # Canvas blits directly, shake applied via camera offset
            screen.blit(canvas, (0, 0))
            
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
                    pygame.draw.rect(canvas, (70, 70, 70), key_rect, border_radius=4)
                    pygame.draw.rect(canvas, (100, 100, 100), key_rect, width=1, border_radius=4)
                    
                    # Key text centered (white)
                    canvas.blit(key_text_surf, (key_rect.x + 8, key_rect.y + 4))
                    
                    # Label text (gray)
                    label_surf = label_font.render(label, True, (150, 150, 150))
                    canvas.blit(label_surf, (key_rect.right + 12, y_pos + 4))
            
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
                pygame.draw.rect(canvas, (70, 70, 70), key_rect, border_radius=4)
                pygame.draw.rect(canvas, (100, 100, 100), key_rect, width=1, border_radius=4)
                
                # Key text centered (white)
                canvas.blit(key_text_surf, (key_rect.x + 8, key_rect.y + 4))
                
                # Label text (gray)
                label_surf = label_font.render(label, True, (150, 150, 150))
                canvas.blit(label_surf, (key_rect.right + 12, y_pos + 4))
            
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
                pygame.draw.rect(canvas, (70, 70, 70), key_rect, border_radius=4)
                pygame.draw.rect(canvas, (100, 100, 100), key_rect, width=1, border_radius=4)
                
                # Key text centered (white)
                canvas.blit(key_text_surf, (key_rect.x + 8, key_rect.y + 4))
                
                # Label text (gray)
                label_surf = label_font.render(label, True, (150, 150, 150))
                canvas.blit(label_surf, (key_rect.right + 12, y_pos + 4))
                 
            # --- PAUSE MENU OVERLAY ---
            if paused:
                # Dim the screen (Use RENDER resolution)
                overlay = pygame.Surface((render_w, render_h), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180)) # Semi-transparent black
                canvas.blit(overlay, (0, 0))
                
                # Draw Menu (Scaled Fonts)
                menu_font = pygame.font.Font(None, int(50 * scale_factor))
                title_font = pygame.font.Font(None, int(80 * scale_factor))
                
                # Title
                title_text = "PAUSED" if menu_state == "PAUSE" else "OPTIONS"
                title_surf = title_font.render(title_text, True, WHITE)
                canvas.blit(title_surf, (render_w//2 - title_surf.get_width()//2, 150))
                
                # Options
                options_to_draw = pause_menu_options if menu_state == "PAUSE" else options_menu_options
                
                start_y = 250
                gap_y = 60
                
                for i, option in enumerate(options_to_draw):
                    color = WHITE
                    text = option
                    
                    # Special handling for sensitivity display
                    if option == "Reticle Sensitivity":
                        text = "Reticle Sensitivity"
                    
                    # Special handling for centering controls: Skip default draw for these options
                    if option in ["Toggle Fullscreen", "Reticle Sensitivity"]:
                         pass
                    elif i == pause_selected:
                        # Selected: White Background, Black Text (like Main Menu)
                        text_surf = menu_font.render(text, True, BLACK_MATTE)
                        text_rect = text_surf.get_rect(center=(render_w//2, start_y + i * gap_y))
                        
                        # Draw Selection Box
                        bg_rect = text_rect.inflate(40, 20)
                        pygame.draw.rect(canvas, WHITE, bg_rect)
                        
                        # Draw Text
                        canvas.blit(text_surf, text_rect)
                    else:
                        # Unselected: White Text
                        text_surf = menu_font.render(text, True, WHITE)
                        text_rect = text_surf.get_rect(center=(render_w//2, start_y + i * gap_y))
                        canvas.blit(text_surf, text_rect)
                    
                    # --- Draw Extra UI Elements for Options ---
                    if menu_state == "OPTIONS":
                        base_y = start_y + i * gap_y
                        
                        # Fullscreen Toggle
                        if option == "Toggle Fullscreen":
                            # Toggle Switch UI
                            switch_w = 60 * scale_factor
                            switch_h = 30 * scale_factor
                            
                            # Calculate dynamic centering
                            # Render the text here to get its width for centering
                            text_surf_s = menu_font.render(option, True, WHITE) # Use original option text for width calc
                            text_w = text_surf_s.get_width()
                            total_w = text_w + 40 * scale_factor + switch_w # Text width + gap + switch width
                            start_x = render_w // 2 - total_w // 2
                            
                            # Draw Text at start_x
                            text_rect = text_surf_s.get_rect(topleft=(start_x, base_y - text_surf_s.get_height()//2))
                            
                            if i == pause_selected:
                                # Selected styling: Highlight covers the entire unified row
                                total_row_rect = pygame.Rect(start_x, base_y - 25 * scale_factor, total_w, 50 * scale_factor)
                                pygame.draw.rect(canvas, WHITE, total_row_rect)
                                
                                # Black Text on White
                                text_surf_s = menu_font.render(option, True, BLACK_MATTE)
                                canvas.blit(text_surf_s, text_rect)
                            else:
                                text_surf_s = menu_font.render(option, True, WHITE)
                                canvas.blit(text_surf_s, text_rect)

                            switch_x = start_x + text_w + 40 * scale_factor
                            switch_y = base_y - switch_h // 2
                            
                            switch_rect = pygame.Rect(switch_x, switch_y, switch_w, switch_h)
                            
                            # Determine state (settings dict or is_fullscreen var)
                            # Note: is_fullscreen variable might not be updated in real-time, checking settings dict is safer if available
                            # core.py usually has 'settings' dict available globally or current state
                            
                            is_fs = settings.get("fullscreen", False)
                            
                            if i == pause_selected:
                                # Selected (White Background): Use Black/Dark elements
                                if is_fs:
                                     # ON: Filled Black, White Knob
                                    pygame.draw.rect(canvas, BLACK_MATTE, switch_rect, border_radius=int(15 * scale_factor))
                                    pygame.draw.circle(canvas, WHITE, (switch_x + switch_w - 15 * scale_factor, switch_y + 15 * scale_factor), 12 * scale_factor)
                                else:
                                     # OFF: Black Outline, Black Knob
                                    pygame.draw.rect(canvas, BLACK_MATTE, switch_rect, 2, border_radius=int(15 * scale_factor))
                                    pygame.draw.circle(canvas, BLACK_MATTE, (switch_x + 15 * scale_factor, switch_y + 15 * scale_factor), 10 * scale_factor)
                            else:
                                # Unselected (Black Background): Use White elements
                                if is_fs:
                                    # ON State: Filled White
                                    pygame.draw.rect(canvas, WHITE, switch_rect, border_radius=int(15 * scale_factor))
                                    # Knob: Black, Right Side
                                    knob_radius = 12 * scale_factor
                                    pygame.draw.circle(canvas, BLACK_MATTE, (switch_x + switch_w - 15 * scale_factor, switch_y + 15 * scale_factor), knob_radius)
                                else:
                                    # OFF State: Outline White
                                    pygame.draw.rect(canvas, WHITE, switch_rect, 2, border_radius=int(15 * scale_factor))
                                    # Knob: White, Left Side
                                    knob_radius = 10 * scale_factor
                                    pygame.draw.circle(canvas, WHITE, (switch_x + 15 * scale_factor, switch_y + 15 * scale_factor), knob_radius)

                        # Sensitivity Slider
                        elif option == "Reticle Sensitivity":
                            # Draw Slider Bar
                            slider_width = 200 * scale_factor
                            
                            # Calculate dynamic centering
                            # Render the text here to get its width for centering
                            display_text = "Reticle Sensitivity"
                            text_surf_s = menu_font.render(display_text, True, WHITE)
                            text_w = text_surf_s.get_width()
                            val_surf = menu_font.render(f"{settings.get('sensitivity', 1.0):.1f}", True, WHITE)
                            val_w = val_surf.get_width()
                            total_w = text_w + 40 * scale_factor + slider_width + 40 * scale_factor + val_w # Text + gap + slider + gap + value
                            start_x = render_w // 2 - total_w // 2
                            
                            # Draw Text at start_x
                            text_rect = text_surf.get_rect(topleft=(start_x, base_y - text_surf.get_height()//2))

                            knob_color = WHITE
                            slider_bg_color = (100, 100, 100) # Gray

                            if i == pause_selected:
                                # Selected styling: Highlight covers the entire unified row
                                total_row_rect = pygame.Rect(start_x, base_y - 25 * scale_factor, total_w, 50 * scale_factor)
                                pygame.draw.rect(canvas, WHITE, total_row_rect)
                                
                                text_surf_s = menu_font.render(text, True, BLACK_MATTE)
                                canvas.blit(text_surf_s, text_rect)
                                
                                # Value text also needs to be black if highlighted
                                val_surf = menu_font.render(f"{settings.get('sensitivity', 1.0):.1f}", True, BLACK_MATTE)
                                
                                knob_color = BLACK_MATTE
                                slider_bg_color = (180, 180, 180) # Lighter gray for contrast? Or keep gray.
                            else:
                                text_surf_s = menu_font.render(text, True, WHITE)
                                canvas.blit(text_surf_s, text_rect)
                                val_surf = menu_font.render(f"{settings.get('sensitivity', 1.0):.1f}", True, WHITE)
                            
                            slider_x = start_x + text_w + 40 * scale_factor
                            slider_y = base_y
                            
                            # Background Line
                            pygame.draw.rect(canvas, slider_bg_color, (slider_x, slider_y, slider_width, 4 * scale_factor))
                            
                            # Handle Knob
                            # Range 0.2 to 3.0
                            val = settings.get("sensitivity", 1.0)
                            normalized = (val - 0.2) / (3.0 - 0.2)
                            knob_x = slider_x + float(normalized * slider_width)
                            
                            pygame.draw.circle(canvas, knob_color, (int(knob_x), int(slider_y + 2 * scale_factor)), 10 * scale_factor)
                            
                            # Draw Value Text
                            canvas.blit(val_surf, (slider_x + slider_width + 40 * scale_factor, slider_y - 15 * scale_factor))

                    continue # Skip default draw

        elif game_over:
            # Game Over State (Pixel Crumble)
            if crumble_effect is None:
                crumble_effect = CrumbleEffect(canvas)
            
            crumble_effect.update()
            crumble_effect.draw(canvas)
        
        # --- Final Presentation ---
        # Scale canvas to actual screen size (Native Fullscreen Support)
        target_size = screen.get_size()
        if target_size != (SCREEN_WIDTH, SCREEN_HEIGHT):
            pygame.transform.smoothscale(canvas, target_size, screen)
        else:
            screen.blit(canvas, (0,0))
            
        pygame.display.flip()
    
    return "quit"
