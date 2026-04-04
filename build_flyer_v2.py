#!/usr/bin/env python3
"""
SkyBand / 4PR Aerial Solutions — V2 Professional Flyer
Clean, agency-quality design at 300 DPI (2550×3300)
"""
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DPI = 300
W, H = int(8.5 * DPI), int(11 * DPI)   # 2550 × 3300

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY      = ( 10,  20,  45)
DEEP_BLUE = ( 18,  38,  82)
MID_BLUE  = ( 38,  82, 145)
SKY       = ( 74, 144, 226)
ICE       = (200, 225, 255)
GOLD      = (255, 184,  50)
GOLD_DRK  = (200, 130,  20)
WHITE     = (255, 255, 255)
OFF_WHITE = (240, 247, 255)
SAND      = (210, 170, 110)

FONT_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_I = "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf"

def font(size, style="bold"):
    path = {"bold": FONT_B, "regular": FONT_R, "italic": FONT_I}[style]
    return ImageFont.truetype(path, size)

def cx(draw, text, f, y, color, width=W, offset_x=0):
    bb = draw.textbbox((0,0), text, font=f)
    x = (width - (bb[2]-bb[0])) // 2 + offset_x
    return draw.text((x, y), text, font=f, fill=color)

def cx_pos(draw, text, f, width=W):
    bb = draw.textbbox((0,0), text, font=f)
    return (width - (bb[2]-bb[0])) // 2

# ─────────────────────────────────────────────────────────────────────────────
# 1. BASE: full-canvas deep navy → dark blue gradient
# ─────────────────────────────────────────────────────────────────────────────
img = Image.new("RGB", (W, H), NAVY)
draw = ImageDraw.Draw(img, "RGBA")

for y in range(H):
    t = y / H
    if t < 0.55:
        f = t / 0.55
        c = tuple(int(NAVY[i] + f*(DEEP_BLUE[i]-NAVY[i])) for i in range(3))
    else:
        f = (t - 0.55) / 0.45
        c = tuple(int(DEEP_BLUE[i] + f*(NAVY[i]-DEEP_BLUE[i])) for i in range(3))
    draw.line([(0,y),(W,y)], fill=c)


# ─────────────────────────────────────────────────────────────────────────────
# 2. BIG RADIAL GLOW — upper center (gives depth / spotlight feel)
# ─────────────────────────────────────────────────────────────────────────────
glow_layer = Image.new("RGBA", (W, H), (0,0,0,0))
gd = ImageDraw.Draw(glow_layer)
gcx, gcy = W//2, int(H*0.36)
for r in range(900, 0, -6):
    a = int(28 * (1 - r/900))
    gd.ellipse([gcx-r, gcy-int(r*0.55), gcx+r, gcy+int(r*0.55)],
               fill=(*MID_BLUE, a))
img = Image.alpha_composite(img.convert("RGBA"), glow_layer).convert("RGB")
draw = ImageDraw.Draw(img, "RGBA")


# ─────────────────────────────────────────────────────────────────────────────
# 3. GOLD TOP BAR + subtle texture lines
# ─────────────────────────────────────────────────────────────────────────────
draw.rectangle([0, 0, W, 18], fill=GOLD)
# thin rule below gold bar
draw.rectangle([0, 18, W, 22], fill=(*GOLD_DRK, 180))

# very faint horizontal scan lines for texture (subtle)
for y in range(0, H, 8):
    draw.line([(0,y),(W,y)], fill=(255,255,255,5))


# ─────────────────────────────────────────────────────────────────────────────
# 4. HEADER: company name + rule
# ─────────────────────────────────────────────────────────────────────────────
# Slim top badge
badge_top, badge_bot = 34, 130
draw.rounded_rectangle([80, badge_top, W-80, badge_bot], radius=6,
                        fill=(*MID_BLUE, 80), outline=(*SKY, 60), width=2)

f_co = font(52, "bold")
cx(draw, "SKYBAND  /  4PR AERIAL SOLUTIONS", f_co, badge_top+14, WHITE)

# gold divider line
draw.rectangle([120, badge_bot+18, W-120, badge_bot+22], fill=(*GOLD, 200))


# ─────────────────────────────────────────────────────────────────────────────
# 5. MAIN HEADLINE  — "FREE" huge + "AERIAL DRONE PACKAGE"
# ─────────────────────────────────────────────────────────────────────────────
hl_y = 175

# "FREE" — massive, gold
f_free = font(260, "bold")
free_bb = draw.textbbox((0,0), "FREE", font=f_free)
free_w  = free_bb[2]-free_bb[0]
free_x  = (W - free_w)//2

# drop shadow
draw.text((free_x+8, hl_y+8), "FREE", font=f_free, fill=(0,0,0,120))
# main text
draw.text((free_x, hl_y), "FREE", font=f_free, fill=GOLD)

# thin highlight stroke illusion (bright top edge)
draw.text((free_x, hl_y-2), "FREE", font=f_free, fill=(*WHITE, 18))

# "AERIAL DRONE PACKAGE" — white, tight tracking
f_sub_hl = font(96, "bold")
adp_y = hl_y + 240
draw.text((cx_pos(draw,"AERIAL DRONE PACKAGE",f_sub_hl)+3, adp_y+4),
          "AERIAL DRONE PACKAGE", font=f_sub_hl, fill=(0,0,0,100))
cx(draw, "AERIAL DRONE PACKAGE", f_sub_hl, adp_y, WHITE)


# ─────────────────────────────────────────────────────────────────────────────
# 6. DIVIDER with stars
# ─────────────────────────────────────────────────────────────────────────────
div_y = adp_y + 118
line_pad = 220
draw.rectangle([line_pad, div_y, W-line_pad, div_y+3], fill=(*GOLD, 160))

def star5(draw, cx, cy, r_out, r_in, color):
    pts = []
    for i in range(10):
        angle = math.radians(-90 + i*36)
        r = r_out if i%2==0 else r_in
        pts.append((cx + r*math.cos(angle), cy + r*math.sin(angle)))
    draw.polygon(pts, fill=color)

for sx in [line_pad-30, W//2, W-line_pad+30]:
    star5(draw, sx, div_y+2, 22, 10, GOLD)


# ─────────────────────────────────────────────────────────────────────────────
# 7. DRONE ICON  — clean, modern, minimal
# ─────────────────────────────────────────────────────────────────────────────
drone_cx = W//2
drone_cy = int(H * 0.455)
S = 1.7   # scale

def draw_drone_v2(draw, cx, cy, S, body_color=WHITE, accent=GOLD, shadow=(0,0,0,90)):
    # ── arms (thin, elegant) ──
    arm_len  = int(195*S)
    arm_w    = int(9*S)
    for ang in [40, 140, 220, 320]:
        rad = math.radians(ang)
        x1 = cx + int(28*S*math.cos(rad))
        y1 = cy + int(28*S*math.sin(rad))
        x2 = cx + int(arm_len*math.cos(rad))
        y2 = cy + int(arm_len*math.sin(rad))
        draw.line([(x1+3,y1+3),(x2+3,y2+3)], fill=shadow, width=arm_w)
        draw.line([(x1,y1),(x2,y2)], fill=body_color, width=arm_w)

    # ── motor housings ──
    for ang in [40, 140, 220, 320]:
        rad = math.radians(ang)
        mx = cx + int(arm_len*math.cos(rad))
        my = cy + int(arm_len*math.sin(rad))
        mr = int(28*S)
        draw.ellipse([mx-mr+3,my-mr+3,mx+mr+3,my+mr+3], fill=shadow)
        draw.ellipse([mx-mr,my-mr,mx+mr,my+mr], fill=MID_BLUE, outline=body_color, width=int(4*S))
        # motor center dot
        dot_r = int(8*S)
        draw.ellipse([mx-dot_r,my-dot_r,mx+dot_r,my+dot_r], fill=accent)

    # ── propeller blades (two per motor, thin elegant) ──
    prop_len = int(92*S)
    prop_w   = int(11*S)
    for ang in [40, 140, 220, 320]:
        rad = math.radians(ang)
        mx = cx + int(arm_len*math.cos(rad))
        my = cy + int(arm_len*math.sin(rad))
        for offset in [0, 90]:
            brad = math.radians(ang + offset + 25)
            px1 = mx - int(prop_len*math.cos(brad))
            py1 = my - int(prop_len*math.sin(brad))
            px2 = mx + int(prop_len*math.cos(brad))
            py2 = my + int(prop_len*math.sin(brad))
            draw.line([(px1+2,py1+2),(px2+2,py2+2)], fill=shadow, width=prop_w)
            draw.line([(px1,py1),(px2,py2)], fill=(*body_color, 200), width=prop_w)

    # ── central body ──
    bw, bh = int(80*S), int(38*S)
    # shadow
    draw.rounded_rectangle([cx-bw+5,cy-bh+5,cx+bw+5,cy+bh+5], radius=int(16*S), fill=shadow)
    # outer shell
    draw.rounded_rectangle([cx-bw,cy-bh,cx+bw,cy+bh], radius=int(16*S),
                            fill=MID_BLUE, outline=body_color, width=int(5*S))
    # inner highlight strip
    draw.rounded_rectangle([cx-bw+int(10*S),cy-bh+int(6*S),
                             cx+bw-int(10*S),cy-bh+int(18*S)],
                            radius=int(6*S), fill=(*WHITE,40))

    # ── landing gear legs ──
    leg_w = int(5*S)
    for lx in [-int(48*S), int(48*S)]:
        draw.line([(cx+lx, cy+bh), (cx+lx, cy+bh+int(28*S))], fill=body_color, width=leg_w)
    draw.line([(cx-int(65*S), cy+bh+int(28*S)),
               (cx+int(65*S), cy+bh+int(28*S))], fill=body_color, width=leg_w)

    # ── gimbal / camera ──
    gbr = int(22*S)
    gbx, gby = cx, cy+bh+int(2*S)
    draw.ellipse([gbx-gbr,gby,gbx+gbr,gby+int(gbr*2)], fill=NAVY, outline=accent, width=int(3*S))
    lens_r = int(11*S)
    draw.ellipse([gbx-lens_r,gby+int(6*S),gbx+lens_r,gby+int(6*S)+lens_r*2],
                 fill=(*SKY, 200))
    # lens glint
    draw.ellipse([gbx-int(4*S),gby+int(8*S),gbx+int(4*S),gby+int(14*S)], fill=(*WHITE,180))

    # ── front LED lights ──
    for lx in [-int(35*S), int(35*S)]:
        lr = int(5*S)
        draw.ellipse([cx+lx-lr,cy-lr,cx+lx+lr,cy+lr], fill=accent)

draw_drone_v2(draw, drone_cx, drone_cy, S)


# ─────────────────────────────────────────────────────────────────────────────
# 8. OFFER PILL: "6 PROFESSIONAL AERIAL PHOTOS"
# ─────────────────────────────────────────────────────────────────────────────
pill_y  = int(H * 0.625)
pill_h  = 105
pill_x0 = 130
pill_x1 = W - 130

# glow behind pill
for i in range(5):
    pad = i*7
    draw.rounded_rectangle([pill_x0-pad, pill_y-pad, pill_x1+pad, pill_y+pill_h+pad],
                            radius=pill_h//2+pad,
                            fill=(*SKY, max(0, 30-i*6)))

draw.rounded_rectangle([pill_x0, pill_y, pill_x1, pill_y+pill_h],
                        radius=pill_h//2, fill=(*MID_BLUE, 220),
                        outline=SKY, width=4)

f_offer = font(66, "bold")
cx(draw, "6 PROFESSIONAL AERIAL PHOTOS", f_offer, pill_y+18, WHITE)


# ─────────────────────────────────────────────────────────────────────────────
# 9. SUBHEADLINES
# ─────────────────────────────────────────────────────────────────────────────
sub_y = pill_y + pill_h + 50

f_limited = font(58, "italic")
cx(draw, "LIMITED TIME GIVEAWAY", f_limited, sub_y, GOLD)

f_showcase = font(44, "regular")
cx(draw, "Showcase Your Property From Above", f_showcase, sub_y+78, ICE)


# ─────────────────────────────────────────────────────────────────────────────
# 10. VALUE BOX  — premium badge feel
# ─────────────────────────────────────────────────────────────────────────────
vb_y  = sub_y + 170
vb_h  = 148
vb_x0 = 175
vb_x1 = W - 175

# outer glow
for i in range(6):
    pad = i*5
    draw.rounded_rectangle([vb_x0-pad, vb_y-pad, vb_x1+pad, vb_y+vb_h+pad],
                            radius=24+pad, fill=(*GOLD, max(0, 35-i*6)))

# gold fill
draw.rounded_rectangle([vb_x0, vb_y, vb_x1, vb_y+vb_h], radius=24, fill=GOLD)
# inner shadow strip at top (gives 3-D depth)
draw.rounded_rectangle([vb_x0, vb_y, vb_x1, vb_y+30], radius=24,
                        fill=(*WHITE, 40))
# bottom shadow strip
draw.rounded_rectangle([vb_x0, vb_y+vb_h-20, vb_x1, vb_y+vb_h], radius=24,
                        fill=(0,0,0,40))

f_val  = font(84, "bold")
f_free = font(58, "bold")

val_text = "$300+ VALUE"
cx(draw, val_text, f_val, vb_y+8, NAVY)

free_text = "★   COMPLETELY FREE   ★"
cx(draw, free_text, f_free, vb_y+vb_h-74, DEEP_BLUE)


# ─────────────────────────────────────────────────────────────────────────────
# 11. WAVE SEPARATOR
# ─────────────────────────────────────────────────────────────────────────────
wave_y = int(H * 0.873)

# dark panel fill below wave
draw.rectangle([0, wave_y+30, W, H], fill=(8,16,38))

# two offset wave layers for depth
def wave_poly(y_base, amp, wavelen, color, draw):
    pts_top = [(0, H)]
    for x in range(0, W+1, 6):
        y = y_base + int(amp * math.sin(2*math.pi*x/wavelen + 0.4))
        pts_top.append((x, y))
    pts_top.append((W, H))
    draw.polygon(pts_top, fill=color)

wave_poly(wave_y+20, 28, 900, (8,16,38), draw)
wave_poly(wave_y,    22, 700, (*MID_BLUE,180), draw)
wave_poly(wave_y-18, 16, 550, (*SKY,80), draw)


# ─────────────────────────────────────────────────────────────────────────────
# 12. FOOTER
# ─────────────────────────────────────────────────────────────────────────────
footer_y = wave_y + 50
draw.rectangle([0, footer_y, W, H], fill=(8,16,38))

# gold rule
draw.rectangle([80, footer_y, W-80, footer_y+4], fill=GOLD)

f_co2   = font(56, "bold")
f_phone = font(62, "bold")
f_ig    = font(50, "regular")
f_cta   = font(42, "italic")

cx(draw, "SkyBand / 4PR Aerial Solutions", f_co2,   footer_y+18,  GOLD)
cx(draw, "984  810  7950",                 f_phone,  footer_y+88,  WHITE)
cx(draw, "@SkyBandLegacyMedia",            f_ig,     footer_y+162, ICE)
cx(draw, "DM or Call to Claim Your Free Package", f_cta, footer_y+218, SAND)

# bottom gold bar
draw.rectangle([0, H-16, W, H], fill=GOLD)


# ─────────────────────────────────────────────────────────────────────────────
# 13. CORNER MARKS  (clean L-brackets, not heavy)
# ─────────────────────────────────────────────────────────────────────────────
def bracket(draw, x, y, flip_x=False, flip_y=False, sz=70, t=6, color=GOLD):
    sx = -1 if flip_x else 1
    sy = -1 if flip_y else 1
    x0h,x1h = sorted([x, x+sx*sz]); y0h,y1h = sorted([y, y+sy*t])
    x0v,x1v = sorted([x, x+sx*t]);  y0v,y1v = sorted([y, y+sy*sz])
    draw.rectangle([x0h,y0h,x1h,y1h], fill=color)
    draw.rectangle([x0v,y0v,x1v,y1v], fill=color)

m = 36
bracket(draw, m,   m,       False, False)
bracket(draw, W-m, m,       True,  False)
bracket(draw, m,   H-m,     False, True)
bracket(draw, W-m, H-m,     True,  True)


# ─────────────────────────────────────────────────────────────────────────────
# 14. LIGHT BOKEH DOTS  (subtle background depth, NOT clip-art)
# ─────────────────────────────────────────────────────────────────────────────
bokeh_layer = Image.new("RGBA", (W, H), (0,0,0,0))
bd = ImageDraw.Draw(bokeh_layer)
bokeh_data = [
    (320,  420, 55, 18), (W-290, 380, 45, 14), (200,  700, 40, 12),
    (W-210,680, 48, 15), (380,  950, 38, 11),  (W-350,920, 42, 13),
    (160, 1100, 50, 16), (W-170,1060,44, 14),  (450,  580, 36, 10),
    (W-420,560, 40, 12),
]
for bx, by, br, ba in bokeh_data:
    for ri in range(br, 0, -3):
        a = int(ba * (ri/br) * 0.6)
        bd.ellipse([bx-ri,by-ri,bx+ri,by+ri], fill=(*SKY, a))
    bd.ellipse([bx-4,by-4,bx+4,by+4], fill=(*WHITE, 80))

bokeh_blur = bokeh_layer.filter(ImageFilter.GaussianBlur(radius=8))
img = Image.alpha_composite(img.convert("RGBA"), bokeh_blur).convert("RGB")


# ─────────────────────────────────────────────────────────────────────────────
# 15. FINAL SHARPENING PASS  (crisp at 300 DPI)
# ─────────────────────────────────────────────────────────────────────────────
from PIL import ImageEnhance
img = ImageEnhance.Sharpness(img).enhance(1.15)
img = ImageEnhance.Contrast(img).enhance(1.05)


# ─────────────────────────────────────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────────────────────────────────────
out_png = "/mnt/user-data/outputs/skyband_flyer.png"
out_pdf = "/mnt/user-data/outputs/skyband_flyer.pdf"

img.save(out_png, "PNG", dpi=(DPI, DPI))
print(f"PNG → {out_png}")

from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
c = rl_canvas.Canvas(out_pdf, pagesize=letter)
c.drawImage(out_png, 0, 0, width=8.5*inch, height=11*inch)
c.showPage()
c.save()
print(f"PDF → {out_pdf}")
print("Done.")
