#!/usr/bin/env python3
"""
Generate diagram 09: HA Connectivity Architecture Diagram
Corrections from v2.1:
  - Elastic IP (Public) outbound only to PSTN Provider
  - Elastic IP bidirectional with External Interface (WAN)
  - Microsoft Teams bidirectional with Elastic IP
  - Virtual IP bidirectional with Internal Interface (LAN)
  - All Virtual IP addresses 10.x.x.x (not 169.254.64.x)
"""

from PIL import Image, ImageDraw, ImageFont
import math

# Canvas
W, H = 1100, 1400
img = Image.new("RGB", (W, H), "#FFFFFF")
draw = ImageDraw.Draw(img)

# Fonts
def font(size, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size)

F_TITLE = font(13, bold=True)
F_BODY = font(11)
F_SMALL = font(10)
F_ZONE = font(12, bold=True)
F_NOTE = font(10)
F_LABEL = font(10, bold=True)

# Colours
ZONE_BG = "#FFFDE7"
ZONE_BORDER = "#C5CAE9"
BOX_BG = "#E8EAF6"
BOX_BORDER = "#7986CB"
NOTE_BG = "#FFF9C4"
NOTE_BORDER = "#FFD54F"
TEXT_COLOR = "#212121"
ARROW_COLOR = "#37474F"
ARROW_BI = "#1565C0"       # blue for bidirectional
ARROW_UNI = "#E65100"      # orange for unidirectional
DASHED_COLOR = "#90A4AE"
AZ_COLOR = "#78909C"
HA_COLOR = "#E65100"


def draw_zone(x, y, w, h, label):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=8,
                           fill=ZONE_BG, outline=ZONE_BORDER, width=2)
    tw = draw.textlength(label, font=F_ZONE)
    draw.text((x + (w - tw) / 2, y + 6), label, fill=TEXT_COLOR, font=F_ZONE)


def draw_box(x, y, w, h, lines, bold_first=True):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=6,
                           fill=BOX_BG, outline=BOX_BORDER, width=2)
    line_h = 16
    start_y = y + (h - len(lines) * line_h) / 2
    for i, line in enumerate(lines):
        f = F_TITLE if (i == 0 and bold_first) else F_BODY
        tw = draw.textlength(line, font=f)
        draw.text((x + (w - tw) / 2, start_y + i * line_h),
                  line, fill=TEXT_COLOR, font=f)


def draw_note(x, y, w, h, lines):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=5,
                           fill=NOTE_BG, outline=NOTE_BORDER, width=2)
    line_h = 14
    start_y = y + (h - len(lines) * line_h) / 2
    for i, line in enumerate(lines):
        tw = draw.textlength(line, font=F_NOTE)
        draw.text((x + (w - tw) / 2, start_y + i * line_h),
                  line, fill=TEXT_COLOR, font=F_NOTE)


def arrowhead(x, y, angle, size=10, color=ARROW_COLOR):
    a1 = angle + math.pi * 0.82
    a2 = angle - math.pi * 0.82
    p1 = (x + size * math.cos(a1), y + size * math.sin(a1))
    p2 = (x + size * math.cos(a2), y + size * math.sin(a2))
    draw.polygon([(x, y), p1, p2], fill=color)


def dashed_line_v(x, y1, y2, color=DASHED_COLOR, width=2, dash=6, gap=4):
    y = y1
    while y < y2:
        end = min(y + dash, y2)
        draw.line([(x, y), (x, end)], fill=color, width=width)
        y = end + gap


def draw_bidir_v(x, y1, y2, color=ARROW_BI, width=2, label=None, label_x_off=15):
    """Two parallel arrows for bidirectional vertical."""
    off = 7
    # Down arrow
    draw.line([(x - off, y1), (x - off, y2)], fill=color, width=width)
    arrowhead(x - off, y2, math.pi / 2, size=8, color=color)
    # Up arrow
    draw.line([(x + off, y2), (x + off, y1)], fill=color, width=width)
    arrowhead(x + off, y1, -math.pi / 2, size=8, color=color)
    if label:
        draw.text((x + label_x_off, (y1 + y2) / 2 - 6), label,
                  fill=color, font=F_LABEL)


def draw_bidir_h(y, x1, x2, color=ARROW_BI, width=2):
    """Bidirectional horizontal arrow."""
    off = 5
    # Right arrow
    draw.line([(x1, y - off), (x2, y - off)], fill=color, width=width)
    arrowhead(x2, y - off, 0, size=8, color=color)
    # Left arrow
    draw.line([(x2, y + off), (x1, y + off)], fill=color, width=width)
    arrowhead(x1, y + off, math.pi, size=8, color=color)


# ═══════════════════════════════════════════════════
# LAYOUT
# ═══════════════════════════════════════════════════

# Internet zone
iz_x, iz_y, iz_w, iz_h = 130, 20, 840, 140
teams_x, teams_y, teams_w, teams_h = 170, 55, 230, 80
pstn_x, pstn_y, pstn_w, pstn_h = 630, 55, 230, 80

# Elastic IP
eip_x, eip_y, eip_w, eip_h = 310, 200, 260, 75

# AWS VPC zone
vpc_x, vpc_y, vpc_w, vpc_h = 55, 330, 990, 610

# External Interface (WAN)
wan_x, wan_y, wan_w, wan_h = 350, 365, 260, 50

# VPC Route Table note
rt_x, rt_y, rt_w, rt_h = 70, 385, 240, 70

# HA Proxy SBC Pair zone
ha_x, ha_y, ha_w, ha_h = 90, 445, 920, 320

# SBC boxes
sbc2_x, sbc2_y, sbc2_w, sbc2_h = 180, 510, 260, 70
sbc1_x, sbc1_y, sbc1_w, sbc1_h = 150, 670, 260, 60

# Internal Interface (LAN)
lan_x, lan_y, lan_w, lan_h = 570, 670, 280, 55

# Virtual IP
vip_x, vip_y, vip_w, vip_h = 370, 980, 280, 85

# On-premises zone
op_x, op_y, op_w, op_h = 70, 1140, 870, 155
ds_x, ds_y, ds_w, ds_h = 105, 1175, 220, 75
rsp_x, rsp_y, rsp_w, rsp_h = 395, 1175, 240, 75
pbx_x, pbx_y, pbx_w, pbx_h = 700, 1175, 200, 75

# Note box
note_x, note_y, note_w, note_h = 780, 975, 270, 100


# ═══════════════════════════════════════════════════
# DRAW ZONES
# ═══════════════════════════════════════════════════

draw_zone(iz_x, iz_y, iz_w, iz_h,
          "INTERNET — EXTERNAL CONNECTIVITY (via Public IP)")
draw_zone(vpc_x, vpc_y, vpc_w, vpc_h, "AWS VPC")
draw_zone(ha_x, ha_y, ha_w, ha_h, "HA PROXY SBC PAIR")

# AZ B outline (around SBC #2)
draw.rounded_rectangle(
    [sbc2_x - 15, sbc2_y - 22, sbc2_x + sbc2_w + 15, sbc2_y + sbc2_h + 12],
    radius=5, fill=None, outline="#B0BEC5", width=1)
draw.text((sbc2_x - 10, sbc2_y - 20), "Availability Zone B",
          fill=AZ_COLOR, font=F_SMALL)

# AZ A outline (around SBC #1)
draw.rounded_rectangle(
    [sbc1_x - 15, sbc1_y - 22, sbc1_x + sbc1_w + 15, sbc1_y + sbc1_h + 12],
    radius=5, fill=None, outline="#B0BEC5", width=1)
draw.text((sbc1_x - 10, sbc1_y - 20), "Availability Zone A",
          fill=AZ_COLOR, font=F_SMALL)

# On-premises zone
draw_zone(op_x, op_y, op_w, op_h,
          "ON-PREMISES — INTERNAL CONNECTIVITY (via Direct Connect / VPN)")


# ═══════════════════════════════════════════════════
# DRAW COMPONENT BOXES
# ═══════════════════════════════════════════════════

draw_box(teams_x, teams_y, teams_w, teams_h,
         ["Microsoft Teams", "52.112.0.0/14", "(Inbound & Outbound)"])

draw_box(pstn_x, pstn_y, pstn_w, pstn_h,
         ["PSTN Provider", "(Internet SIP)", "(Outbound from SBC only)"])

draw_box(eip_x, eip_y, eip_w, eip_h,
         ["ELASTIC IP (Public)", "e.g., 54.x.x.x", "(Moves on failover)"])

draw_box(wan_x, wan_y, wan_w, wan_h,
         ["EXTERNAL INTERFACE (WAN)"])

draw_box(sbc2_x, sbc2_y, sbc2_w, sbc2_h,
         ["SBC #2 (STANDBY)", "Ready to take over on failure"])

draw_box(sbc1_x, sbc1_y, sbc1_w, sbc1_h,
         ["SBC #1 (ACTIVE)", "Handles all traffic"])

draw_box(lan_x, lan_y, lan_w, lan_h,
         ["INTERNAL INTERFACE (LAN)"])

draw_box(vip_x, vip_y, vip_w, vip_h,
         ["VIRTUAL IP", "10.x.x.x", "(Floats between SBC #1", "and #2)"])

draw_box(ds_x, ds_y, ds_w, ds_h,
         ["Downstream SBCs", "Sites with local endpoints"])

draw_box(rsp_x, rsp_y, rsp_w, rsp_h,
         ["Regional SIP Provider", "(AU/US)", "Local carrier via MPLS/DC"])

draw_box(pbx_x, pbx_y, pbx_w, pbx_h,
         ["3rd Party PBX", "On-prem integrations"])


# ═══════════════════════════════════════════════════
# DRAW NOTES
# ═══════════════════════════════════════════════════

draw_note(rt_x, rt_y, rt_w, rt_h, [
    "VPC Route Table points",
    "VIP to Active SBC",
    "(Updated on failover)"
])

draw_note(note_x, note_y, note_w, note_h, [
    "All internal entities connect",
    "to the SAME Virtual IP (10.x.x.x).",
    "They are unaware of which",
    "physical SBC is currently Active."
])


# ═══════════════════════════════════════════════════
# DRAW ARROWS
# ═══════════════════════════════════════════════════

teams_cx = teams_x + teams_w / 2
pstn_cx = pstn_x + pstn_w / 2
eip_cx = eip_x + eip_w / 2
wan_cx = wan_x + wan_w / 2
sbc2_cx = sbc2_x + sbc2_w / 2
sbc1_cx = sbc1_x + sbc1_w / 2
lan_cx = lan_x + lan_w / 2
vip_cx = vip_x + vip_w / 2

# 1. Microsoft Teams ↔ Elastic IP (bidirectional)
draw_bidir_v(teams_cx, teams_y + teams_h + 2, eip_y - 2,
             color=ARROW_BI, label="Inbound/Outbound", label_x_off=15)

# 2. PSTN Provider ← Elastic IP (outbound only — arrow goes UP from EIP to PSTN)
draw.line([(pstn_cx, eip_y - 2), (pstn_cx, pstn_y + pstn_h + 2)],
          fill=ARROW_UNI, width=2)
arrowhead(pstn_cx, pstn_y + pstn_h + 2, -math.pi / 2, size=8, color=ARROW_UNI)
draw.text((pstn_cx + 10, (eip_y + pstn_y + pstn_h) / 2 - 6),
          "Outbound only", fill=ARROW_UNI, font=F_LABEL)

# 3. Elastic IP ↔ External Interface WAN (bidirectional)
draw_bidir_v(eip_cx, eip_y + eip_h + 2, wan_y - 2,
             color=ARROW_BI, label="Inbound/Outbound", label_x_off=15)

# 4. WAN → SBC #2 (dashed, failover path)
dashed_line_v(wan_cx, wan_y + wan_h + 5, sbc2_y - 25,
              color=DASHED_COLOR, width=2)
arrowhead(wan_cx, sbc2_y - 25, math.pi / 2, size=7, color=DASHED_COLOR)
draw.text((wan_cx + 10, (wan_y + wan_h + sbc2_y - 25) / 2 - 4),
          "after failover", fill=AZ_COLOR, font=F_SMALL)

# 5. WAN → SBC #1 (Active) — solid line, routes left then down
bend_x = wan_x - 30
# Horizontal from WAN left edge to bend point
draw.line([(wan_x, wan_y + wan_h / 2), (bend_x, wan_y + wan_h / 2)],
          fill=ARROW_COLOR, width=2)
# Vertical from bend down to SBC #1 height
sbc1_cy = sbc1_y + sbc1_h / 2
draw.line([(bend_x, wan_y + wan_h / 2), (bend_x, sbc1_cy)],
          fill=ARROW_COLOR, width=2)
# Horizontal from bend to SBC #1
draw.line([(bend_x, sbc1_cy), (sbc1_x + sbc1_w + 2, sbc1_cy)],
          fill=ARROW_COLOR, width=2)
arrowhead(sbc1_x + sbc1_w + 2, sbc1_cy, math.pi, size=8, color=ARROW_COLOR)

# 6. HA Heartbeat links (dashed, between SBC #1 and SBC #2)
hb_positions = [sbc1_x + 50, sbc1_x + 170]
for i, hbx in enumerate(hb_positions):
    dashed_line_v(hbx, sbc2_y + sbc2_h + 5, sbc1_y - 25,
                  color=HA_COLOR, width=2, dash=5, gap=4)
    if i == 0:
        draw.text((hbx - 60, (sbc2_y + sbc2_h + sbc1_y) / 2 - 12),
                  "HA Link", fill=HA_COLOR, font=F_SMALL)
        draw.text((hbx - 68, (sbc2_y + sbc2_h + sbc1_y) / 2 + 2),
                  "Heartbeat", fill=HA_COLOR, font=F_SMALL)
    else:
        draw.text((hbx + 10, (sbc2_y + sbc2_h + sbc1_y) / 2 - 12),
                  "HA Link", fill=HA_COLOR, font=F_SMALL)
        draw.text((hbx + 10, (sbc2_y + sbc2_h + sbc1_y) / 2 + 2),
                  "Heartbeat", fill=HA_COLOR, font=F_SMALL)

# 7. SBC #1 (Active) ↔ Internal Interface (LAN) — bidirectional horizontal
lan_cy = lan_y + lan_h / 2
draw_bidir_h(lan_cy, sbc1_x + sbc1_w + 5, lan_x - 5, color=ARROW_BI)

# 8. Internal Interface (LAN) ↔ Virtual IP (bidirectional vertical)
draw_bidir_v(lan_cx, lan_y + lan_h + 2, vip_y - 2,
             color=ARROW_BI, label="Inbound/Outbound", label_x_off=15)

# 9. Virtual IP → On-premises entities (via Direct Connect/VPN)
# Three lines fanning out from VIP bottom to each on-prem box
ds_cx = ds_x + ds_w / 2
rsp_cx = rsp_x + rsp_w / 2
pbx_cx = pbx_x + pbx_w / 2

junction_y = vip_y + vip_h + 30

# Main vertical from VIP
draw.line([(vip_cx, vip_y + vip_h), (vip_cx, junction_y)],
          fill=ARROW_COLOR, width=2)

# Horizontal span
draw.line([(ds_cx, junction_y), (pbx_cx, junction_y)],
          fill=ARROW_COLOR, width=2)

# Three verticals down from junction to on-prem boxes
for cx in [ds_cx, rsp_cx, pbx_cx]:
    draw.line([(cx, junction_y), (cx, op_y + 30)], fill=ARROW_COLOR, width=2)
    arrowhead(cx, op_y + 30, math.pi / 2, size=8, color=ARROW_COLOR)

# "Direct Connect / VPN" labels
for cx in [ds_cx, rsp_cx, pbx_cx]:
    text = "Direct Connect / VPN"
    tw = draw.textlength(text, font=F_SMALL)
    draw.text((cx - tw / 2, junction_y + 6), text, fill=AZ_COLOR, font=F_SMALL)

# Small arrows from zone top area to each box
for cx, bx, by, bw, bh in [(ds_cx, ds_x, ds_y, ds_w, ds_h),
                             (rsp_cx, rsp_x, rsp_y, rsp_w, rsp_h),
                             (pbx_cx, pbx_x, pbx_y, pbx_w, pbx_h)]:
    draw.line([(cx, op_y + 30), (cx, by)], fill=ARROW_COLOR, width=2)
    arrowhead(cx, by, math.pi / 2, size=7, color=ARROW_COLOR)


# ═══════════════════════════════════════════════════
# LEGEND
# ═══════════════════════════════════════════════════

ly = H - 55
draw.text((60, ly), "Legend:", fill=TEXT_COLOR, font=F_LABEL)

# Bidirectional
lx1 = 120
draw.line([(lx1, ly + 7), (lx1 + 60, ly + 7)], fill=ARROW_BI, width=2)
arrowhead(lx1 + 60, ly + 7, 0, size=7, color=ARROW_BI)
arrowhead(lx1, ly + 7, math.pi, size=7, color=ARROW_BI)
draw.text((lx1 + 70, ly), "Bidirectional (Inbound/Outbound)",
          fill=ARROW_BI, font=F_SMALL)

# Unidirectional
lx2 = 500
draw.line([(lx2, ly + 7), (lx2 + 60, ly + 7)], fill=ARROW_UNI, width=2)
arrowhead(lx2 + 60, ly + 7, 0, size=7, color=ARROW_UNI)
draw.text((lx2 + 70, ly), "Outbound only (from SBC)",
          fill=ARROW_UNI, font=F_SMALL)

# Standard flow
lx3 = 780
draw.line([(lx3, ly + 7), (lx3 + 60, ly + 7)], fill=ARROW_COLOR, width=2)
arrowhead(lx3 + 60, ly + 7, 0, size=7, color=ARROW_COLOR)
draw.text((lx3 + 70, ly), "Connection flow",
          fill=ARROW_COLOR, font=F_SMALL)


# ═══════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════

out = "/home/kevin/public/png-diagrams/09-ha-connectivity-architecture-diagram.png"
img.save(out, "PNG", dpi=(150, 150))
print(f"Saved: {out}")
