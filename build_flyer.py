#!/usr/bin/env python3
"""
SkyBand / 4PR Aerial Solutions — Professional Giveaway Flyer Generator
Produces skyband_flyer.png and skyband_flyer.pdf at 300 DPI (2550×3300 px)
"""

import math
from PIL import Image, ImageDraw, ImageFont

# ── Canvas ────────────────────────────────────────────────────────────────────
DPI = 300
W, H = int(8.5 * DPI), int(11 * DPI)   # 2550 × 3300

# ── Brand Palette ─────────────────────────────────────────────────────────────
SKY      = (74,  144, 226)   # #4A90E2
OCEAN    = (46,   92, 138)   # #2E5C8A
DEEP     = (20,   45,  80)   # deep navy
SAND     = (212, 165, 116)   # #D4A574
GOLD     = (255, 184,  77)   # #FFB84D
WHITE    = (255, 255, 255)
OFF_WHT  = (245, 248, 255)
LTBLUE   = (180, 215, 250)
DARK_TXT = (15,  35,  65)
MID_BLUE = (60, 110, 175)

# ── Font Paths ────────────────────────────────────────────────────────────────
FONT_DIR   = "/usr/share/fonts/truetype/liberation/"
FONT_BOLD  = FONT_DIR + "LiberationSans-Bold.ttf"
FONT_REG   = FONT_DIR + "LiberationSans-Regular.ttf"
FONT_BITAL = FONT_DIR + "LiberationSans-BoldItalic.ttf"

def F(size, bold=False, italic=False):
    path = FONT_BITAL if (bold and italic) else (FONT_BOLD if bold else FONT_REG)
    return ImageFont.truetype(path, size)


def centered_x(draw, text, font, y, color, img_width=W):
    """Draw text horizontally centered."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((img_width - tw) // 2, y), text, font=font, fill=color)


def draw_rounded_rect(draw, x0, y0, x1, y1, r, fill, outline=None, width=3):
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill,
                            outline=outline, width=width)


# ─────────────────────────────────────────────────────────────────────────────
#  BACKGROUND: layered sky gradient
# ─────────────────────────────────────────────────────────────────────────────
img = Image.new("RGB", (W, H), DEEP)
draw = ImageDraw.Draw(img)

# Sky gradient: deep navy → sky blue → pale sky
gradient_stops = [
    (0,        DEEP),
    (0.35,     OCEAN),
    (0.62,     SKY),
    (0.78,     LTBLUE),
    (1.0,      OFF_WHT),
]
for y in range(H):
    t = y / H
    # find surrounding stops
    c0 = gradient_stops[0][1]; c1 = gradient_stops[-1][1]
    for i in range(len(gradient_stops) - 1):
        t0, rgb0 = gradient_stops[i]
        t1, rgb1 = gradient_stops[i + 1]
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0)
            c0 = tuple(int(rgb0[j] + f * (rgb1[j] - rgb0[j])) for j in range(3))
            break
    draw.line([(0, y), (W, y)], fill=c0)


# ─────────────────────────────────────────────────────────────────────────────
#  OCEAN WAVE BANDS (decorative bottom strips)
# ─────────────────────────────────────────────────────────────────────────────
def draw_wave(draw, y_base, amplitude, wavelength, color, thickness=18):
    pts = []
    for x in range(0, W + 1, 4):
        y = y_base + int(amplitude * math.sin(2 * math.pi * x / wavelength))
        pts.append((x, y))
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        draw.line([(x0, y0), (x1, y1)], fill=color, width=thickness)

wave_base = int(H * 0.84)
draw_wave(draw, wave_base,        22, 520, (*OCEAN, 130),   thickness=40)
draw_wave(draw, wave_base + 28,   18, 480, (*SKY,   100),   thickness=28)
draw_wave(draw, wave_base + 50,   14, 440, (*LTBLUE, 90),   thickness=20)


# ─────────────────────────────────────────────────────────────────────────────
#  HEADER PANEL  (top dark strip)
# ─────────────────────────────────────────────────────────────────────────────
hdr_h = 210
draw_rounded_rect(draw, 0, 0, W, hdr_h + 40, r=0, fill=DEEP)
# subtle bottom glow line under header
for i in range(6):
    alpha_c = tuple(int(c * (0.7 - i * 0.1)) for c in SKY)
    draw.line([(0, hdr_h + i), (W, hdr_h + i)], fill=(*SKY, max(0, 180 - i * 30)), width=2)

# Gold accent bar across top
draw.rectangle([0, 0, W, 12], fill=GOLD)

# Logo / company name
logo_font = F(64, bold=True)
centered_x(draw, "SKYBAND  /  4PR AERIAL SOLUTIONS", logo_font, 30, WHITE)

# Thin rule under logo
rule_y = 115
draw.rectangle([80, rule_y, W - 80, rule_y + 3], fill=GOLD)

# Tagline in header
tag_font = F(34, bold=False, italic=False)
centered_x(draw, "PROFESSIONAL AERIAL PHOTOGRAPHY  •  NORTH CAROLINA", tag_font, 128, LTBLUE)

# Gold bottom accent bar of header
draw.rectangle([0, hdr_h + 30, W, hdr_h + 42], fill=GOLD)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN HEADLINE BANNER
# ─────────────────────────────────────────────────────────────────────────────
banner_y   = hdr_h + 60
banner_bot = banner_y + 230

# Starburst / spotlight glow behind text
cx, cy = W // 2, banner_y + 100
for r in range(280, 0, -4):
    alpha = int(38 * (1 - r / 280))
    draw.ellipse([cx - r, cy - r // 2, cx + r, cy + r // 2],
                 fill=(*GOLD, alpha))

# Headline text — shadow then fill
hl_font = F(148, bold=True)
hl_text = "FREE AERIAL"
bbox = draw.textbbox((0, 0), hl_text, font=hl_font)
tw = bbox[2] - bbox[0]
tx = (W - tw) // 2
draw.text((tx + 5, banner_y + 8),  hl_text, font=hl_font, fill=(0, 0, 0, 60))
draw.text((tx,     banner_y),      hl_text, font=hl_font, fill=GOLD)

hl2_font = F(148, bold=True)
hl2_text = "DRONE PACKAGE"
bbox2 = draw.textbbox((0, 0), hl2_text, font=hl2_font)
tw2 = bbox2[2] - bbox2[0]
tx2 = (W - tw2) // 2
draw.text((tx2 + 5, banner_y + 148), hl2_text, font=hl2_font, fill=(0, 0, 0, 60))
draw.text((tx2,     banner_y + 140), hl2_text, font=hl2_font, fill=WHITE)


# ─────────────────────────────────────────────────────────────────────────────
#  DRONE SVG-STYLE SILHOUETTE  (drawn with PIL primitives)
# ─────────────────────────────────────────────────────────────────────────────
def draw_drone(draw, cx, cy, scale=1.0, color=WHITE, shadow_color=(0,0,0,80)):
    s = scale

    def arm(angle_deg, length=200, w=18):
        angle = math.radians(angle_deg)
        x1 = cx + int(30 * s * math.cos(angle))
        y1 = cy + int(30 * s * math.sin(angle))
        x2 = cx + int(length * s * math.cos(angle))
        y2 = cy + int(length * s * math.sin(angle))
        # shadow
        draw.line([(x1+4, y1+4), (x2+4, y2+4)], fill=shadow_color, width=int(w * s))
        draw.line([(x1, y1), (x2, y2)], fill=color, width=int(w * s))

    def motor(angle_deg, arm_len=200):
        angle = math.radians(angle_deg)
        mx = cx + int(arm_len * s * math.cos(angle))
        my = cy + int(arm_len * s * math.sin(angle))
        r = int(32 * s)
        draw.ellipse([mx - r, my - r, mx + r, my + r], fill=shadow_color)
        draw.ellipse([mx - r + 4, my - r + 4, mx + r - 4, my + r - 4],
                     outline=color, width=int(8 * s))

    def propeller(angle_deg, arm_len=200):
        angle = math.radians(angle_deg)
        mx = cx + int(arm_len * s * math.cos(angle))
        my = cy + int(arm_len * s * math.sin(angle))
        pr = int(80 * s)
        pa = int(14 * s)
        # two blades rotated 90° from the arm angle
        perp = angle + math.pi / 2
        bx1 = mx + int(pr * math.cos(perp))
        by1 = my + int(pr * math.sin(perp))
        bx2 = mx - int(pr * math.cos(perp))
        by2 = my - int(pr * math.sin(perp))
        # shadow
        draw.line([(bx2+3, by2+3), (bx1+3, by1+3)], fill=shadow_color, width=pa)
        draw.line([(bx2, by2), (bx1, by1)], fill=color, width=pa)
        # second blade pair rotated 45°
        perp2 = angle + math.pi / 4
        bx3 = mx + int(pr * 0.8 * math.cos(perp2))
        by3 = my + int(pr * 0.8 * math.sin(perp2))
        bx4 = mx - int(pr * 0.8 * math.cos(perp2))
        by4 = my - int(pr * 0.8 * math.sin(perp2))
        draw.line([(bx4+3, by4+3), (bx3+3, by3+3)], fill=shadow_color, width=pa)
        draw.line([(bx4, by4), (bx3, by3)], fill=color, width=pa)

    # four arms at 45°, 135°, 225°, 315°
    for a in [45, 135, 225, 315]:
        arm(a)
        motor(a)
        propeller(a)

    # central body
    bw, bh = int(90 * s), int(50 * s)
    draw.rounded_rectangle([cx - bw, cy - bh, cx + bw, cy + bh],
                            radius=int(20 * s), fill=shadow_color)
    draw.rounded_rectangle([cx - bw + 4, cy - bh + 4, cx + bw - 4, cy + bh - 4],
                            radius=int(18 * s), fill=color)
    # camera dome
    cam_r = int(24 * s)
    draw.ellipse([cx - cam_r, cy + bh - 10, cx + cam_r, cy + bh + cam_r * 2],
                 fill=OCEAN)
    draw.ellipse([cx - cam_r + 6, cy + bh - 4, cx + cam_r - 6, cy + bh + cam_r * 2 - 6],
                 fill=SKY)
    # lens glint
    draw.ellipse([cx - 6, cy + bh + 6, cx + 6, cy + bh + 18], fill=WHITE)

    # LED dots on body
    for lx, ly in [(-40, -8), (0, -8), (40, -8)]:
        draw.ellipse([cx + int(lx * s) - 5, cy + int(ly * s) - 5,
                      cx + int(lx * s) + 5, cy + int(ly * s) + 5],
                     fill=GOLD)


drone_cx = W // 2
drone_cy = int(H * 0.47)
draw_drone(draw, drone_cx, drone_cy, scale=1.55,
           color=WHITE, shadow_color=(10, 30, 60, 100))


# ─────────────────────────────────────────────────────────────────────────────
#  "6 PROFESSIONAL AERIAL PHOTOS" badge
# ─────────────────────────────────────────────────────────────────────────────
offer_y = int(H * 0.615)
draw_rounded_rect(draw, 160, offer_y, W - 160, offer_y + 110,
                  r=55, fill=OCEAN, outline=SKY, width=4)

offer_font = F(62, bold=True)
centered_x(draw, "6 PROFESSIONAL AERIAL PHOTOS", offer_font, offer_y + 22, WHITE)


# ─────────────────────────────────────────────────────────────────────────────
#  SUBHEADLINE + bullets
# ─────────────────────────────────────────────────────────────────────────────
sub_y = int(H * 0.695)

sub1_font = F(56, bold=True, italic=True)
centered_x(draw, "LIMITED TIME GIVEAWAY", sub1_font, sub_y, GOLD)

sub2_font = F(46, bold=False)
centered_x(draw, "Showcase Your Property From Above", sub2_font, sub_y + 80, WHITE)

# Divider dots
dot_y = sub_y + 148
for i, x in enumerate(range(W // 2 - 120, W // 2 + 121, 40)):
    r = 8 if i == 3 else 5
    c = GOLD if i == 3 else LTBLUE
    draw.ellipse([x - r, dot_y - r, x + r, dot_y + r], fill=c)


# ─────────────────────────────────────────────────────────────────────────────
#  VALUE BADGE  "$300+ VALUE • FREE"
# ─────────────────────────────────────────────────────────────────────────────
badge_y = int(H * 0.764)
bx0, bx1 = W // 2 - 390, W // 2 + 390
bbot = badge_y + 150

# Outer glow rings
for i in range(4):
    pad = i * 6
    draw.rounded_rectangle([bx0 - pad, badge_y - pad, bx1 + pad, bbot + pad],
                            radius=75 + pad, fill=None,
                            outline=(*GOLD, max(0, 80 - i * 20)), width=3)

draw_rounded_rect(draw, bx0, badge_y, bx1, bbot,
                  r=75, fill=GOLD, outline=WHITE, width=5)

val_font  = F(90, bold=True)
val_text  = "$300+ VALUE"
bbox_v = draw.textbbox((0, 0), val_text, font=val_font)
tw_v   = bbox_v[2] - bbox_v[0]
draw.text(((W - tw_v) // 2 + 3, badge_y + 16), val_text, font=val_font, fill=(100, 60, 0))
draw.text(((W - tw_v) // 2,     badge_y + 13), val_text, font=val_font, fill=DEEP)

free_font = F(68, bold=True)
free_text = "★  COMPLETELY FREE  ★"
bbox_f = draw.textbbox((0, 0), free_text, font=free_font)
tw_f   = bbox_f[2] - bbox_f[0]
draw.text(((W - tw_f) // 2 + 2, badge_y + 94), free_text, font=free_font, fill=(100, 60, 0))
draw.text(((W - tw_f) // 2,     badge_y + 91), free_text, font=free_font, fill=DEEP)


# ─────────────────────────────────────────────────────────────────────────────
#  WAVE SEPARATOR  between body and footer
# ─────────────────────────────────────────────────────────────────────────────
sep_y = int(H * 0.865)
# Fill sandy band
draw.rectangle([0, sep_y - 8, W, H], fill=DEEP)
draw_wave(draw, sep_y, 20, 600, OCEAN, thickness=36)
draw_wave(draw, sep_y - 14, 16, 460, SKY, thickness=18)
draw.rectangle([0, sep_y + 30, W, H], fill=DEEP)


# ─────────────────────────────────────────────────────────────────────────────
#  FOOTER  contact info panel
# ─────────────────────────────────────────────────────────────────────────────
footer_y = sep_y + 36
draw.rectangle([0, footer_y, W, H], fill=DEEP)

# Gold rule at top of footer
draw.rectangle([60, footer_y + 2, W - 60, footer_y + 6], fill=GOLD)

# Company name in footer
co_font = F(52, bold=True)
centered_x(draw, "SkyBand / 4PR Aerial Solutions", co_font, footer_y + 20, GOLD)

# Contact details
c1_font = F(46, bold=False)
c2_font = F(42, bold=True)

centered_x(draw, "☎  984 810 7950", c1_font, footer_y + 90, WHITE)
centered_x(draw, "@SkyBandLegacyMedia", c2_font, footer_y + 150, LTBLUE)

cta_font = F(40, bold=True, italic=True)
centered_x(draw, "DM or Call for Information", cta_font, footer_y + 210, SAND)

# Bottom gold bar
draw.rectangle([0, H - 14, W, H], fill=GOLD)


# ─────────────────────────────────────────────────────────────────────────────
#  CORNER DECORATIONS  (gold bracket accents)
# ─────────────────────────────────────────────────────────────────────────────
def corner_bracket(draw, x, y, flip_x=False, flip_y=False, size=90, t=8, color=GOLD):
    sx = -1 if flip_x else 1
    sy = -1 if flip_y else 1
    # horizontal bar
    x0h, x1h = sorted([x, x + sx * size])
    y0h, y1h = sorted([y, y + sy * t])
    draw.rectangle([x0h, y0h, x1h, y1h], fill=color)
    # vertical bar
    x0v, x1v = sorted([x, x + sx * t])
    y0v, y1v = sorted([y, y + sy * size])
    draw.rectangle([x0v, y0v, x1v, y1v], fill=color)

m = 28
corner_bracket(draw, m, m)
corner_bracket(draw, W - m, m, flip_x=True)
corner_bracket(draw, m, H - m, flip_y=True)
corner_bracket(draw, W - m, H - m, flip_x=True, flip_y=True)


# ─────────────────────────────────────────────────────────────────────────────
#  SMALL STARS / sparkles scattered around drone area
# ─────────────────────────────────────────────────────────────────────────────
def sparkle(draw, x, y, r=12, color=GOLD):
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        ex = x + int(r * math.cos(rad))
        ey = y + int(r * math.sin(rad))
        draw.line([(x, y), (ex, ey)], fill=color, width=3)
    draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=WHITE)

sparkle_positions = [
    (320, 560), (W - 290, 580), (210, 750), (W - 220, 730),
    (380, 900), (W - 360, 880), (155, 1050), (W - 140, 1040),
]
for sx, sy in sparkle_positions:
    sparkle(draw, sx, sy, r=14, color=GOLD)


# ─────────────────────────────────────────────────────────────────────────────
#  SAVE PNG
# ─────────────────────────────────────────────────────────────────────────────
out_png = "/mnt/user-data/outputs/skyband_flyer.png"
img.save(out_png, "PNG", dpi=(DPI, DPI))
print(f"PNG saved → {out_png}")


# ─────────────────────────────────────────────────────────────────────────────
#  SAVE PDF  (embed the PNG as a full-page image at print resolution)
# ─────────────────────────────────────────────────────────────────────────────
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage
from reportlab.lib import pagesizes

from reportlab.pdfgen import canvas as rl_canvas

out_pdf = "/mnt/user-data/outputs/skyband_flyer.pdf"
c = rl_canvas.Canvas(out_pdf, pagesize=letter)
c.drawImage(out_png, 0, 0, width=8.5 * inch, height=11 * inch)
c.showPage()
c.save()
print(f"PDF saved → {out_pdf}")
print("Done!")
