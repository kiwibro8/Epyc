import pygame
import sys

# Pygame initialization
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Click the 6 points to get coordinates")

# Load and scale map just like the main game
map_image = pygame.image.load("assets/map.png").convert()
map_image = pygame.transform.scale(map_image, (WIDTH, HEIGHT))

print("Click on the screen to get the (X, Y) coordinates.")
print("Close the window when you are done.")

clock = pygame.time.Clock()
while True:
    screen.blit(map_image, (0, 0))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                x, y = event.pos
                print(f"Clicked coordinate: ({x}, {y})")
                
    pygame.display.flip()
    clock.tick(60)
