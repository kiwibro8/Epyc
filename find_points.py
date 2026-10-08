import pygame
import sys
import math

pygame.init()
pygame.display.set_mode((800, 600), pygame.HIDDEN)
img = pygame.image.load("assets/map.png").convert()
img = pygame.transform.scale(img, (800, 600))

width, height = img.get_size()
golden_pixels = []
for x in range(width):
    for y in range(height):
        r, g, b, a = img.get_at((x, y))
        if r > 180 and g > 150 and b < 80 and (int(r)+int(g)-int(b)) > 300:
            golden_pixels.append((x, y))

# cluster them by distance
clusters = []
for x, y in golden_pixels:
    found = False
    for c in clusters:
        for cx, cy in c:
            if math.hypot(x - cx, y - cy) < 20:
                c.append((x, y))
                found = True
                break
        if found:
            break
    if not found:
        clusters.append([(x, y)])

print(f"Found {len(clusters)} clusters.")
centroids = []
for i, c in enumerate(clusters):
    if len(c) < 5:
        continue # ignore noise
    sum_x = sum([p[0] for p in c])
    sum_y = sum([p[1] for p in c])
    cx = int(sum_x / len(c))
    cy = int(sum_y / len(c))
    centroids.append((cx, cy))
    print(f"Cluster {i} with {len(c)} pixels: center at ({cx}, {cy})")

pygame.quit()