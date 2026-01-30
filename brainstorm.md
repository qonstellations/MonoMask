# MonoMask: Brainstorming & Roadmap

## 🧠 Narrative: "The Architecture of Self"

**Theme**: Mental Health & Internal Duality.
**Concept**: The game doesn't take place in a dungeon, but inside a *mind*.
*   **White Mode (The Persona)**: Represents how we want to be seen—bright, polished, perfectionist. But it can be blinding and superficial (you fall through "deep" things).
*   **Black Mode (The Shadow)**: Represents our fears, doubts, and suppressed emotions. It feels heavy, but it offers substance and grounding (solid platforms where White finds none).
*   **The Goal**: You are not trying to escape. You are trying to reach **Integration** (The Neutral State). The "Goal" at the end of the level is a memory or a moment of clarity.

**Narrative Delivery**:
*   **Floating Text**: Instead of signs, thoughts appear in the background.
    *   *White Mode thought*: "Everything is fine."
    *   *Black Mode thought*: "I am empty."
*   **The Ending**: You don't win by defeating a boss. You win by fusing the two masks into a single, grey/gold joyful face.

---

## 🚀 Gameplay Features to Add

### 1. "Memory Shards" (Collectibles)
*   Scattered throughout the level.
*   **Mechanic**: Some are only visible/collectable in White, some in Black.
*   **Reward**: Unlocks a sentence of the story.

### 2. "Echo Blocks" (Time/Space Mechanic)
*   **Mechanic**: Blocks that only exist for 2 seconds *after* a swap.
*   **Purpose**: Forces rapid switching and rhythmic play.

### 3. "The Observer" (Enemy/Hazard)
*   A giant eye in the background.
*   **Mechanic**: If you stay in one mode too long, the eye opens and drains your health/sanity. Encourages balance.

### 4. Dynamic Music (Audio)
*   **White Layer**: Harp/Piano (Light, airy).
*   **Black Layer**: Bass/Synth (Deep, heavy).
*   **Concept**: Both tracks play constantly, but volume crossfades when you swap. They harmonize perfectly.

---

## 💎 Polish & Improvements (Double Down)

### 1. "Juice" the Transition
*   The expanding circle is great. Add a **time-dilation effect** (slow motion) for 0.2s during the swap to give the player time to adjust.
*   Add **Screenshake** when landing on a "heavy" (Black) platform.

### 2. Movement Tech
*   **Coyote Time**: Allow jumping for a few frames after walking off a ledge.
*   **Jump Buffering**: Remember jump inputs pressed just before hitting the ground.
*   *Essential for making the platforming feel "fair".*

### 3. Visual Storytelling
*   **Backgrounds**:
    *   **Minimalist & Abstract**: No clouds or stars. Pure, solid colors or subtle gradients.
    *   **White Mode**: Soft Cream/Off-White. Clean, stark, "Empty".
    *   **Black Mode**: Soft Matte Black. Deep, absorbing, "Heavy".
    *   **Contrast**: rely on the geometry and the text to tell the story, not environment art.

---

## 🎯 Recommended Next Steps
1.  **Implement Text/Narrative System**: Add floating text that changes based on mode.
2.  **Add Collectibles**: Gives a reason to explore.
3.  **Refine Movement**: Add Coyote Time/Jump Buffer (Crucial for "Game Feel").
