"""
DJI Matrice M600 + GS Pro System Architecture Diagram Generator
Produces publication-ready PNG and PDF files at 300 DPI, 8.5" x 11".
"""

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np

# ── Output paths ────────────────────────────────────────────────────────────
OUTPUT_PNG = "/mnt/user-data/outputs/m600_architecture.png"
OUTPUT_PDF = "/mnt/user-data/outputs/m600_architecture.pdf"

# ── Canvas ───────────────────────────────────────────────────────────────────
FIG_W, FIG_H = 8.5, 11.0   # inches (portrait US Letter)
DPI         = 300

# ── Color palette (academic, soft) ───────────────────────────────────────────
COLORS = {
    "gcs":        "#BDD7EE",   # steel blue
    "comms":      "#D6E4BC",   # sage green
    "fc":         "#FFE699",   # amber yellow
    "power":      "#F4B8C1",   # rose
    "propulsion": "#C5E0B4",   # mint green
    "payload":    "#D9B8F4",   # lavender
    "positioning":"#B8D9F4",   # sky blue
    "edge":       "#2F4F8F",   # dark navy (borders)
    "arrow":      "#1A1A3E",   # near-black arrows
    "protocol":   "#3B3B6B",   # protocol label color
    "title_bg":   "#1C3557",   # title bar background
    "title_fg":   "#FFFFFF",   # title text
    "subbox":     "#FFFFFFCC", # sub-component box fill
}

# ── Layer definitions ─────────────────────────────────────────────────────────
LAYERS = [
    {
        "id":       "gcs",
        "label":    "LAYER 1 — GROUND CONTROL STATION",
        "protocol": "Protocol: 802.11 Wi-Fi / USB",
        "color":    COLORS["gcs"],
        "items": [
            "DJI Remote Controller",
            "Mobile Device  (iPad / Tablet)",
            "GS Pro Application",
        ],
        "subitems": None,
    },
    {
        "id":       "comms",
        "label":    "LAYER 2 — COMMUNICATION LINK",
        "protocol": "Protocol: 2.4 / 5.8 GHz RF  ·  Proprietary DJI  ·  MAVLink-like",
        "color":    COLORS["comms"],
        "items": [
            "Lightbridge 2 Data Link",
            "Uplink:  Commands, Waypoints",
            "Downlink:  Telemetry, Video Feed",
        ],
        "subitems": None,
    },
    {
        "id":       "fc",
        "label":    "LAYER 3 — FLIGHT CONTROLLER",
        "protocol": "Protocol: CAN Bus  ·  I²C  ·  UART  ·  SPI",
        "color":    COLORS["fc"],
        "items": [
            "A3 Pro Flight Controller",
        ],
        "subitems": [
            ["IMU (Triple\nRedundant)", "GPS Module\n(Dual)", "Barometer\n& Compass"],
        ],
    },
    {
        "id":       "power",
        "label":    "LAYER 4 — POWER SYSTEM",
        "protocol": "Protocol: SMBus  ·  PWM",
        "color":    COLORS["power"],
        "items": [
            "6× TB47S / TB48S Battery Packs",
            "Power Management Unit  (PMU)",
            "Electronic Speed Controllers  (ESC)",
        ],
        "subitems": None,
    },
    {
        "id":       "propulsion",
        "label":    "LAYER 5 — PROPULSION SYSTEM",
        "protocol": "Protocol: PWM Signal (50 Hz / Digital)",
        "color":    COLORS["propulsion"],
        "items": [
            "6× DJI 6010 Brushless Motors",
            "6× Bi-directional ESCs",
            "6× 21″ Carbon Fibre Propellers",
        ],
        "subitems": None,
    },
    {
        "id":       "payload",
        "label":    "LAYER 6 — PAYLOAD INTERFACE",
        "protocol": "Protocol: UART  ·  CAN  ·  OSDK / SDK API",
        "color":    COLORS["payload"],
        "items": [
            "Ronin-MX Gimbal Stabiliser",
            "Zenmuse X5 / X7 Camera",
            "Expansion / SDK Port",
        ],
        "subitems": None,
    },
    {
        "id":       "positioning",
        "label":    "LAYER 7 — POSITIONING SYSTEM",
        "protocol": "Protocol: NMEA 0183  ·  UBX Binary",
        "color":    COLORS["positioning"],
        "items": [
            "GPS L1/L2  (Primary)",
            "GLONASS  (Secondary)",
            "Triple-redundant Compass",
        ],
        "subitems": None,
    },
]


def draw_rounded_box(ax, x, y, w, h, color, edge_color, lw=1.5, radius=0.015,
                     zorder=2, alpha=1.0):
    """Draw a FancyBboxPatch with rounded corners."""
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=lw,
        edgecolor=edge_color,
        facecolor=color,
        alpha=alpha,
        zorder=zorder,
    )
    ax.add_patch(box)
    return box


def draw_layer(ax, layer_def, y_top, layer_h,
               x_main=0.07, w_main=0.70,
               x_proto=0.78, w_proto=0.20):
    """
    Draw one architecture layer:
      - Left: main coloured box with items
      - Right: protocol label box
      - Returns y_bottom of this layer
    """
    pad_x = 0.012
    pad_y = 0.010
    color     = layer_def["color"]
    items     = layer_def["items"]
    subitems  = layer_def["subitems"]
    lbl       = layer_def["label"]
    proto_txt = layer_def["protocol"]

    # ── Main layer box ───────────────────────────────────────────────────
    draw_rounded_box(ax, x_main, y_top - layer_h, w_main, layer_h,
                     color=color, edge_color=COLORS["edge"], lw=1.8, radius=0.012)

    # Layer heading strip (slightly darker band at the top of the box)
    heading_h = 0.028
    heading_color = _darken(color, 0.18)
    draw_rounded_box(ax, x_main, y_top - heading_h, w_main, heading_h,
                     color=heading_color, edge_color=COLORS["edge"],
                     lw=1.8, radius=0.010, zorder=3)
    ax.text(x_main + w_main / 2, y_top - heading_h / 2, lbl,
            ha="center", va="center", fontsize=6.2, fontweight="bold",
            color="#FFFFFF", zorder=4,
            fontfamily="DejaVu Sans")

    # ── Item text ────────────────────────────────────────────────────────
    content_top  = y_top - heading_h - pad_y
    content_h    = layer_h - heading_h - pad_y
    has_subitems = subitems is not None

    if not has_subitems:
        # Evenly distribute items vertically inside the box
        n = len(items)
        slot_h = content_h / n
        for i, txt in enumerate(items):
            ty = content_top - slot_h * (i + 0.5)
            # Small bullet rectangle
            bullet_x = x_main + pad_x + 0.003
            bullet_y = ty - 0.006
            ax.add_patch(mpatches.FancyBboxPatch(
                (bullet_x, bullet_y), 0.008, 0.012,
                boxstyle="round,pad=0,rounding_size=0.003",
                linewidth=0, facecolor=COLORS["edge"], alpha=0.55, zorder=4))
            ax.text(x_main + pad_x + 0.018, ty, txt,
                    ha="left", va="center", fontsize=7.2,
                    color="#1A1A2E", zorder=4,
                    fontfamily="DejaVu Sans")
    else:
        # Draw the main item text above the sub-boxes
        ty_main = content_top - 0.018
        ax.text(x_main + w_main / 2, ty_main, items[0],
                ha="center", va="center", fontsize=7.8, fontweight="bold",
                color="#1A1A2E", zorder=4, fontfamily="DejaVu Sans")

        # Sub-item boxes (for Flight Controller layer)
        sub_row    = subitems[0]
        n_sub      = len(sub_row)
        sub_y_top  = ty_main - 0.030
        sub_h      = content_h - 0.060
        sub_gap    = 0.010
        sub_total_w = w_main - 2 * pad_x - sub_gap * (n_sub - 1)
        sub_w      = sub_total_w / n_sub
        for j, stxt in enumerate(sub_row):
            sx = x_main + pad_x + j * (sub_w + sub_gap)
            sy = sub_y_top - sub_h
            draw_rounded_box(ax, sx, sy, sub_w, sub_h,
                             color=COLORS["subbox"],
                             edge_color=COLORS["edge"],
                             lw=1.2, radius=0.008, zorder=4, alpha=0.95)
            ax.text(sx + sub_w / 2, sy + sub_h / 2, stxt,
                    ha="center", va="center", fontsize=6.5,
                    color="#1A1A2E", zorder=5,
                    fontfamily="DejaVu Sans",
                    multialignment="center")

    # ── Protocol box (right side) ────────────────────────────────────────
    draw_rounded_box(ax, x_proto, y_top - layer_h, w_proto, layer_h,
                     color="#F8F9FA", edge_color=COLORS["protocol"],
                     lw=1.2, radius=0.010, zorder=2, alpha=0.92)
    ax.text(x_proto + 0.005, y_top - layer_h / 2,
            proto_txt,
            ha="left", va="center", fontsize=5.5,
            color=COLORS["protocol"], zorder=4,
            fontfamily="DejaVu Sans",
            wrap=True,
            multialignment="left")

    return y_top - layer_h


def draw_bidirectional_arrow(ax, y_mid, x_start=0.07, w=0.70, gap=0.004):
    """Draw a double-headed arrow between two layers."""
    cx = x_start + w / 2
    ax.annotate("", xy=(cx - 0.06, y_mid - gap),
                xytext=(cx - 0.06, y_mid + gap),
                arrowprops=dict(arrowstyle="->",
                                color=COLORS["arrow"],
                                lw=1.5,
                                connectionstyle="arc3,rad=0.0"),
                zorder=6)
    ax.annotate("", xy=(cx + 0.06, y_mid + gap),
                xytext=(cx + 0.06, y_mid - gap),
                arrowprops=dict(arrowstyle="->",
                                color=COLORS["arrow"],
                                lw=1.5,
                                connectionstyle="arc3,rad=0.0"),
                zorder=6)
    # Centre dashed connector line
    ax.plot([cx - 0.10, cx + 0.10], [y_mid, y_mid],
            color=COLORS["arrow"], lw=0.8, linestyle="--",
            alpha=0.45, zorder=5)


def _darken(hex_color, amount=0.15):
    """Return a darkened version of a hex colour."""
    import colorsys
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = max(0.0, l - amount)
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return "#{:02X}{:02X}{:02X}".format(int(r2*255), int(g2*255), int(b2*255))


def build_diagram():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # ── Title bar ────────────────────────────────────────────────────────────
    title_h  = 0.058
    title_y  = 1.0 - title_h
    draw_rounded_box(ax, 0.03, title_y, 0.94, title_h,
                     color=COLORS["title_bg"],
                     edge_color=COLORS["title_bg"],
                     lw=0, radius=0.010, zorder=2)
    ax.text(0.50, title_y + title_h * 0.60,
            "DJI Matrice M600 + GS Pro",
            ha="center", va="center",
            fontsize=13.5, fontweight="bold",
            color=COLORS["title_fg"], zorder=4,
            fontfamily="DejaVu Sans")
    ax.text(0.50, title_y + title_h * 0.20,
            "System Architecture  ·  7-Layer Model",
            ha="center", va="center",
            fontsize=7.8, fontstyle="italic",
            color="#B0C4DE", zorder=4,
            fontfamily="DejaVu Sans")

    # ── Legend (small, top-right corner) ────────────────────────────────────
    legend_items = [
        ("Ground Control", COLORS["gcs"]),
        ("Comm Link",      COLORS["comms"]),
        ("Flight Control", COLORS["fc"]),
        ("Power",          COLORS["power"]),
        ("Propulsion",     COLORS["propulsion"]),
        ("Payload",        COLORS["payload"]),
        ("Positioning",    COLORS["positioning"]),
    ]
    # (legend is inherently conveyed by layer colours; skip redundant box
    #  to keep diagram clean — uncomment to add)

    # ── Layer geometry ───────────────────────────────────────────────────────
    margin_top    = 0.025   # gap below title bar
    margin_bottom = 0.030
    arrow_gap     = 0.022   # vertical space reserved for each inter-layer arrow
    n_layers      = len(LAYERS)
    n_arrows      = n_layers - 1

    usable_h = title_y - margin_top - margin_bottom
    total_arrow_h = arrow_gap * n_arrows
    # FC layer (index 2) gets more height for sub-boxes
    base_h   = (usable_h - total_arrow_h) / (n_layers + 0.6)
    layer_heights = [base_h] * n_layers
    layer_heights[2] *= 1.6   # Flight controller layer taller

    # Normalise so total fits
    total_layer_h = sum(layer_heights)
    scale = (usable_h - total_arrow_h) / total_layer_h
    layer_heights = [h * scale for h in layer_heights]

    # ── Draw layers top→bottom ───────────────────────────────────────────────
    y_cursor = title_y - margin_top
    y_bottoms = []

    for i, (layer, lh) in enumerate(zip(LAYERS, layer_heights)):
        y_bottom = draw_layer(ax, layer, y_cursor, lh)
        y_bottoms.append(y_bottom)
        y_cursor = y_bottom

        if i < n_layers - 1:
            # Reserve space for arrow
            y_mid = y_cursor - arrow_gap / 2
            draw_bidirectional_arrow(ax, y_mid)
            y_cursor -= arrow_gap

    # ── Footer ───────────────────────────────────────────────────────────────
    ax.text(0.50, 0.010,
            "Source: DJI Official Documentation  ·  Generated for Academic Research  ·  "
            "DJI Matrice 600 Pro User Manual v1.0",
            ha="center", va="bottom", fontsize=4.8,
            color="#888888", fontfamily="DejaVu Sans")

    # ── Column headers (faint) ───────────────────────────────────────────────
    ax.text(0.07 + 0.70/2, title_y - 0.010,
            "◀  System Components  ▶",
            ha="center", va="top", fontsize=5.2,
            color="#AAAAAA", fontfamily="DejaVu Sans")
    ax.text(0.78 + 0.20/2, title_y - 0.010,
            "Interface Protocol",
            ha="center", va="top", fontsize=5.2,
            color="#AAAAAA", fontfamily="DejaVu Sans")

    return fig


def main():
    print("Generating DJI M600 system architecture diagram …")
    fig = build_diagram()

    # ── Save PNG ─────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PNG, dpi=DPI, bbox_inches="tight",
                facecolor="white", format="png")
    print(f"  ✓  PNG saved → {OUTPUT_PNG}")

    # ── Save PDF ─────────────────────────────────────────────────────────────
    fig.savefig(OUTPUT_PDF, dpi=DPI, bbox_inches="tight",
                facecolor="white", format="pdf")
    print(f"  ✓  PDF saved → {OUTPUT_PDF}")

    plt.close(fig)
    print("Done.")


if __name__ == "__main__":
    main()
