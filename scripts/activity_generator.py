#!/usr/bin/env python3
# activity_generator.py

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
import json
import sys
import math
import random
import argparse
from typing import List, Dict, Any

# ============================================================
# Kid-perfect helpers
# ============================================================

def kid_stroke(width, height):
    sw = int(min(width, height) * 0.012)
    return max(4, min(sw, 12))

def kid_margin(width, height):
    return int(min(width, height) * 0.07)

def center_box(width, height):
    m = kid_margin(width, height)
    return m, m, width - 2*m, height - 2*m

# ============================================================
# Procedural subject renderers
# ============================================================

def draw_circle(c, W, H):
    x, y, w, h = center_box(W, H)
    r = min(w, h) * 0.35
    cx, cy = W/2, H/2
    c.circle(cx, cy, r, stroke=1, fill=0)

def draw_rounded_square(c, W, H):
    x, y, w, h = center_box(W, H)
    s = min(w, h) * 0.65
    r = s * 0.18
    x0 = (W - s) / 2
    y0 = (H - s) / 2
    c.roundRect(x0, y0, s, s, r, stroke=1, fill=0)

def draw_triangle(c, W, H):
    x, y, w, h = center_box(W, H)
    s = min(w, h) * 0.75
    cx, cy = W/2, H/2 + s*0.05
    p = c.beginPath()
    p.moveTo(cx, cy - 0.50*s)
    p.lineTo(cx - 0.50*s, cy + 0.35*s)
    p.lineTo(cx + 0.50*s, cy + 0.35*s)
    p.close()
    c.drawPath(p, stroke=1, fill=0)

def draw_star(c, W, H, points=5):
    x, y, w, h = center_box(W, H)
    R = min(w, h) * 0.36
    r = R * 0.45
    cx, cy = W/2, H/2
    pts = []
    for i in range(points*2):
        ang = math.pi/2 + i * math.pi/points
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad*math.cos(ang), cy - rad*math.sin(ang)))
    p = c.beginPath()
    p.moveTo(pts[0][0], pts[0][1])
    for px, py in pts[1:]:
        p.lineTo(px, py)
    p.close()
    c.drawPath(p, stroke=1, fill=0)

def draw_heart(c, W, H):
    x, y, w, h = center_box(W, H)
    s = min(w, h) * 0.55
    cx, cy = W/2, H/2 + s*0.05
    p = c.beginPath()
    p.moveTo(cx, cy + 0.28*s)
    p.curveTo(cx - 0.60*s, cy - 0.20*s, cx - 0.18*s, cy - 0.65*s, cx, cy - 0.30*s)
    p.curveTo(cx + 0.18*s, cy - 0.65*s, cx + 0.60*s, cy - 0.20*s, cx, cy + 0.28*s)
    p.close()
    c.drawPath(p, stroke=1, fill=0)

def draw_cloud(c, W, H):
    x, y, w, h = center_box(W, H)
    cx, cy = W/2, H/2
    R = min(w, h)*0.20
    c.circle(cx - 1.1*R, cy + 0.2*R, 0.9*R, stroke=1, fill=0)
    c.circle(cx - 0.3*R, cy - 0.2*R, 1.05*R, stroke=1, fill=0)
    c.circle(cx + 0.7*R, cy + 0.1*R, 0.85*R, stroke=1, fill=0)
    c.line(cx - 1.5*R, cy + 0.8*R, cx + 1.5*R, cy + 0.8*R)

def draw_leaf(c, W, H):
    cx, cy = W/2, int(H*0.52)
    s = min(W, H) * 0.48
    p = c.beginPath()
    p.moveTo(cx, cy - 0.60*s)
    p.curveTo(cx + 0.55*s, cy - 0.55*s, cx + 0.65*s, cy + 0.10*s, cx, cy + 0.65*s)
    p.curveTo(cx - 0.65*s, cy + 0.10*s, cx - 0.55*s, cy - 0.55*s, cx, cy - 0.60*s)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    c.line(cx, cy - 0.55*s, cx, cy + 0.72*s)
    vr = c.beginPath()
    vr.moveTo(cx, cy + 0.10*s)
    vr.curveTo(cx + 0.25*s, cy, cx + 0.30*s, cy - 0.15*s, cx + 0.35*s, cy - 0.25*s)
    c.drawPath(vr, stroke=1, fill=0)
    vl = c.beginPath()
    vl.moveTo(cx, cy)
    vl.curveTo(cx - 0.22*s, cy - 0.10*s, cx - 0.30*s, cy - 0.22*s, cx - 0.38*s, cy - 0.30*s)
    c.drawPath(vl, stroke=1, fill=0)

def draw_acorn(c, W, H):
    cx, cy = W/2, H/2
    s = min(W, H) * 0.50
    body = c.beginPath()
    body.moveTo(cx, cy - 0.10*s)
    body.curveTo(cx + 0.48*s, cy - 0.05*s, cx + 0.48*s, cy + 0.55*s, cx, cy + 0.60*s)
    body.curveTo(cx - 0.48*s, cy + 0.55*s, cx - 0.48*s, cy - 0.05*s, cx, cy - 0.10*s)
    body.close()
    c.drawPath(body, stroke=1, fill=0)
    cap_top = c.beginPath()
    cap_top.moveTo(cx - 0.55*s, cy - 0.02*s)
    cap_top.curveTo(cx - 0.15*s, cy - 0.35*s, cx + 0.15*s, cy - 0.35*s, cx + 0.55*s, cy - 0.02*s)
    c.drawPath(cap_top, stroke=1, fill=0)
    sc = c.beginPath()
    sc.moveTo(cx - 0.55*s, cy - 0.02*s)
    sc.curveTo(cx - 0.40*s, cy + 0.10*s, cx - 0.20*s, cy + 0.10*s, cx - 0.05*s, cy - 0.02*s)
    sc.curveTo(cx + 0.10*s, cy + 0.10*s, cx + 0.30*s, cy + 0.10*s, cx + 0.45*s, cy - 0.02*s)
    c.drawPath(sc, stroke=1, fill=0)
    st = c.beginPath()
    st.moveTo(cx + 0.10*s, cy - 0.30*s)
    st.curveTo(cx + 0.20*s, cy - 0.45*s, cx + 0.05*s, cy - 0.55*s, cx - 0.05*s, cy - 0.48*s)
    c.drawPath(st, stroke=1, fill=0)

def draw_mushroom(c, W, H):
    x, y, w, h = center_box(W, H)
    s = min(w, h) * 0.65
    cx, cy = W/2, H/2
    cap = c.beginPath()
    cap.moveTo(cx - 0.55*s, cy)
    cap.curveTo(cx - 0.20*s, cy - 0.60*s, cx + 0.20*s, cy - 0.60*s, cx + 0.55*s, cy)
    c.drawPath(cap, stroke=1, fill=0)
    brim = c.beginPath()
    brim.moveTo(cx - 0.55*s, cy)
    brim.curveTo(cx - 0.20*s, cy + 0.25*s, cx + 0.20*s, cy + 0.25*s, cx + 0.55*s, cy)
    c.drawPath(brim, stroke=1, fill=0)
    wst = 0.24*s; hst = 0.55*s; rx = 0.10*s
    x0, y0 = cx - wst/2, cy
    c.roundRect(x0, y0, wst, hst, rx, stroke=1, fill=0)
    c.circle(cx - 0.25*s, cy - 0.18*s, 0.06*s, stroke=1, fill=0)
    c.circle(cx + 0.15*s, cy - 0.22*s, 0.07*s, stroke=1, fill=0)
    c.circle(cx,          cy - 0.05*s, 0.05*s, stroke=1, fill=0)

def draw_pine_tree(c, W, H):
    x, y, w, h = center_box(W, H)
    s = min(w, h) * 0.75
    cx, cy = W/2, H/2 + s*0.05
    def tri(top_y, base_w, base_y):
        p = c.beginPath()
        p.moveTo(cx, top_y)
        p.lineTo(cx - base_w/2, base_y)
        p.lineTo(cx + base_w/2, base_y)
        p.close()
        c.drawPath(p, stroke=1, fill=0)
    tri(cy - 0.55*s, 0.55*s, cy - 0.25*s)
    tri(cy - 0.35*s, 0.70*s, cy - 0.05*s)
    tri(cy - 0.15*s, 0.85*s, cy + 0.15*s)
    wst = 0.14*s; hst = 0.30*s; rx = 0.04*s
    x0, y0 = cx - wst/2, cy + 0.15*s
    c.roundRect(x0, y0, wst, hst, rx, stroke=1, fill=0)

def draw_sun(c, W, H):
    x, y, w, h = center_box(W, H)
    cx, cy = W/2, H/2
    r = min(w, h)*0.28
    c.circle(cx, cy, r, stroke=1, fill=0)
    for i in range(12):
        ang = i * (2*math.pi/12.0)
        r1 = r*1.25
        r2 = r*1.55
        x1, y1 = cx + r1*math.cos(ang), cy + r1*math.sin(ang)
        x2, y2 = cx + r2*math.cos(ang), cy + r2*math.sin(ang)
        c.line(x1, y1, x2, y2)

def draw_raindrop(c, W, H):
    x, y, w, h = center_box(W, H)
    s = min(w, h)*0.60
    cx, cy = W/2, H/2
    p = c.beginPath()
    p.moveTo(cx, cy - 0.45*s)
    p.curveTo(cx + 0.26*s, cy - 0.10*s, cx + 0.26*s, cy + 0.35*s, cx, cy + 0.42*s)
    p.curveTo(cx - 0.26*s, cy + 0.35*s, cx - 0.26*s, cy - 0.10*s, cx, cy - 0.45*s)
    p.close()
    c.drawPath(p, stroke=1, fill=0)

RENDERERS = {
    "circle": draw_circle,
    "rounded square": draw_rounded_square,
    "square": draw_rounded_square,
    "triangle": draw_triangle,
    "star": draw_star,
    "heart": draw_heart,
    "cloud": draw_cloud,
    "leaf": draw_leaf,
    "acorn": draw_acorn,
    "mushroom": draw_mushroom,
    "pine tree": draw_pine_tree,
    "tree": draw_pine_tree,
    "sun": draw_sun,
    "raindrop": draw_raindrop,
    "drop": draw_raindrop,
}

SYNONYMS = {
    "wobbly circle": "circle",
    "rounded-square": "rounded square",
    "smiling star": "star",
    "spiky sun": "sun",
    "striped mushroom": "mushroom",
    "dotted leaf": "leaf",
}

# ============================================================
# Generator class
# ============================================================

class ActivityBookletGenerator:
    def __init__(self, output_file):
        self.c = canvas.Canvas(output_file, pagesize=A4)
        self.width, self.height = A4
        self.margin = max(0.75 * inch, kid_margin(self.width, self.height))

    def draw_border(self):
        self.c.setStrokeColor(colors.HexColor('#FF69B4'))
        self.c.setLineWidth(3)
        self.c.rect(self.margin/2, self.margin/2,
                    self.width - self.margin,
                    self.height - self.margin)

    def draw_title(self, title, y_offset=50):
        self.c.setFont("Helvetica-Bold", 24)
        self.c.setFillColor(colors.HexColor('#4A90E2'))
        self.c.drawCentredString(self.width/2, self.height - y_offset, title)

    def draw_instruction(self, instruction, y_offset=80):
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(colors.black)
        self.c.drawCentredString(self.width/2, self.height - y_offset, instruction)

    def _prep_kid_lines(self):
        self.c.setLineWidth(kid_stroke(self.width, self.height))
        self.c.setStrokeColor(colors.black)
        self.c.setFillColor(colors.white)

    def create_coloring_page(self, page_data):
        self.draw_border()
        self.draw_title(page_data.get('title', 'Coloring Page'))
        self.draw_instruction(page_data.get('instruction', 'Use your favorite crayons!'))
        subject = (page_data.get('subject') or page_data.get('subjectHint') or 'circle').lower().strip()
        subject = SYNONYMS.get(subject, subject)
        self._prep_kid_lines()
        renderer = RENDERERS.get(subject)
        if renderer:
            renderer(self.c, self.width, self.height)
        else:
            draw_circle(self.c, self.width, self.height)

    def create_tracing_page(self, page_data):
        self.draw_border()
        self.draw_title(page_data.get('title', 'Tracing'))
        self.draw_instruction("Trace over the dotted lines")
        content = page_data.get('content', 'A')
        repetitions = page_data.get('repetitions', 12)

        cols = 3
        rows = math.ceil(repetitions / cols)
        start_y = self.height - 150
        spacing_x = (self.width - 2 * self.margin) / cols
        spacing_y = (self.height - 250) / rows

        self.c.setFont("Helvetica-Bold", 72)
        self.c.setDash(6, 6)
        self.c.setStrokeGray(0.5)
        self.c.setFillGray(0.0)

        for row in range(rows):
            for col in range(cols):
                if row * cols + col >= repetitions:
                    break
                x = self.margin + col * spacing_x + spacing_x/2 - 30
                y = start_y - row * spacing_y
                self.c.drawString(x, y, str(content))
        self.c.setDash()

    def create_counting_page(self, page_data):
        self.draw_border()
        self.draw_title(page_data.get('title', 'Count'))
        self.draw_instruction("Count and write the number")

        count = page_data.get('count', 5)
        item = page_data.get('item', 'circle')

        self.c.setLineWidth(max(2, kid_stroke(self.width, self.height) - 2))
        self.c.setStrokeColor(colors.black)

        cols = min(5, count)
        rows = math.ceil(count / cols)
        start_x = self.width / 2 - (cols * 60) / 2
        start_y = self.height - 220

        for i in range(count):
            row = i // cols
            col = i % cols
            x = start_x + col * 60
            y = start_y - row * 60

            if 'circle' in item.lower():
                self.c.circle(x, y, 20, stroke=1, fill=0)
            elif 'star' in item.lower():
                pts = []
                for j in range(10):
                    angle = math.radians(j * 36 - 90)
                    radius = 20 if j % 2 == 0 else 10
                    px = x + radius * math.cos(angle)
                    py = y + radius * math.sin(angle)
                    pts.append((px, py))
                p = self.c.beginPath()
                p.moveTo(pts[0][0], pts[0][1])
                for pt in pts[1:]:
                    p.lineTo(pt[0], pt[1])
                p.close()
                self.c.drawPath(p, stroke=1, fill=0)
            elif 'heart' in item.lower():
                p = self.c.beginPath()
                p.moveTo(x, y - 15)
                p.curveTo(x - 20, y + 10, x - 15, y + 15, x, y + 5)
                p.curveTo(x + 15, y + 15, x + 20, y + 10, x, y - 15)
                self.c.drawPath(p, stroke=1, fill=0)
            else:
                self.c.rect(x - 15, y - 15, 30, 30, stroke=1, fill=0)

        self.c.setFont("Helvetica", 18)
        self.c.setFillColor(colors.black)
        self.c.drawCentredString(self.width/2, 150, "How many? Write your answer:")
        self.c.setStrokeColor(colors.black)
        self.c.setLineWidth(2)
        self.c.rect(self.width/2 - 40, 100, 80, 60, stroke=1, fill=0)

    def create_maze_page(self, page_data):
        self.draw_border()
        self.draw_title(page_data.get('title', 'Maze'))
        self.draw_instruction("Help find the way through the maze!")

        maze_size = 7
        cell_size = 50
        start_x = self.width / 2 - (maze_size * cell_size) / 2
        start_y = self.height / 2 + (maze_size * cell_size) / 2

        self.c.setLineWidth(max(3, kid_stroke(self.width, self.height) - 1))
        self.c.setStrokeColor(colors.black)

        walls = [
            (0, 0, 3), (4, 0, 3), (1, 1, 2), (5, 1, 2),
            (0, 2, 2), (3, 2, 2), (6, 2, 1), (1, 3, 1),
            (3, 3, 3), (0, 4, 2), (4, 4, 3), (2, 5, 2),
            (5, 5, 2), (0, 6, 2), (3, 6, 4),
        ]

        self.c.rect(start_x, start_y - maze_size * cell_size,
                    maze_size * cell_size, maze_size * cell_size, stroke=1, fill=0)

        for x, y, length in walls:
            wall_x = start_x + x * cell_size
            wall_y = start_y - (y + 1) * cell_size
            self.c.line(wall_x, wall_y, wall_x + length * cell_size, wall_y)

        self.c.setFillColor(colors.green)
        self.c.circle(start_x + cell_size/2, start_y - cell_size/2, 8, stroke=0, fill=1)
        self.c.setFillColor(colors.red)
        self.c.circle(start_x + (maze_size - 0.5) * cell_size,
                      start_y - (maze_size - 0.5) * cell_size, 8, stroke=0, fill=1)

        self.c.setFillColor(colors.black)
        self.c.setFont("Helvetica-Bold", 12)
        self.c.drawString(start_x - 40, start_y - cell_size/2, "START")
        self.c.drawString(start_x + maze_size * cell_size + 10,
                          start_y - (maze_size - 0.5) * cell_size, "END")

    def create_matching_page(self, page_data):
        self.draw_border()
        self.draw_title(page_data.get('title', 'Match the Pairs'))
        self.draw_instruction("Draw lines to match the pairs!")

        pairs = page_data.get('pairs', [])
        left_x = self.width * 0.25
        right_x = self.width * 0.75
        start_y = self.height - 150
        spacing = 100

        self.c.setLineWidth(max(2, kid_stroke(self.width, self.height) - 2))
        self.c.setStrokeColor(colors.black)

        right_items = [pair[1] if isinstance(pair, list) else pair for pair in pairs]
        random.shuffle(right_items)

        for i, pair in enumerate(pairs):
            if i >= 4:
                break
            y = start_y - i * spacing
            left_item = pair[0] if isinstance(pair, list) else pair
            self.draw_matching_item(left_x, y, left_item)
            self.draw_matching_item(right_x, y, right_items[i])
            self.c.circle(left_x + 40, y, 5, stroke=1, fill=0)
            self.c.circle(right_x - 40, y, 5, stroke=1, fill=0)

    def draw_matching_item(self, x, y, item):
        if isinstance(item, dict):
            item_type = item.get('type', 'shape')
            if item_type == 'shape':
                shape = item.get('shape', 'circle')
                if shape == 'circle':
                    self.c.circle(x, y, 25, stroke=1, fill=0)
                elif shape == 'square':
                    self.c.rect(x - 25, y - 25, 50, 50, stroke=1, fill=0)
                elif shape == 'triangle':
                    p = self.c.beginPath()
                    p.moveTo(x, y + 25)
                    p.lineTo(x - 25, y - 25)
                    p.lineTo(x + 25, y - 25)
                    p.close()
                    self.c.drawPath(p, stroke=1, fill=0)
            elif item_type == 'number':
                self.c.setFont("Helvetica-Bold", 36)
                self.c.drawCentredString(x, y - 12, str(item.get('value', '1')))
            elif item_type == 'color':
                try:
                    self.c.setFillColor(colors.HexColor(item.get('color', '#000000')))
                    self.c.circle(x, y, 25, stroke=1, fill=1)
                    self.c.setFillColor(colors.black)
                except Exception:
                    self.c.circle(x, y, 25, stroke=1, fill=0)

    def create_dot_to_dot_page(self, page_data):
        self.draw_border()
        self.draw_title(page_data.get('title', 'Connect the Dots'))
        dots_count = page_data.get('dots', 12)
        self.draw_instruction(f"Connect 1 to {dots_count}")

        if 'dot_positions' not in page_data:
            page_data['dot_positions'] = self.generate_dot_positions(
                page_data.get('shape', 'star'), dots_count)

        dots = page_data['dot_positions']
        self.c.setFont("Helvetica-Bold", 12)
        self.c.setFillColor(colors.black)

        for i, (x, y) in enumerate(dots[:dots_count], 1):
            self.c.circle(x, y, 4, stroke=1, fill=1)
            self.c.drawCentredString(x, y + 10, str(i))

    def generate_dot_positions(self, shape='star', num_dots=15):
        center_x = self.width / 2
        center_y = self.height / 2
        dots = []

        if shape == 'star':
            for i in range(num_dots):
                angle = (i / num_dots) * 2 * math.pi
                radius = 110 if i % 2 == 0 else 60
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                dots.append((x, y))
        elif shape == 'circle':
            for i in range(num_dots):
                angle = (i / num_dots) * 2 * math.pi
                radius = 110
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                dots.append((x, y))
        elif shape == 'heart':
            for i in range(num_dots):
                t = (i / num_dots) * 2 * math.pi
                x = center_x + 60 * (16 * math.sin(t) ** 3) / 16
                y = center_y + 60 * (13 * math.cos(t) - 5 * math.cos(2*t) -
                                      2 * math.cos(3*t) - math.cos(4*t)) / 13
                dots.append((x, y))
        return dots

    def save(self):
        self.c.save()

# ============================================================
# Runner + TEST MODE
# ============================================================

def generate_booklet(pages_data: List[Dict[str, Any]], output_file: str):
    generator = ActivityBookletGenerator(output_file)
    for page in pages_data:
        page_type = page.get('type', 'coloring')
        if page_type == 'coloring':
            generator.create_coloring_page(page)
        elif page_type == 'tracing':
            generator.create_tracing_page(page)
        elif page_type == 'counting':
            generator.create_counting_page(page)
        elif page_type == 'maze':
            generator.create_maze_page(page)
        elif page_type == 'matching':
            generator.create_matching_page(page)
        elif page_type == 'dot-to-dot':
            if 'dot_positions' not in page:
                page['dot_positions'] = generator.generate_dot_positions(
                    page.get('shape', 'star'), page.get('dots', 15))
            generator.create_dot_to_dot_page(page)
        generator.c.showPage()
    generator.save()
    print(f"Booklet generated: {output_file}")

def sample_pages() -> List[Dict[str, Any]]:
    # 6-page friendly preview
    return [
        {"type": "coloring", "title": "Color the Leaf",      "instruction": "Use your favorite crayons!", "subject": "leaf"},
        {"type": "coloring", "title": "Color the Acorn",     "instruction": "Big bold lines!",            "subject": "acorn"},
        {"type": "coloring", "title": "Color the Mushroom",  "instruction": "Keep inside the lines!",     "subject": "mushroom"},
        {"type": "coloring", "title": "Color the Pine Tree", "instruction": "One big outline!",           "subject": "pine tree"},
        {"type": "coloring", "title": "Color the Cloud",     "instruction": "Add a sky if you like!",     "subject": "cloud"},
        {"type": "coloring", "title": "Color the Square",    "instruction": "Go wild with colors!",       "subject": "rounded square"},
    ]

def parse_args():
    p = argparse.ArgumentParser(description="Generate a children's activity booklet PDF.")
    p.add_argument("input_json", nargs="?", help="Path to input JSON (list of page specs).")
    p.add_argument("output_pdf", nargs="?", help="Path to output PDF.")
    p.add_argument("--test", action="store_true", help="Generate a 6-page test booklet without an input JSON.")
    p.add_argument("--output", help="Output PDF path for --test mode (default: test.pdf).")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()

    if args.test:
        out = args.output or "test.pdf"
        pages = sample_pages()
        generate_booklet(pages, out)
        sys.exit(0)

    if not args.input_json or not args.output_pdf:
        print("Usage:")
        print("  python3 activity_generator.py <input_json> <output_pdf>")
        print("  python3 activity_generator.py --test [--output test.pdf]")
        sys.exit(1)

    with open(args.input_json, "r") as f:
        pages_data = json.load(f)

    generate_booklet(pages_data, args.output_pdf)
