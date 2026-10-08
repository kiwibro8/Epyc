import pygame
import os
import json
import glob

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Equipment Visual Editor")

font = pygame.font.SysFont(None, 24)

OFFSETS_FILE = "equipment_offsets.json"

if os.path.exists(OFFSETS_FILE):
    with open(OFFSETS_FILE, "r") as f:
        offsets = json.load(f)
else:
    offsets = {}

# Dynamically find base characters and equipment
base_chars = [f.replace("\\", "/") for f in glob.glob("assets/*Char.png")]
# Exclude backgrounds and non-equipment stuff
excluded_keywords = ["Background", "map", "flag", "MainMenu"]
items = [f.replace("\\", "/") for f in glob.glob("assets/*.png") if "Char" not in f and not any(kw in f for kw in excluded_keywords)]

if not base_chars:
    base_chars = ["assets/BaseChar.png", "assets/CombatChar.png"]
if not items:
    items = ["assets/CrusaderArmor.png", "assets/GreatHelm.png", "assets/CrusaderSword.png"]

base_idx = 0
item_idx = 0

def save_offsets():
    with open(OFFSETS_FILE, "w") as f:
        json.dump(offsets, f, indent=2)
    print(f"Saved to {OFFSETS_FILE}")

def get_current_offset(item_path, base_path):
    if item_path not in offsets:
        offsets[item_path] = {}
    if base_path not in offsets[item_path]:
        # Calculate a good default based on legacy logic
        temp_img = pygame.image.load(item_path)
        default_scale = 1.0
        if temp_img.get_height() > 150:
            default_scale = 48.0 / temp_img.get_height()
        offsets[item_path][base_path] = {"dx": 0, "dy": 0, "rot": 0, "scale": default_scale}
    # Migration for already saved offsets that lack "scale"
    if "scale" not in offsets[item_path][base_path]:
        temp_img = pygame.image.load(item_path)
        default_scale = 1.0
        if temp_img.get_height() > 150:
            default_scale = 48.0 / temp_img.get_height()
        offsets[item_path][base_path]["scale"] = default_scale
    return offsets[item_path][base_path]

running = True
dragging = False

image_cache = {}
def load_image(path):
    if path not in image_cache:
        image_cache[path] = pygame.image.load(path).convert_alpha()
    return image_cache[path]

clock = pygame.time.Clock()
offset_x, offset_y = 0, 0

while running:
    base_path = base_chars[base_idx]
    item_path = items[item_idx]
    
    current_offset = get_current_offset(item_path, base_path)
    dx = current_offset["dx"]
    dy = current_offset["dy"]
    rot = current_offset["rot"]
    scale = current_offset["scale"]

    base_img = load_image(base_path)
    if base_img.get_height() > 150:
        b_scale = 108.0 / base_img.get_height()
        base_img = pygame.transform.smoothscale(base_img, (max(1, int(base_img.get_width() * b_scale)), 108))
    
    base_x, base_y = 350, 250
    
    item_img = load_image(item_path)
    # Apply custom scaling
    if scale != 1.0:
        item_img = pygame.transform.smoothscale(item_img, (max(1, int(item_img.get_width() * scale)), max(1, int(item_img.get_height() * scale))))
        
    # Apply rotation
    rotated_item = pygame.transform.rotate(item_img, rot)
    item_rect = rotated_item.get_rect()
    item_rect.x = base_x + dx
    item_rect.y = base_y + dy

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Add a bit of padding to the click area for small items
                click_rect = item_rect.inflate(20, 20)
                if click_rect.collidepoint(event.pos):
                    dragging = True
                    mouse_x, mouse_y = event.pos
                    offset_x = item_rect.x - mouse_x
                    offset_y = item_rect.y - mouse_y
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                mouse_x, mouse_y = event.pos
                new_x = mouse_x + offset_x
                new_y = mouse_y + offset_y
                current_offset["dx"] = new_x - base_x
                current_offset["dy"] = new_y - base_y
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                base_idx = (base_idx + 1) % len(base_chars)
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                item_idx = (item_idx - 1) % len(items)
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                item_idx = (item_idx + 1) % len(items)
            elif event.key == pygame.K_q:
                current_offset["rot"] += 5
            elif event.key == pygame.K_e:
                current_offset["rot"] -= 5
            elif event.key == pygame.K_w:
                step = 0.01 if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 0.05
                current_offset["scale"] += step
            elif event.key == pygame.K_s and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                step = 0.01 if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 0.05
                current_offset["scale"] -= step
                if current_offset["scale"] < 0.005:
                    current_offset["scale"] = 0.005
            elif event.key == pygame.K_UP:
                current_offset["dy"] -= 1
            elif event.key == pygame.K_DOWN:
                current_offset["dy"] += 1
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_SHIFT:
                if event.key == pygame.K_LEFT:
                    current_offset["dx"] -= 1
                elif event.key == pygame.K_RIGHT:
                    current_offset["dx"] += 1
            elif event.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
                save_offsets()
            # Let's also support just 'S' if user forgets Ctrl, but W/S is better for scale. Actually let's use 'X' for save.
            elif event.key == pygame.K_x:
                save_offsets()

    screen.fill((40, 40, 45))
    
    # Draw Character
    screen.blit(base_img, (base_x, base_y))
    
    # Draw Item Outline for visibility
    pygame.draw.rect(screen, (255, 255, 50), item_rect, 1)
    
    # Draw Item
    screen.blit(rotated_item, (item_rect.x, item_rect.y))
    
    # Draw HUD
    hud_texts = [
        "EQUIPMENT EDITOR",
        f"Base [SPACE]: {base_path}",
        f"Item [A/D]: {item_path}",
        f"Position: dx={dx}, dy={dy} (Drag or Up/Down/Shift+Left/Right)",
        f"Rotation: {rot} deg (Q/E)",
        f"Scale: {scale:.2f}x (W/S)",
        "Press 'X' or 'Ctrl+S' to Save offsets"
    ]
    for i, text in enumerate(hud_texts):
        color = (255, 255, 255) if i > 0 else (255, 255, 0)
        label = font.render(text, True, color)
        screen.blit(label, (20, 20 + i * 30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
