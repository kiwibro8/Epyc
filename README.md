# Epyc ⚔️

A turn-based stickman RPG made with Python and Pygame. Put together a party, gear them up, and fight your way across the realm to take down the dragon.

## What's in the game?

- **Stick figures with actual gear**: When you equip swords, axes, wizard hats, or heavy armor, the sprites actually show up on your stickman characters.
- **Turn-based tactical combat**: Battles run on a speed-based turn order with attack animations, critical hits, and status effects like Bleed and Fire. Enemies naturally target your frontline heroes first, so your team lineup matters.
- **4 playable classes**: 
  - **Crusader**: Heavy frontline tank with high HP and defense.
  - **Mage**: Fragile glass cannon dealing high magic damage with animated spells.
  - **Rogue**: Speedy assassin built around high dodge and critical strikes.
  - **Archer**: Ranged physical attacker with custom arrow animations.
- **A journey across the map**: Travel through 7 hand-drawn locations on the world map — start out in Sunnydale and work your way through the Whispering Woods, a spooky Graveyard, a Bridge Troll encounter, the freezing Whitewalker Mountain, and finally the Dragon's Lair.
- **Inventory & visual equipment tool**: Swap gear around and inspect stats via hover tooltips. Includes a standalone `equipment_editor.py` tool used to visually line up and scale weapons and armor onto character sprites in real-time.

---

## 🚧 Upcoming / Roadmap

- **Cleric Class (Work in Progress)**: The class skeleton already exists in `stickman_classes.py`. Still needs its custom holy gear (mace, chainmail, halo), dedicated sprite assets, and balanced support stats.
- **Healing & Support Abilities**: Expanding the combat system so party members can heal allies, cast defensive buffs, or cleanse Bleed and Fire status effects during battle.
- **More Loot & Encounters**: Additional weapons, armor sets, and enemy varieties.

---

## How to Play

### 1. Requirements
- Python 3.8 or newer
- Pygame

Install Pygame using the requirements file:
```bash
pip install -r requirements.txt
```

### 2. Launching the Game
Start the game with:
```bash
python main.py
```

### 3. Controls
- **Mouse**: Everything is point-and-click. Use the mouse to pick your destination on the map, choose targets in battle, and manage equipment in the inventory.
- **Hover**: Move your cursor over items and party members to view their stats, bonuses, and class restrictions.

---

## Modding & Dev Tools

If you want to add new items or tweak how weapons and armors sit on the characters, launch the visual editor:
```bash
python equipment_editor.py
```
This lets you preview items on any base sprite, tweak the position (`dx`, `dy`), scale, and rotation, and save the coordinates directly to `equipment_offsets.json`.

---

## File Breakdown

- `main.py` — The core game loop, world map navigation, inventory system, and combat engine.
- `stickman_classes.py` — Hero classes, enemy stats, item models, and equipment logic.
- `equipment_editor.py` — Visual tool for adjusting gear placement and scale.
- `equipment_offsets.json` — Saved coordinates and scale factors for worn equipment.
- `items.json` — Item stats, bonuses, and class restrictions.
- `assets/` — All sprites, animations, and backgrounds.
