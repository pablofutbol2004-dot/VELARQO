# RESPONSIVE REEL SAFE-ZONE SYSTEM

When designing vertical video, do NOT assume a fixed resolution such as 1080×1920.

Treat the canvas as:

W = total canvas width
H = total canvas height

All positioning, margins, safe zones, typography, and composition should scale relative to W and H.

## 1. Understand what "safe" means

Social platforms place interface elements over the video:
- account/header information near the top
- captions, description, audio information, navigation, etc. near the bottom
- like/comment/share/profile controls along the right side
- occasional platform-specific overlays elsewhere

Therefore divide the canvas into:

### A. BLEED ZONE
The entire canvas. Backgrounds, textures, photos, gradients, decorative shapes, ambient motion, and non-essential visual elements may occupy this area.

### B. CONTENT-SAFE ZONE
The region where important information should normally live.

Conservative default for a vertical short-form video:
- left boundary: ~6% of W
- right boundary: ~82–86% of W
- top boundary: ~10–13% of H
- bottom boundary: ~76–80% of H

Equivalent approximate safe rectangle:
x = 0.06W → 0.84W
y = 0.11H → 0.78H

These are GUIDELINES, not immutable coordinates. Adjust them according to: platform, aspect ratio, interface layout, whether captions are visible, content type, importance of the element, and actual preview/safe-area metadata if available.

## 2. Reserve interface-risk zones

Unless better platform-specific information is available, assume approximately:

TOP UI RISK = top 8–13% of H
BOTTOM UI RISK = bottom 18–24% of H
RIGHT UI RISK = rightmost 10–16% of W
LEFT EDGE MARGIN = leftmost 4–7% of W

Do NOT place essential text, logos, faces, buttons, numbers, product information, diagrams, or important focal details in these areas. Background imagery may extend through them.

## 3. Use importance-dependent safety

### CRITICAL — hook/headline, subtitles, CTA, price, important numbers, logos when identification matters, diagrams, UI that must be read, faces when expression matters → keep completely inside the content-safe zone.

### IMPORTANT — supporting copy, secondary graphics, supporting product details → prefer the content-safe zone; minor overlap with peripheral zones may be acceptable.

### DECORATIVE — backgrounds, texture, lighting, particles, oversized typography used as texture, abstract forms, secondary imagery → may intentionally extend into unsafe areas or beyond the canvas.

The goal is NOT to cram the whole design into a rectangle. The safe zone protects INFORMATION, not aesthetics.

## 4. Create a visual hierarchy inside the safe zone

Place the strongest focal point roughly around x = 35–55% of W, y = 30–50% of H. Do not automatically center everything. The right side usually carries platform controls, so compositions can often benefit from a slight LEFT bias. Example: subject slightly left of center; text left/center; environmental space extending toward the right; decorative elements allowed behind the UI.

## 5. Caption-safe region

Reserve a predictable caption band when subtitles are required:
x = 8–82% of W, y = approximately 58–76% of H. Captions should normally sit ABOVE the platform's bottom interface rather than at the physical bottom. Avoid extremely wide subtitle lines, text touching right-side action buttons, subtitles extending into description/audio/navigation areas. Aim for roughly 1–2 lines at once, strong contrast, comfortable horizontal padding. Move subtitles upward when the platform UI is unusually tall.

## 6. Adapt by content type

### TALKING HEAD — protect eyes, mouth, expression, captions; face central or slightly left-central; body may extend into bottom UI area.
### TEXT-LED / EDUCATIONAL REEL — keep headline, key points, statistics, diagrams, captions inside the safe region; use the rest for illustration/photography/decorative type/motion; do not make every text block full width.
### MOTION GRAPHICS — principal message must stay readable in the safe zone; objects may enter/exit through unsafe zones; animations may cross UI areas if the information remains understandable; final resting positions of important elements should usually be safe.
### PRODUCT / OBJECT VIDEO — object may extend outside safe zone; keep the feature being demonstrated inside it.
### SCREEN RECORDING / SOFTWARE DEMO — readable interface = critical info; crop/zoom/reframe so the active interaction is not hidden by controls; do not shrink the whole screen; zoom toward the discussed info.
### CINEMATIC / B-ROLL — safe-zone restrictions much looser; protect faces/essential info; do not sacrifice composition to keep every object inside the rectangle.

## 7. Adapt to arbitrary resolutions

Never write rules like "x = 100 pixels" or "CTA at y = 1500 px". Calculate from dimensions:

safe_left = W × 0.06
safe_right = W × 0.84
safe_top = H × 0.11
safe_bottom = H × 0.78

For 1080×1920 this yields ≈ 65px / 907px / 211px / 1498px; the same composition scales automatically.

## 8. Adapt to aspect ratio

Determine aspect ratio before designing. ~9:16 → vertical-video rules above. Taller/narrower → increase horizontal protection, avoid extremely wide typography. Wider → do not blindly reuse the 9:16 rectangle; recalculate while preserving UI exclusion zones. When exact platform overlays are known, PLATFORM-SPECIFIC DATA OVERRIDES THE GENERIC PERCENTAGES.

## 9. Use nested safety levels

LEVEL 1 — ULTRA SAFE: central ~60–65% of canvas; use for the single most important information.
LEVEL 2 — NORMAL SAFE: x 6–84%, y 11–78%; use for ordinary information.
LEVEL 3 — FULL BLEED: entire canvas; use for visual composition and non-critical content.

This prevents every design from becoming a small box floating in the middle.

## 10. Final validation

Verify: 1) main hook readable with UI visible; 2) subtitles unobstructed; 3) nothing important under right-side controls; 4) nothing important too close to top; 5) nothing hidden behind bottom captions/navigation/audio UI; 6) design still uses the FULL canvas visually; 7) excessive caution hasn't weakened the composition; 8) composition survives minor device/UI differences; 9) focal points protected rather than every decorative object; 10) if a platform preview exists, validate against the actual overlay.

CORE PRINCIPLE:

"FULL BLEED FOR VISUALS. SAFE ZONES FOR INFORMATION."

Safe zones are risk-management constraints, not rigid design boxes. Compose freely across the whole canvas while protecting anything the viewer must see, read, recognize, or interact with.

