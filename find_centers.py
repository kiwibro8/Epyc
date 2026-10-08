import pygame
import sys
import math

pygame.init()
pygame.display.set_mode((800, 600), pygame.HIDDEN)
img = pygame.image.load("assets/map.png").convert()
img = pygame.transform.scale(img, (800, 600))

width, height = img.get_size()

def is_golden(color):
    r, g, b, a = color
    # Golden is roughly High R, High G, Low B
    return r > 200 and g > 150 and b < 100 and (int(r) + int(g) - int(b)) > 300

candidates = []

for x in range(20, width - 20):
    for y in range(20, height - 20):
        # We are looking for the center of the white text "1", "2" etc.
        center_color = img.get_at((x, y))
        r, g, b, a = center_color
        # Text is white/light
        if r > 220 and g > 220 and b > 220:
            # Check a circle of radius 12 around it
            golden_count = 0
            total_points = 16
            for i in range(total_points):
                angle = 2 * math.pi * i / total_points
                cx = int(x + 15 * math.cos(angle))
                cy = int(y + 15 * math.sin(angle))
                if is_golden(img.get_at((cx, cy))):
                    golden_count += 1
            if golden_count >= 10:
                candidates.append((x, y, golden_count))

# Cluster the candidates
clusters = []
for x, y, gc in candidates:
    found = False
    for c in clusters:
        cx, cy = c['sum_x']/c['n'], c['sum_y']/c['n']
        if math.hypot(x - cx, y - cy) < 20:
            c['sum_x'] += x
            c['sum_y'] += y
            c['n'] += 1
            c['max_gc'] = max(c['max_gc'], gc)
            found = True
            break
    if not found:
        clusters.append({'sum_x': x, 'sum_y': y, 'n': 1, 'max_gc': gc})

clusters.sort(key=lambda c: c['sum_x'] / c['n'])
for i, c in enumerate(clusters):
    cx = round(c['sum_x'] / c['n'])
    cy = round(c['sum_y'] / c['n'])
    print(f"Node Candidate {i+1}: ({cx}, {cy}) with max golden perimeter {c['max_gc']}/16")

pygame.quit()