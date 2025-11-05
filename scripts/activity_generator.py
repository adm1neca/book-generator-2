from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
import json
import sys
import math
import random

class ActivityBookletGenerator:
    def __init__(self, output_file):
        self.c = canvas.Canvas(output_file, pagesize=A4)
        self.width, self.height = A4
        self.margin = 0.75 * inch
        
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

    def create_coloring_page(self, page_data):
        """Generate a coloring page with simple shapes"""
        self.draw_border()
        self.draw_title(page_data.get('title', 'Coloring Page'))
        self.draw_instruction(page_data.get('instruction', 'Color me in!'))

        subject = page_data.get('subject', 'circle').lower()
        center_x = self.width / 2
        center_y = self.height / 2

        self.c.setLineWidth(4)
        self.c.setStrokeColor(colors.black)
        self.c.setFillColor(colors.white)

        # PIG
        if 'pig' in subject:
            # Body
            self.c.circle(center_x, center_y, 100, stroke=1, fill=1)
            # Ears
            self.c.ellipse(center_x - 80, center_y + 60, center_x - 40, center_y + 120, stroke=1, fill=1)
            self.c.ellipse(center_x + 40, center_y + 60, center_x + 80, center_y + 120, stroke=1, fill=1)
            # Eyes
            self.c.circle(center_x - 30, center_y + 20, 12, stroke=1, fill=1)
            self.c.circle(center_x + 30, center_y + 20, 12, stroke=1, fill=1)
            # Snout
            self.c.ellipse(center_x - 40, center_y - 40, center_x + 40, center_y - 10, stroke=1, fill=1)
            # Nostrils
            self.c.circle(center_x - 15, center_y - 25, 6, stroke=1, fill=1)
            self.c.circle(center_x + 15, center_y - 25, 6, stroke=1, fill=1)

        # DOG
        elif 'dog' in subject or 'puppy' in subject:
            # Head
            self.c.circle(center_x, center_y + 20, 80, stroke=1, fill=1)
            # Ears (floppy)
            self.c.ellipse(center_x - 100, center_y, center_x - 60, center_y + 80, stroke=1, fill=1)
            self.c.ellipse(center_x + 60, center_y, center_x + 100, center_y + 80, stroke=1, fill=1)
            # Eyes
            self.c.circle(center_x - 25, center_y + 40, 10, stroke=1, fill=1)
            self.c.circle(center_x + 25, center_y + 40, 10, stroke=1, fill=1)
            # Nose
            path = self.c.beginPath()
            path.moveTo(center_x, center_y)
            path.lineTo(center_x - 15, center_y + 15)
            path.lineTo(center_x + 15, center_y + 15)
            path.close()
            self.c.drawPath(path, stroke=1, fill=1)
            # Smile
            self.c.arc(center_x - 30, center_y - 40, center_x + 30, center_y, 180, 360)

        # CAT
        elif 'cat' in subject:
            # Head
            self.c.circle(center_x, center_y, 90, stroke=1, fill=1)
            # Pointy ears
            path1 = self.c.beginPath()
            path1.moveTo(center_x - 60, center_y + 90)
            path1.lineTo(center_x - 70, center_y + 140)
            path1.lineTo(center_x - 40, center_y + 100)
            path1.close()
            self.c.drawPath(path1, stroke=1, fill=1)

            path2 = self.c.beginPath()
            path2.moveTo(center_x + 60, center_y + 90)
            path2.lineTo(center_x + 70, center_y + 140)
            path2.lineTo(center_x + 40, center_y + 100)
            path2.close()
            self.c.drawPath(path2, stroke=1, fill=1)
            # Eyes
            self.c.ellipse(center_x - 35, center_y + 10, center_x - 15, center_y + 40, stroke=1, fill=1)
            self.c.ellipse(center_x + 15, center_y + 10, center_x + 35, center_y + 40, stroke=1, fill=1)
            # Whiskers
            self.c.setLineWidth(2)
            self.c.line(center_x - 90, center_y + 10, center_x - 50, center_y + 15)
            self.c.line(center_x - 90, center_y, center_x - 50, center_y)
            self.c.line(center_x + 50, center_y + 15, center_x + 90, center_y + 10)
            self.c.line(center_x + 50, center_y, center_x + 90, center_y)
            self.c.setLineWidth(4)

        # BUTTERFLY
        elif 'butterfly' in subject:
            # Body
            self.c.ellipse(center_x - 8, center_y - 60, center_x + 8, center_y + 60, stroke=1, fill=1)
            # Top wings
            self.c.ellipse(center_x - 80, center_y + 20, center_x - 10, center_y + 100, stroke=1, fill=1)
            self.c.ellipse(center_x + 10, center_y + 20, center_x + 80, center_y + 100, stroke=1, fill=1)
            # Bottom wings
            self.c.ellipse(center_x - 70, center_y - 60, center_x - 10, center_y + 10, stroke=1, fill=1)
            self.c.ellipse(center_x + 10, center_y - 60, center_x + 70, center_y + 10, stroke=1, fill=1)
            # Antennae
            self.c.line(center_x - 5, center_y + 60, center_x - 20, center_y + 90)
            self.c.line(center_x + 5, center_y + 60, center_x + 20, center_y + 90)
            self.c.circle(center_x - 20, center_y + 90, 5, stroke=1, fill=1)
            self.c.circle(center_x + 20, center_y + 90, 5, stroke=1, fill=1)

        # SUN
        elif 'sun' in subject:
            # Center circle
            self.c.circle(center_x, center_y, 60, stroke=1, fill=1)
            # Rays
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                x1 = center_x + 70 * math.cos(rad)
                y1 = center_y + 70 * math.sin(rad)
                x2 = center_x + 110 * math.cos(rad)
                y2 = center_y + 110 * math.sin(rad)
                self.c.line(x1, y1, x2, y2)
            # Face
            self.c.circle(center_x - 20, center_y + 15, 8, stroke=1, fill=1)
            self.c.circle(center_x + 20, center_y + 15, 8, stroke=1, fill=1)
            self.c.arc(center_x - 30, center_y - 40, center_x + 30, center_y - 5, 180, 360)

        # BALLOON
        elif 'balloon' in subject:
            # Balloon
            path = self.c.beginPath()
            path.moveTo(center_x, center_y - 80)
            path.curveTo(center_x - 80, center_y - 60, center_x - 80, center_y + 40, center_x, center_y + 80)
            path.curveTo(center_x + 80, center_y + 40, center_x + 80, center_y - 60, center_x, center_y - 80)
            self.c.drawPath(path, stroke=1, fill=1)
            # Knot
            self.c.circle(center_x, center_y + 85, 8, stroke=1, fill=1)
            # String
            self.c.line(center_x, center_y + 85, center_x, center_y + 150)

        # RAINBOW
        elif 'rainbow' in subject:
            # Draw arcs for rainbow
            colors_list = [70, 60, 50, 40, 30, 20, 10]
            for i, size in enumerate(colors_list):
                radius = 120 - (i * 15)
                self.c.arc(center_x - radius, center_y - 150, 
                          center_x + radius, center_y + 150, 0, 180)

        # BADGE (Paw Patrol)
        elif 'badge' in subject:
            # Star badge
            points = []
            for i in range(10):
                angle = math.radians(i * 36 - 90)
                radius = 100 if i % 2 == 0 else 50
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.append((x, y))
            path = self.c.beginPath()
            path.moveTo(points[0][0], points[0][1])
            for point in points[1:]:
                path.lineTo(point[0], point[1])
            path.close()
            self.c.drawPath(path, stroke=1, fill=1)
            # Circle in center
            self.c.circle(center_x, center_y, 30, stroke=1, fill=1)

        # BONE
        elif 'bone' in subject:
            # Center rectangle
            self.c.rect(center_x - 60, center_y - 15, 120, 30, stroke=1, fill=1)
            # Left circles
            self.c.circle(center_x - 60, center_y - 15, 20, stroke=1, fill=1)
            self.c.circle(center_x - 60, center_y + 15, 20, stroke=1, fill=1)
            # Right circles
            self.c.circle(center_x + 60, center_y - 15, 20, stroke=1, fill=1)
            self.c.circle(center_x + 60, center_y + 15, 20, stroke=1, fill=1)

        # PAW PRINT
        elif 'paw' in subject:
            # Main pad
            self.c.ellipse(center_x - 40, center_y - 50, center_x + 40, center_y + 10, stroke=1, fill=1)
            # Toe pads
            self.c.ellipse(center_x - 50, center_y + 10, center_x - 20, center_y + 40, stroke=1, fill=1)
            self.c.ellipse(center_x - 20, center_y + 20, center_x + 10, center_y + 55, stroke=1, fill=1)
            self.c.ellipse(center_x + 10, center_y + 20, center_x + 40, center_y + 55, stroke=1, fill=1)
            self.c.ellipse(center_x + 20, center_y + 10, center_x + 50, center_y + 40, stroke=1, fill=1)

        # TRIANGLE (shape)
        elif 'triangle' in subject:
            path = self.c.beginPath()
            path.moveTo(center_x, center_y + 100)
            path.lineTo(center_x - 100, center_y - 100)
            path.lineTo(center_x + 100, center_y - 100)
            path.close()
            self.c.drawPath(path, stroke=1, fill=1)

        # CIRCLE (shape - default with smiley)
        elif 'circle' in subject or 'ball' in subject:
            self.c.circle(center_x, center_y, 120, stroke=1, fill=1)
            self.c.circle(center_x - 40, center_y + 30, 15, stroke=1, fill=1)
            self.c.circle(center_x + 40, center_y + 30, 15, stroke=1, fill=1)
            self.c.arc(center_x - 60, center_y - 80, center_x + 60, center_y - 20, 180, 360)

        # HEART
        elif 'heart' in subject:
            path = self.c.beginPath()
            path.moveTo(center_x, center_y - 80)
            path.curveTo(center_x - 100, center_y + 60, center_x - 80, center_y + 100, center_x, center_y + 20)
            path.curveTo(center_x + 80, center_y + 100, center_x + 100, center_y + 60, center_x, center_y - 80)
            self.c.drawPath(path, stroke=1, fill=1)

        # STAR
        elif 'star' in subject:
            points = []
            for i in range(10):
                angle = math.radians(i * 36 - 90)
                radius = 100 if i % 2 == 0 else 45
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.append((x, y))
            path = self.c.beginPath()
            path.moveTo(points[0][0], points[0][1])
            for point in points[1:]:
                path.lineTo(point[0], point[1])
            path.close()
            self.c.drawPath(path, stroke=1, fill=1)

        # FLOWER
        elif 'flower' in subject:
            self.c.circle(center_x, center_y, 25, stroke=1, fill=1)
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                x = center_x + 60 * math.cos(rad)
                y = center_y + 60 * math.sin(rad)
                self.c.circle(x, y, 35, stroke=1, fill=1)
            self.c.setLineWidth(6)
            self.c.line(center_x, center_y - 25, center_x, center_y - 120)
            self.c.ellipse(center_x - 40, center_y - 80, center_x - 10, center_y - 50, stroke=1, fill=1)
            self.c.ellipse(center_x + 10, center_y - 100, center_x + 40, center_y - 70, stroke=1, fill=1)

        # HOUSE
        elif 'house' in subject:
            self.c.rect(center_x - 80, center_y - 60, 160, 120, stroke=1, fill=1)
            path = self.c.beginPath()
            path.moveTo(center_x - 100, center_y + 60)
            path.lineTo(center_x, center_y + 130)
            path.lineTo(center_x + 100, center_y + 60)
            path.close()
            self.c.drawPath(path, stroke=1, fill=1)
            self.c.rect(center_x - 25, center_y - 60, 50, 70, stroke=1, fill=1)
            self.c.rect(center_x - 65, center_y + 10, 35, 35, stroke=1, fill=1)
            self.c.rect(center_x + 30, center_y + 10, 35, 35, stroke=1, fill=1)

        # DEFAULT FALLBACK
        else:
            self.c.circle(center_x, center_y, 100, stroke=1, fill=1)
            self.c.circle(center_x - 35, center_y + 30, 12, stroke=1, fill=1)
            self.c.circle(center_x + 35, center_y + 30, 12, stroke=1, fill=1)
            self.c.arc(center_x - 50, center_y - 60, center_x + 50, center_y - 10, 180, 360)
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
        self.c.setFillGray(0.85)
        
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
        
        self.c.setLineWidth(3)
        self.c.setStrokeColor(colors.black)
        
        cols = min(5, count)
        rows = math.ceil(count / cols)
        start_x = self.width / 2 - (cols * 60) / 2
        start_y = self.height - 200
        
        for i in range(count):
            row = i // cols
            col = i % cols
            x = start_x + col * 60
            y = start_y - row * 60
            
            if 'circle' in item.lower():
                self.c.circle(x, y, 20, stroke=1, fill=0)
            elif 'star' in item.lower():
                self.c.setFillColor(colors.white)
                points = []
                for j in range(10):
                    angle = math.radians(j * 36 - 90)
                    radius = 20 if j % 2 == 0 else 10
                    px = x + radius * math.cos(angle)
                    py = y + radius * math.sin(angle)
                    points.append((px, py))
                path = self.c.beginPath()
                path.moveTo(points[0][0], points[0][1])
                for point in points[1:]:
                    path.lineTo(point[0], point[1])
                path.close()
                self.c.drawPath(path, stroke=1, fill=1)
            elif 'heart' in item.lower():
                path = self.c.beginPath()
                path.moveTo(x, y - 15)
                path.curveTo(x - 20, y + 10, x - 15, y + 15, x, y + 5)
                path.curveTo(x + 15, y + 15, x + 20, y + 10, x, y - 15)
                self.c.drawPath(path, stroke=1, fill=1)
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
        
        self.c.setLineWidth(3)
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
        
        self.c.setLineWidth(2)
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
                    path = self.c.beginPath()
                    path.moveTo(x, y + 25)
                    path.lineTo(x - 25, y - 25)
                    path.lineTo(x + 25, y - 25)
                    path.close()
                    self.c.drawPath(path, stroke=1, fill=0)
            elif item_type == 'number':
                self.c.setFont("Helvetica-Bold", 36)
                self.c.drawCentredString(x, y - 12, str(item.get('value', '1')))
            elif item_type == 'color':
                try:
                    self.c.setFillColor(colors.HexColor(item.get('color', '#000000')))
                    self.c.circle(x, y, 25, stroke=1, fill=1)
                    self.c.setFillColor(colors.black)
                except:
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
                radius = 100 if i % 2 == 0 else 50
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                dots.append((x, y))
        elif shape == 'circle':
            for i in range(num_dots):
                angle = (i / num_dots) * 2 * math.pi
                radius = 100
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                dots.append((x, y))
        elif shape == 'heart':
            for i in range(num_dots):
                t = (i / num_dots) * 2 * math.pi
                x = center_x + 100 * (16 * math.sin(t) ** 3)
                y = center_y + 100 * (13 * math.cos(t) - 5 * math.cos(2*t) - 
                                      2 * math.cos(3*t) - math.cos(4*t)) / 13
                dots.append((x, y))
        return dots

    def save(self):
        self.c.save()

def generate_booklet(pages_data, output_file):
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

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 activity_generator.py <input_json> <output_pdf>")
        sys.exit(1)
    input_json = sys.argv[1]
    output_file = sys.argv[2]
    with open(input_json, 'r') as f:
        pages_data = json.load(f)
    generate_booklet(pages_data, output_file)