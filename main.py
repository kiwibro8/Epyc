import pygame
import sys
import os
import json
import random
from stickman_classes import Party, Crusader, Mage, Rogue, Cleric, Archer, Unit, Headgear, Armor, Weapon


pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Epyc")

font_large = pygame.font.SysFont(None, 64)
font_medium = pygame.font.SysFont(None, 36)
font_small = pygame.font.SysFont(None, 24)
font_location = pygame.font.SysFont('georgia,garamond,timesnewroman,palatino', 22, bold=True, italic=True)

class Game:
    def __init__(self):
        """
        Inițializează starea jocului, fereastra Pygame, grupul jucătorului (party)
        și configurează nodurile hărții.
        """
        self.state = "MAIN_MENU"

        # Încarcă dicționarul de coordonate (offsets) dintr-un fișier JSON extern.
        # Aceste coordonate sunt folosite pentru a poziționa corect săbiile,
        # armurile și coifurile pe modelul (sprite-ul) personajului din joc.
        self.equipment_offsets = {}
        if os.path.exists("equipment_offsets.json"):
            try:
                with open("equipment_offsets.json", "r") as f:
                    self.equipment_offsets = json.load(f)
            except Exception as e:
                print(f"Failed to load offsets: {e}")


        self.roster = [Mage(), Rogue(), Crusader(), Cleric(), Archer()]


        self.party = Party()
        self.party.add_member(self.roster[0], 0)
        self.party.add_member(self.roster[1], 1)
        self.party.add_member(self.roster[2], 2)

        # Variabile folosite pentru a gestiona interfața inventarului:
        # - inventory_selected_character: reține indexul personajului selectat curent
        # - inventory_hovered_item / char: stochează obiectul/personajul pe care e pus mouse-ul (pentru tooltip)
        self.inventory_selected_character = 0
        self.inventory_hovered_item = None
        self.inventory_hovered_char = None
        
        # Adăugăm un obiect de start puternic (topor) direct în rucsacul echipei pentru teste
        self.party.inventory.append(Weapon("Halbeard Axe", attack_bonus=12, sprite_path="assets/HalbeardAxe.png", defense_bonus=0, speed_bonus=-5, crit_bonus=10, magic_bonus=0, hp_bonus=5))


        # Variabile pentru logica de luptă pe ture:
        # - turn_queue: ordinea de atac (inițiativa) calculată pentru toți participanții
        # - current_turn_index: reține care participant este la rând în acest moment
        # - enemies: lista cu inamicii generați pentru bătălia activă
        self.turn_queue = []
        self.current_turn_index = 0
        self.enemies = []

        # Variabile folosite pentru randarea animațiilor grafice de atac:
        self.animating_unit = None
        self.animation_target = None
        self.animation_effect_path = None
        self.animation_frames_left = 0
        
        # Cache pentru optimizare: păstrează imaginile în memorie ca să nu fie citite iar de pe disc
        self.image_cache = {}


        # --- ÎNCĂRCARE MENIU PRINCIPAL ---
        # Încearcă să citească imaginea de fundal pentru meniul de început.
        # .convert() se folosește pentru a optimiza randarea în Pygame.
        main_menu_path = "assets/MainMenu.png"
        if os.path.exists(main_menu_path):
            self.main_menu_image = pygame.image.load(main_menu_path).convert()
            self.main_menu_image = pygame.transform.scale(self.main_menu_image, (WIDTH, HEIGHT))
        else:
            self.main_menu_image = None

        # --- ÎNCĂRCARE HARTĂ OVERWORLD ---
        # La fel ca la meniu, caută imaginea hărții (map.png) și o scalează fin.
        # Dacă imaginea lipsește, creează un fundal verde drept "fallback" pentru a preveni crash-urile.
        map_path = "assets/map.png"
        if os.path.exists(map_path):
            self.map_image = pygame.image.load(map_path).convert()
            self.map_image = pygame.transform.smoothscale(self.map_image, (WIDTH, HEIGHT))
        else:
            self.map_image = pygame.Surface((WIDTH, HEIGHT))
            self.map_image.fill((30, 80, 30))


        # --- ÎNCĂRCARE STEAG (FLAG) ---
        # Încarcă iconița de steag care marchează locațiile jucătorului pe hartă.
        # .convert_alpha() este vital aici deoarece steagul are margini transparente.
        flag_path = "assets/flag.png"
        if os.path.exists(flag_path):
            self.flag_image = pygame.image.load(flag_path).convert_alpha()
        else:
            self.flag_image = None

        # --- DEFINIREA NODURILOR DE PE HARTĂ ---
        # Fiecare dicționar reprezintă un nivel de joc (locație), având un Nume 
        # și coordonatele (X, Y) unde va fi desenat pe harta overworld.
        self.map_nodes = [
            {"id": 1, "name": "Sunnydale Harbor", "pos": (120, 414)},
            {"id": 2, "name": "Graveyard", "pos": (289, 380)},
            {"id": 3, "name": "Whispering Woods", "pos": (338, 197)},
            {"id": 4, "name": "Troll Bridge", "pos": (442, 331)},
            {"id": 5, "name": "Whitewalker Mountain", "pos": (562, 233)},
            {"id": 6, "name": "Dragon's Peak", "pos": (722, 359)}
        ]
        
        # Variabile pentru progresul pe hartă:
        # current_node_index: Pe ce nod se află fizic personajul acum (0 înseamnă Sunnydale)
        # unlocked_node_index: Până la ce nod ai voie să te duci (limitează jucătorul)
        # completed_nodes: Un set cu indexurile nivelurilor pe care le-ai terminat cu succes
        self.current_node_index = 0
        self.unlocked_node_index = 0
        self.completed_nodes = set()

    def get_image(self, path):
        """
        Încarcă și returnează o imagine de la calea specificată, cu suport pentru transparență.
        Returnează None dacă fișierul nu este găsit.
        """
        if not path or not os.path.exists(path):
            return None
        if path not in self.image_cache:
            self.image_cache[path] = pygame.image.load(path).convert_alpha()
        return self.image_cache[path]

    def run(self):
        """
        Bucla principală a jocului. Rulează continuu pentru a gestiona logica,
        evenimentele și desenarea cadrelor pe ecran.
        """
        # clock ne ajută să controlăm viteza jocului (câte cadre pe secundă - FPS - va rula)
        clock = pygame.time.Clock()
        
        # Aceasta este Bucla Principală a Jocului (Game Loop) care rulează la infinit
        while True:
            # Curăță ecranul cu o culoare gri închis înainte de a desena noul cadru
            screen.fill((20, 20, 25))

            # --- PROCESAREA EVENIMENTELOR ---
            for event in pygame.event.get():
                # Verifică dacă utilizatorul a închis fereastra jocului (de la butonul X)
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                # Orice altă apăsare pe taste sau mouse este trimisă mai departe
                self.handle_input(event)

            # --- GESTIONAREA ANIMAȚIILOR DE LUPTĂ ---
            # Dacă suntem în luptă și o animație rulează, scade numărul de cadre rămase.
            # Cât timp timer-ul scade, jocul "îngheață" tura pentru a lăsa efectul să se vadă.
            if self.state == "COMBAT" and getattr(self, 'animation_frames_left', 0) > 0:
                self.animation_frames_left -= 1
                
                # Când timer-ul de animație se termină, șterge efectul și trece la următorul combatant
                if self.animation_frames_left <= 0:
                    self.animating_unit = None
                    self.animation_target = None
                    self.animation_effect_path = None
                    self.advance_turn()
            
            # Dacă suntem în luptă și NU e nicio animație activă, verifică dacă e rândul inamicului (AI)
            elif self.state == "COMBAT" and getattr(self, 'animation_frames_left', 0) == 0:

                # Verificăm dacă există participanți la luptă în listă
                if self.turn_queue and self.current_turn_index < len(self.turn_queue):
                    current_unit = self.turn_queue[self.current_turn_index]
                    
                    # Dacă inamicul a murit între timp (de exemplu, de la sângerare), sari peste tura lui
                    if current_unit and current_unit.current_hp <= 0:
                        self.advance_turn()
                        
                    # === INTELIGENȚA ARTIFICIALĂ (AI) A INAMICILOR ===
                    # Când este rândul unui inamic să atace:
                    elif current_unit and getattr(current_unit, 'is_enemy', False):
                        import random
                        
                        # Logica de "Aggro": Inamicii preferă să atace personajele din față.
                        # Șanse de a fi lovit: Poziția 0 (10%), Poziția 1 (30%), Poziția 2 - Tancul (60%)
                        weights = [10, 30, 60]
                        valid_targets = []
                        valid_weights = []
                        for i, p in enumerate(self.party.members):
                            if p is not None and p.current_hp > 0:
                                valid_targets.append(p)
                                valid_weights.append(weights[i])

                        if valid_targets:
                            # Selectează ținta pe baza greutăților (șanselor) calculate mai sus
                            target = random.choices(valid_targets, weights=valid_weights, k=1)[0]
                            damage = current_unit.attack_power
                            
                            # Calculează dacă lovitura este Critică (șansă % pentru daune duble)
                            if random.randint(1, 100) <= current_unit.crit_chance:
                                damage *= 2
                            target.take_damage(damage)

                            # --- ABILITĂȚI SPECIALE ALE INAMICILOR ---
                            # Hoții (Thief) au o șansă de 30% să provoace efectul "Bleed" (Sângerare)
                            if current_unit.name.startswith("Thief"):
                                if random.random() < 0.3:
                                    target.apply_status("Bleed", 2)
                            # Mini-boss-ul "Bridge Troll" lovește masiv și are 35% șanse de Sângerare
                            elif current_unit.name == "Bridge Troll":
                                if random.random() < 0.35:
                                    target.apply_status("Bleed", 2)

                            # Pregătește ecranul pentru animația atacului (blochează lupta 30 de cadre)
                            self.animating_unit = current_unit
                            self.animation_target = target
                            self.animation_frames_left = 30
                            self.animation_effect_path = self.get_random_attack_effect(current_unit)
                        else:
                            # Dacă nu găsește jucători în viață, trece tura
                            self.advance_turn()

            self.draw(screen)
            pygame.display.flip()
            clock.tick(60)

    def handle_input(self, event):
        """
        Procesează inputul de la tastatură și mouse în funcție de starea
        curentă a jocului (Meniu Principal, Hartă, Luptă, Inventar etc.).
        """
        # Ignoră evenimentele care nu sunt apăsări de taste sau acțiuni de mouse
        if event.type not in (pygame.KEYDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            return

        # Gestionarea stării Meniului Principal
        if self.state == "MAIN_MENU":
            # Apasă Space pentru a trece la Hartă
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.state = "MAP"

        # Gestionarea stării Hărții
        elif self.state == "MAP":
            if event.type == pygame.KEYDOWN:
                # Navigare noduri hartă spre dreapta
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    if self.current_node_index < len(self.map_nodes) - 1:
                        self.current_node_index += 1
                # Navigare noduri hartă spre stânga
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    if self.current_node_index > 0:
                        self.current_node_index -= 1

                # Intră în nod (începe lupta sau verifică starea de blocare/completare)
                elif event.key == pygame.K_RETURN:
                    if self.current_node_index in getattr(self, 'completed_nodes', set()):
                        print("Node already completed!")
                    elif self.current_node_index > getattr(self, 'unlocked_node_index', 0):
                        print("Node locked!")
                    else:
                        self.start_combat()

                # Deschide Inventarul
                elif event.key == pygame.K_i or event.key == pygame.K_TAB:
                    self.state = "INVENTORY"
                    self.inventory_hovered_item = None
                    self.inventory_hovered_char = None
                    self.inventory_selected_character = 0

                # Deschide ecranul de Selecție Echipă (Party)
                elif event.key == pygame.K_p:
                    self.state = "PARTY_SELECT"
                    self.party_select_selected_slot = None

        # Gestionarea stării Inventarului
        elif self.state == "INVENTORY":
            if event.type == pygame.KEYDOWN:
                # Închide inventarul și revino la hartă
                if event.key in (pygame.K_i, pygame.K_TAB, pygame.K_ESCAPE):
                    self.state = "MAP"
            elif event.type == pygame.MOUSEMOTION:
                # Gestionează trecerea mouse-ului peste obiecte sau caractere
                self.handle_inventory_mouse_motion(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Gestionează click-ul pe obiecte sau caractere (click stânga)
                    self.handle_inventory_click(event.pos)

        # Gestionarea stării de Selecție Echipă
        elif self.state == "PARTY_SELECT":
            if event.type == pygame.KEYDOWN:
                # Închide selecția echipei și revino la hartă
                if event.key in (pygame.K_p, pygame.K_ESCAPE):
                    self.state = "MAP"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Gestionează selecția slotului (click stânga)
                    self.handle_party_select_click(event.pos)

        # Gestionarea stării de Luptă (Combat)
        elif self.state == "COMBAT":
            # Blochează inputul în timpul animațiilor
            if getattr(self, 'animation_frames_left', 0) > 0:
                return

            if event.type == pygame.KEYDOWN:
                # Treci tura sau declanșează animația de atac
                if event.key == pygame.K_SPACE:
                    if self.turn_queue:
                        self.animating_unit = self.turn_queue[self.current_turn_index]
                        self.animation_frames_left = 30
                        self.animation_effect_path = self.get_random_attack_effect(self.animating_unit)
                    else:
                        self.advance_turn()
                # Fugi din luptă și revino la hartă
                elif event.key == pygame.K_ESCAPE:
                    self.state = "MAP"

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Gestionează atacul jucătorului asupra unui inamic prin click
                if self.turn_queue and self.current_turn_index < len(self.turn_queue):
                    current_unit = self.turn_queue[self.current_turn_index]
                    # Asigură-te că este rândul unui caracter al jucătorului și că e în viață
                    if current_unit and current_unit.current_hp > 0 and not getattr(current_unit, 'is_enemy', False):
                        mouse_pos = event.pos

                        ex = 550
                        # Verifică coliziunea cu toți inamicii pentru a găsi ținta pe care s-a dat click
                        for enemy in self.enemies:
                            if enemy is not None and enemy.current_hp > 0:
                                current_node_name = self.map_nodes[self.current_node_index]["name"]
                                sprite_base_y = 400
                                # Ajustează poziția Y a sprite-ului în funcție de nodul curent al hărții
                                if current_node_name == "Sunnydale Harbor":
                                    sprite_base_y = 450
                                elif current_node_name == "Troll Bridge":
                                    sprite_base_y = 465
                                elif current_node_name == "Dragon's Peak":
                                    sprite_base_y = 450

                                enemy_rect = pygame.Rect(ex - 20, sprite_base_y - 80, 150, 200)

                                # Dacă s-a dat click pe inamic, aplică daune
                                if enemy_rect.collidepoint(mouse_pos):
                                    # Calculează daunele și verifică pentru lovitură critică
                                    damage = max(current_unit.attack_power, getattr(current_unit, 'magic_power', 0))
                                    if random.randint(1, 100) <= current_unit.crit_chance:
                                        damage *= 2
                                    enemy.take_damage(damage)

                                    # Aplică efecte de status specifice clasei
                                    if type(current_unit).__name__ == "Rogue":
                                        if random.random() < 0.3:
                                            enemy.apply_status("Bleed", 3)
                                    elif type(current_unit).__name__ == "Mage":
                                        enemy.apply_status("Fire", 2)

                                    # Începe animația de atac vizând inamicul selectat
                                    self.animating_unit = current_unit
                                    self.animation_target = enemy
                                    self.animation_frames_left = 30
                                    self.animation_effect_path = self.get_random_attack_effect(current_unit)
                                    break
                            ex += 100

        # Gestionarea stării de Victorie
        elif self.state == "VICTORY":
            # Apasă orice tastă sau click pentru a continua
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                # Marchează nodul curent al hărții ca finalizat
                if not hasattr(self, 'completed_nodes'):
                    self.completed_nodes = set()
                self.completed_nodes.add(self.current_node_index)

                # Deblochează următorul nod de pe hartă dacă nu este deja deblocat
                if not hasattr(self, 'unlocked_node_index'):
                    self.unlocked_node_index = 0
                if self.current_node_index == self.unlocked_node_index:
                    self.unlocked_node_index = min(self.unlocked_node_index + 1, len(self.map_nodes) - 1)

                # Mută-te la nodul nou deblocat și revino la hartă
                self.current_node_index = self.unlocked_node_index
                self.state = "MAP"

    def handle_inventory_mouse_motion(self, pos):
        # Resetează elementele pe care se află mouse-ul
        self.inventory_hovered_item = None
        self.inventory_hovered_char = None

        # Verifică dacă mouse-ul este deasupra unui caracter din inventar
        if hasattr(self, 'inventory_char_rects'):
            for i, rect in enumerate(self.inventory_char_rects):
                if rect.collidepoint(pos):
                    self.inventory_hovered_char = i

        # Verifică dacă mouse-ul este deasupra unui obiect din inventar
        if hasattr(self, 'inventory_item_rects'):
            for i, rect in enumerate(self.inventory_item_rects):
                if rect.collidepoint(pos):
                    if i < len(self.party.inventory):
                        self.inventory_hovered_item = i

    def handle_inventory_click(self, pos):
        # Dacă s-a dat click pe un caracter, selectează-l
        if self.inventory_hovered_char is not None:
            self.inventory_selected_character = self.inventory_hovered_char

        # Dacă s-a dat click pe un obiect, încearcă să-l echipezi
        elif self.inventory_hovered_item is not None:
            unit = self.party.members[self.inventory_selected_character]
            item = self.party.inventory[self.inventory_hovered_item]

            # Verifică dacă clasa caracterului permite echiparea acestui obiect
            if getattr(item, "allowed_classes", None):
                if type(unit).__name__ not in item.allowed_classes:
                    return

            # Elimină obiectul din inventar
            self.party.inventory.pop(self.inventory_hovered_item)

            # Echipează obiectul în funcție de tipul său și pune obiectul vechi înapoi în inventar
            if isinstance(item, Weapon):
                if unit.weapon: self.party.inventory.append(unit.weapon)
                unit.equip_weapon(item)
            elif isinstance(item, Armor):
                if unit.armor: self.party.inventory.append(unit.armor)
                unit.equip_armor(item)
            elif isinstance(item, Headgear):
                if unit.headgear: self.party.inventory.append(unit.headgear)
                unit.equip_headgear(item)

            # Resetează obiectul selectat după echipare
            self.inventory_hovered_item = None

    def handle_party_select_click(self, pos):
        # Verifică dacă s-a dat click pe un slot din echipă (party)
        if hasattr(self, 'party_slot_rects'):
            for i, rect in enumerate(self.party_slot_rects):
                if rect.collidepoint(pos):
                    # Dacă slotul este deja selectat, deselectează-l
                    if getattr(self, 'party_select_selected_slot', None) == i:
                        self.party_select_selected_slot = None
                    # Altfel, selectează noul slot
                    else:
                        self.party_select_selected_slot = i
                    return

        # Verifică dacă s-a dat click pe un caracter din lista completă (roster)
        if hasattr(self, 'roster_rects'):
            for i, rect in enumerate(self.roster_rects):
                if rect.collidepoint(pos):
                    # Dacă un slot din echipă este deja selectat, efectuează schimbarea
                    if getattr(self, 'party_select_selected_slot', None) is not None:
                        unit = self.roster[i]
                        current_slot = -1
                        # Găsește dacă caracterul este deja în echipă
                        for idx, member in enumerate(self.party.members):
                            if member == unit:
                                current_slot = idx
                                break

                        target_slot = self.party_select_selected_slot
                        # Dacă caracterul este deja în echipă, schimbă-i poziția
                        if current_slot != -1:
                            temp = self.party.members[target_slot]
                            self.party.members[target_slot] = self.party.members[current_slot]
                            self.party.members[current_slot] = temp
                        # Dacă nu este în echipă, adaugă-l în slotul selectat
                        else:
                            self.party.members[target_slot] = unit

                        # Deselectează slotul după schimbare
                        self.party_select_selected_slot = None
                    return

    def draw_inventory(self, surface):
        """
        Desenează ecranul de inventar. Afișează echipamentul personajelor
        din party, statusurile lor și obiectele din rucsac.
        """
        # Desenarea unui fundal semi-transparent peste hartă pentru inventar
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 15, 230))
        surface.blit(overlay, (0, 0))

        # Titlul ecranului de inventar
        title = font_large.render("INVENTORY", True, (255, 215, 0))
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))

        self.inventory_char_rects = []
        char_start_y = 100
        font_tiny = pygame.font.SysFont(None, 18)
        font_stats = pygame.font.SysFont(None, 20)

        # Parcurge membrii echipei pentru a le desena informațiile
        for i, member in enumerate(self.party.members):
            if not member: continue

            # Crearea chenarului pentru fiecare membru al echipei
            rect = pygame.Rect(30, char_start_y + i * 150, 260, 130)
            self.inventory_char_rects.append(rect)

            # Modificarea culorii fundalului în funcție de interacțiunea cu mouse-ul (hover) sau dacă este selectat
            bg_color = (60, 60, 80) if i == self.inventory_selected_character else (40, 40, 50)
            if self.inventory_hovered_char == i:
                bg_color = (80, 80, 100)
            pygame.draw.rect(surface, bg_color, rect, border_radius=10)
            
            # Adăugarea unui contur auriu pentru personajul curent selectat
            if i == self.inventory_selected_character:
                pygame.draw.rect(surface, (255, 215, 0), rect, 3, border_radius=10)

            # Afișarea numelui și statisticilor (HP, Atac, Apărare)
            name_lbl = font_medium.render(member.name, True, (255, 255, 255))
            surface.blit(name_lbl, (rect.x + 10, rect.y + 10))
            stats = f"HP:{member.current_hp}/{member.max_hp} ATK:{member.attack_power} DEF:{member.defense_power}"
            stats_lbl = font_stats.render(stats, True, (200, 200, 200))
            surface.blit(stats_lbl, (rect.x + 10, rect.y + 40))

            # Pregătirea textului pentru echipamentul curent
            wpn = member.weapon.name if member.weapon else "None"
            arm = member.armor.name if member.armor else "None"
            hdg = member.headgear.name if member.headgear else "None"

            # Afișarea echipamentului (Armă, Armură, Cască) cu culori distincte
            g1 = font_tiny.render(f"W: {wpn}", True, (150, 200, 150))
            g2 = font_tiny.render(f"A: {arm}", True, (150, 150, 200))
            g3 = font_tiny.render(f"H: {hdg}", True, (200, 150, 150))
            surface.blit(g1, (rect.x + 10, rect.y + 65))
            surface.blit(g2, (rect.x + 10, rect.y + 85))
            surface.blit(g3, (rect.x + 10, rect.y + 105))

            # Desenarea imaginii personajului (miniatură) în inventar
            char_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
            base_img = self.get_image(member.sprite_path)

            if base_img:
                # Centrarea personajului în miniatura alocată
                px = 100 - base_img.get_width() // 2
                py = 150 - base_img.get_height()
                char_surf.blit(base_img, (px, py))

                from stickman_classes import Headgear, Armor, Weapon
                
                # Suprapunerea echipamentului pe miniatura personajului
                for item in [member.armor, member.weapon, member.headgear]:
                    if item and getattr(item, "sprite_path", None):
                        item_img = self.get_image(item.sprite_path)
                        if item_img:
                            base_x = px
                            base_y = py

                            # Căutarea datelor de offset pentru alinierea corectă a echipamentului
                            offset_data = None
                            if hasattr(self, 'equipment_offsets'):
                                if item.sprite_path in self.equipment_offsets:
                                    if member.sprite_path in self.equipment_offsets[item.sprite_path]:
                                        offset_data = self.equipment_offsets[item.sprite_path][member.sprite_path]

                            # Aplicarea offset-ului, scalării și rotației personalizate dacă există
                            if offset_data:
                                scale_factor = offset_data.get("scale", None)
                                if scale_factor is not None and scale_factor != 1.0:
                                    item_img = pygame.transform.smoothscale(item_img, (max(1, int(item_img.get_width() * scale_factor)), max(1, int(item_img.get_height() * scale_factor))))
                                elif scale_factor is None and item_img.get_height() > 150:
                                    scale = 48.0 / item_img.get_height()
                                    item_img = pygame.transform.smoothscale(item_img, (int(item_img.get_width() * scale), 48))

                                item_img = pygame.transform.rotate(item_img, offset_data.get("rot", 0))
                                ix = base_x + offset_data.get("dx", 0)
                                iy = base_y + offset_data.get("dy", 0)
                            # Aliniere standard (fallback) dacă nu există offset definit pentru combinația respectivă
                            else:
                                if item_img.get_height() > 150:
                                    scale = 48.0 / item_img.get_height()
                                    item_img = pygame.transform.smoothscale(item_img, (int(item_img.get_width() * scale), 48))

                                if isinstance(item, Headgear):
                                    ix = base_x + (base_img.get_width() - item_img.get_width()) // 2
                                    iy = base_y - 12
                                elif isinstance(item, Armor):
                                    ix = base_x + (base_img.get_width() - item_img.get_width()) // 2 - 3
                                    iy = base_y + 28
                                else:
                                    ix = base_x + base_img.get_width() - 20
                                    iy = base_y + 40

                            char_surf.blit(item_img, (ix, iy))

                # Scalarea finală a portretului la 100x100 și afișarea în dreptunghiul personajului
                char_surf = pygame.transform.smoothscale(char_surf, (100, 100))
                surface.blit(char_surf, (rect.x + 160, rect.y + 15))

        # Desenează rucsacul (stash-ul) cu obiecte
        stash_rect = pygame.Rect(320, 100, 450, 450)
        pygame.draw.rect(surface, (30, 30, 40), stash_rect, border_radius=10)

        stash_lbl = font_medium.render("Stash", True, (255, 255, 255))
        surface.blit(stash_lbl, (stash_rect.x + 20, stash_rect.y + 10))

        self.inventory_item_rects = []
        cols = 4
        slot_size = 80
        padding = 15

        start_x = stash_rect.x + 30
        start_y = stash_rect.y + 50

        # Desenează sloturile de obiecte (16 în total)
        for i in range(16):
            row = i // cols
            col = i % cols
            x = start_x + col * (slot_size + padding)
            y = start_y + row * (slot_size + padding)
            rect = pygame.Rect(x, y, slot_size, slot_size)
            self.inventory_item_rects.append(rect)

            bg_color = (50, 50, 60)
            if self.inventory_hovered_item == i:
                bg_color = (100, 100, 120)
            pygame.draw.rect(surface, bg_color, rect, border_radius=5)
            pygame.draw.rect(surface, (100, 100, 100), rect, 1, border_radius=5)

            if i < len(self.party.inventory):
                item = self.party.inventory[i]
                img = self.get_image(item.sprite_path)
                if img:
                    img = pygame.transform.smoothscale(img, (60, 60))
                    surface.blit(img, (x + 10, y + 10))

        # Afișează un tooltip cu informații dacă mouse-ul este deasupra unui obiect
        if self.inventory_hovered_item is not None and self.inventory_hovered_item < len(self.party.inventory):
            item = self.party.inventory[self.inventory_hovered_item]
            mx, my = pygame.mouse.get_pos()

            tt_w, tt_h = 200, 140
            tt_x, tt_y = mx + 15, my + 15
            if tt_x + tt_w > WIDTH: tt_x = mx - tt_w - 15
            if tt_y + tt_h > HEIGHT: tt_y = HEIGHT - tt_h - 15

            tt_rect = pygame.Rect(tt_x, tt_y, tt_w, tt_h)
            pygame.draw.rect(surface, (20, 20, 20), tt_rect, border_radius=5)
            pygame.draw.rect(surface, (255, 215, 0), tt_rect, 1, border_radius=5)

            lines = [
                item.name,
                f"Type: {item.__class__.__name__}",
                f"ATK: {item.attack_bonus} | DEF: {item.defense_bonus}",
                f"MAG: {item.magic_bonus} | SPD: {item.speed_bonus}",
                f"HP: {item.hp_bonus} | CRIT: {item.crit_bonus}%"
            ]

            for idx, line in enumerate(lines):
                color = (255, 215, 0) if idx == 0 else (200, 200, 200)
                fnt = font_medium if idx == 0 else font_small
                lbl = fnt.render(line, True, color)
                surface.blit(lbl, (tt_x + 10, tt_y + 10 + idx * 25))

    def draw_party_select(self, surface):
        """
        Afișează meniul de selecție a membrilor echipei, permițând jucătorului
        să schimbe ordinea sau componența grupului (party-ului) înainte de a explora.
        """
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 15, 230))
        surface.blit(overlay, (0, 0))

        title = font_large.render("PARTY SELECT", True, (255, 215, 0))
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))

        instruction = font_small.render("Click a slot, then click a roster member to assign. P/ESC to return.", True, (200, 200, 200))
        surface.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, 80))

        self.party_slot_rects = []
        slot_w, slot_h = 200, 150
        start_x = WIDTH // 2 - (3 * slot_w + 40) // 2
        start_y = 120

        # Desenează cele 3 sloturi ale echipei active
        for i in range(3):
            rect = pygame.Rect(start_x + i * (slot_w + 20), start_y, slot_w, slot_h)
            self.party_slot_rects.append(rect)

            bg_color = (60, 60, 80) if getattr(self, 'party_select_selected_slot', None) == i else (40, 40, 50)
            pygame.draw.rect(surface, bg_color, rect, border_radius=10)

            slot_title = font_small.render(f"Slot {i+1} ({['Back', 'Middle', 'Front'][i]})", True, (150, 150, 150))
            surface.blit(slot_title, (rect.x + 10, rect.y + 10))

            member = self.party.members[i]
            if member:
                name_lbl = font_medium.render(member.name, True, (255, 255, 255))
                surface.blit(name_lbl, (rect.x + 10, rect.y + 40))

                hp_color = (255, 50, 50) if member.current_hp <= 0 else (200, 200, 200)
                hp_lbl = font_small.render(f"HP: {member.current_hp}/{member.max_hp}", True, hp_color)
                surface.blit(hp_lbl, (rect.x + 10, rect.y + 70))

                char_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
                base_img = self.get_image(member.sprite_path)

                if base_img:
                    px = 100 - base_img.get_width() // 2
                    py = 150 - base_img.get_height()
                    char_surf.blit(base_img, (px, py))

                    from stickman_classes import Headgear, Armor, Weapon
                    for item in [member.armor, member.weapon, member.headgear]:
                        if item and getattr(item, "sprite_path", None):
                            item_img = self.get_image(item.sprite_path)
                            if item_img:
                                base_x = px
                                base_y = py

                                offset_data = None
                                if hasattr(self, 'equipment_offsets'):
                                    if item.sprite_path in self.equipment_offsets:
                                        if member.sprite_path in self.equipment_offsets[item.sprite_path]:
                                            offset_data = self.equipment_offsets[item.sprite_path][member.sprite_path]

                                if offset_data:
                                    scale_factor = offset_data.get("scale", None)
                                    if scale_factor is not None and scale_factor != 1.0:
                                        item_img = pygame.transform.smoothscale(item_img, (max(1, int(item_img.get_width() * scale_factor)), max(1, int(item_img.get_height() * scale_factor))))
                                    elif scale_factor is None and item_img.get_height() > 150:
                                        scale = 48.0 / item_img.get_height()
                                        item_img = pygame.transform.smoothscale(item_img, (int(item_img.get_width() * scale), 48))

                                    item_img = pygame.transform.rotate(item_img, offset_data.get("rot", 0))
                                    ix = base_x + offset_data.get("dx", 0)
                                    iy = base_y + offset_data.get("dy", 0)
                                else:
                                    if item_img.get_height() > 150:
                                        scale = 48.0 / item_img.get_height()
                                        item_img = pygame.transform.smoothscale(item_img, (int(item_img.get_width() * scale), 48))

                                    if isinstance(item, Headgear):
                                        ix = base_x + (base_img.get_width() - item_img.get_width()) // 2
                                        iy = base_y - 12
                                    elif isinstance(item, Armor):
                                        ix = base_x + (base_img.get_width() - item_img.get_width()) // 2 - 3
                                        iy = base_y + 28
                                    else:
                                        ix = base_x + base_img.get_width() - 20
                                        iy = base_y + 40

                                char_surf.blit(item_img, (ix, iy))

                    char_surf = pygame.transform.smoothscale(char_surf, (80, 80))
                    surface.blit(char_surf, (rect.right - 90, rect.bottom - 90))
            else:
                empty_lbl = font_medium.render("EMPTY", True, (100, 100, 100))
                surface.blit(empty_lbl, (rect.x + 10, rect.y + 50))


        roster_title = font_medium.render("Roster", True, (255, 255, 255))
        surface.blit(roster_title, (50, 300))

        self.roster_rects = []
        roster_w, roster_h = 180, 80
        cols = 4

        # Desenează caracterele disponibile în lista completă (roster)
        for i, unit in enumerate(self.roster):
            row = i // cols
            col = i % cols
            rect = pygame.Rect(50 + col * (roster_w + 20), 340 + row * (roster_h + 20), roster_w, roster_h)
            self.roster_rects.append(rect)

            in_party = unit in self.party.members
            bg_color = (50, 70, 50) if in_party else (40, 40, 40)
            pygame.draw.rect(surface, bg_color, rect, border_radius=5)

            name_lbl = font_small.render(unit.name, True, (255, 255, 255))
            surface.blit(name_lbl, (rect.x + 10, rect.y + 10))

            hp_color = (255, 50, 50) if unit.current_hp <= 0 else (200, 200, 200)
            hp_lbl = font_small.render(f"HP: {unit.current_hp}/{unit.max_hp}", True, hp_color)
            surface.blit(hp_lbl, (rect.x + 10, rect.y + 35))

            if in_party:
                slot_idx = self.party.members.index(unit)
                in_lbl = font_small.render(f"In Slot {slot_idx+1}", True, (100, 255, 100))
                surface.blit(in_lbl, (rect.x + 10, rect.y + 55))

    def start_round(self):
        """
        Inițiază o nouă rundă de luptă. Se determină ordinea de atac (inițiativa)
        pe baza vitezei unităților plus un factor aleatoriu.
        """
        import random


        # Calculează inițiativa pentru toți combatanții în viață
        for unit in self.party.members + self.enemies:
            if unit is not None and unit.current_hp > 0:

                unit.current_initiative = unit.speed + random.randint(1, 8)


        # Sortează coada de rânduri în funcție de inițiativă (descrescător)
        active_combatants = [u for u in self.party.members + self.enemies if u is not None and u.current_hp > 0]
        self.turn_queue = sorted(active_combatants, key=lambda u: u.current_initiative, reverse=True)
        self.current_turn_index = 0

        if self.turn_queue:
            for u in self.turn_queue:
                if u and u.current_hp > 0:
                    u.process_statuses()


            if not any(e for e in getattr(self, 'enemies', []) if e is not None and e.current_hp > 0):
                self.advance_turn()
            elif not any(p for p in getattr(self.party, 'members', []) if p is not None and p.current_hp > 0):
                self.advance_turn()

    def start_combat(self):
        """
        Generează inamicii în funcție de locația curentă de pe hartă
        și trece jocul în starea de luptă.
        """
        self.state = "COMBAT"


        # Identifică locația curentă pentru a genera inamici specifici
        current_node_name = self.map_nodes[self.current_node_index]["name"]

        if current_node_name == "Sunnydale Harbor":
            enemy1 = Unit(name="Thief A", hp=45, base_attack=12, base_defense=3, sprite_path="assets/Thief.png", crit_chance=20, base_speed=16, is_enemy=True)
            enemy2 = Unit(name="Thief B", hp=45, base_attack=12, base_defense=3, sprite_path="assets/Thief.png", crit_chance=20, base_speed=14, is_enemy=True)
            self.enemies = [enemy1, enemy2]
        elif current_node_name == "Graveyard":
            enemy1 = Unit(name="Skeleton A", hp=50, base_attack=14, base_defense=4, sprite_path="assets/Skeleton.png", crit_chance=15, base_speed=10, is_enemy=True)
            enemy2 = Unit(name="Skeleton B", hp=50, base_attack=14, base_defense=4, sprite_path="assets/Skeleton.png", crit_chance=15, base_speed=12, is_enemy=True)
            self.enemies = [enemy1, enemy2]
        elif current_node_name == "Troll Bridge":

            enemy1 = Unit(name="Bridge Troll", hp=180, base_attack=24, base_defense=9, sprite_path="assets/TrollEnemy.png", crit_chance=10, base_speed=6, is_enemy=True)
            self.enemies = [enemy1]
        elif current_node_name == "Whitewalker Mountain":
            enemy1 = Unit(name="White Walker", hp=95, base_attack=18, base_defense=6, sprite_path="assets/WhiteWalker.png", crit_chance=10, base_speed=14, is_enemy=True)
            enemy2 = Unit(name="White Walker", hp=95, base_attack=18, base_defense=6, sprite_path="assets/WhiteWalker.png", crit_chance=10, base_speed=12, is_enemy=True)
            self.enemies = [enemy1, enemy2]
        elif current_node_name == "Dragon's Peak":
            enemy1 = Unit(name="Dragon", hp=250, base_attack=25, base_defense=10, sprite_path="assets/Dragon.png", crit_chance=15, base_speed=10, is_enemy=True)
            self.enemies = [enemy1]
        else:
            enemy1 = Unit(name=f"{current_node_name} Guard A", hp=75, base_attack=20, base_defense=6, sprite_path="assets/Goblin.png", crit_chance=25, base_speed=12, is_enemy=True)
            enemy2 = Unit(name=f"{current_node_name} Guard B", hp=75, base_attack=20, base_defense=6, sprite_path="assets/Goblin.png", crit_chance=25, base_speed=16, is_enemy=True)
            self.enemies = [enemy1, enemy2]

        # Începe prima rundă de luptă
        self.start_round()

    def advance_turn(self):
        """
        Avansează rândul în luptă. Elimină personajele/inamicii morți și
        verifică condițiile de victorie sau înfrângere.
        """

        # Elimină inamicii care au rămas fără viață (HP <= 0)
        for i in range(len(self.enemies)):
            if self.enemies[i] is not None and self.enemies[i].current_hp <= 0:
                self.enemies[i] = None


        # Verifică dacă toți inamicii au fost învinși (Victorie)
        if not any(e for e in self.enemies if e is not None):
            self.state = "VICTORY"
            return


        # Verifică dacă toată echipa a fost învinsă (Game Over)
        if not any(p for p in self.party.members if p is not None and p.current_hp > 0):
            print("GAME OVER")
            self.state = "MAP"
            return

        self.current_turn_index += 1
        if self.current_turn_index >= len(self.turn_queue):
            self.start_round()
        else:
            for u in self.turn_queue:
                if u and u.current_hp > 0:
                    u.process_statuses()


            if not any(e for e in getattr(self, 'enemies', []) if e is not None and e.current_hp > 0):
                self.advance_turn()
            elif not any(p for p in getattr(self.party, 'members', []) if p is not None and p.current_hp > 0):
                self.advance_turn()

    def get_random_attack_effect(self, unit):
        """
        Returnează o animație grafică de atac (tăietură de sabie, săgeată etc.)
        în funcție de clasa unității.
        """
        is_mage = type(unit).__name__ == "Mage" or (hasattr(unit, 'name') and "Mage" in getattr(unit, 'name', ''))
        is_archer = type(unit).__name__ == "Archer" or (hasattr(unit, 'name') and "Archer" in getattr(unit, 'name', ''))
        if is_mage:
            return random.choice(["assets/WizardAttack.png", "assets/WizardAttack2.png", "assets/WizardAttack3.png"])
        elif is_archer:
            return random.choice(["assets/ArrowAttack1.png", "assets/ArrowAttack2.png", "assets/ArrowAttack3.png"])
        else:
            return random.choice(["assets/VerticalSlashes1.png", "assets/VerticalSlashes2.png"])

    def draw_attack_effect(self, surface, x, y):
        """
        Randează pe ecran animația de atac peste țintă (ex: lovitură de sabie).
        Efectul este centrat pe coordonatele (x, y) ale țintei.
        """
        frames = getattr(self, 'animation_frames_left', 0)
        path = getattr(self, 'animation_effect_path', None)
        if frames <= 0 or not path: return

        img = self.get_image(path)
        if img:
            img = pygame.transform.smoothscale(img, (150, 150))
            surface.blit(img, (x - 40, y - 45))

    def draw(self, surface):
        """
        Metoda principală de desenare (render) a întregului joc. Apelează funcțiile
        de desenare specifice în funcție de starea jocului (Meniu, Hartă, Luptă etc.).
        """
        # Desenarea Meniului Principal
        if self.state == "MAIN_MENU":
            if self.main_menu_image:
                surface.blit(self.main_menu_image, (0, 0))
            else:
                surface.fill((20, 20, 25))


            title_shadow = font_large.render("EPYC", True, (255, 255, 255))
            title = font_large.render("EPYC", True, (0, 0, 0))


            title_y = HEIGHT // 2 - 50
            surface.blit(title_shadow, (WIDTH//2 - title_shadow.get_width()//2 + 3, title_y + 3))
            surface.blit(title, (WIDTH//2 - title.get_width()//2, title_y))


            prompt_shadow = font_medium.render("Press SPACE to Start", True, (0, 0, 0))
            prompt = font_medium.render("Press SPACE to Start", True, (255, 255, 255))
            surface.blit(prompt_shadow, (WIDTH//2 - prompt_shadow.get_width()//2 + 2, HEIGHT - 100 + 2))
            surface.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT - 100))

        # Desenarea Hărții și ecranelor adiacente
        elif self.state in ("MAP", "INVENTORY", "PARTY_SELECT"):
            # Afișează imaginea de fundal a hărții
            surface.blit(self.map_image, (0, 0))

            # Creează un strat transparent pentru a desena liniile și nodurile
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

            # Parcurge fiecare nod (locație) de pe hartă
            for i, node in enumerate(self.map_nodes):
                pos = node["pos"]

                # Desenează liniile care conectează nodurile consecutive
                if i < len(self.map_nodes) - 1:
                    next_pos = self.map_nodes[i+1]["pos"]
                    pygame.draw.line(overlay, (200, 200, 200, 0), pos, next_pos, 4)

                # Obține setul de noduri finalizate și indexul celui mai avansat nod deblocat
                completed = getattr(self, 'completed_nodes', set())
                unlocked = getattr(self, 'unlocked_node_index', 0)

                # Stabilește culoarea nodului în funcție de starea lui
                if i in completed:
                    color = (50, 200, 50, 150) # Verde pentru finalizat
                elif i > unlocked:
                    color = (100, 100, 100, 150) # Gri pentru blocat
                else:
                    color = (255, 255, 255, 150) # Alb pentru deblocat (neînceput)

                # Evidențiază nodul la care se află jucătorul în prezent
                if i == self.current_node_index:
                    color = (255, 255, 0, 255) # Galben pentru locația curentă

                # Desenează punctul nodului pe stratul transparent
                pygame.draw.circle(overlay, color, pos, 15)

                # Afișează numele locației sub nodul curent
                if i == self.current_node_index:
                    text = node["name"]

                    # Randează textul cu fontul de locație
                    text_surface = font_location.render(text, True, (255, 215, 0))
                    tw, th = text_surface.get_size()

                    # Calculează poziția textului pentru a-l centra sub nod
                    text_x = pos[0] - tw // 2
                    text_y = pos[1] + 20

                    # Desenează o umbră sub text pentru lizibilitate
                    label_shadow = font_location.render(text, True, (40, 20, 10))
                    surface.blit(label_shadow, (text_x + 2, text_y + 2))

                    # Desenează textul principal
                    surface.blit(text_surface, (text_x, text_y))

            # Aplică stratul transparent peste ecran
            surface.blit(overlay, (0, 0))

            # Afișează instrucțiunile de control în partea de jos a ecranului
            instruction = font_small.render("A/D to Move | I for Inventory | P for Party | ENTER to Fight", True, (255, 255, 255))
            surface.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT - 30))

            # Desenează ecranele adiacente (suprapuse peste hartă)
            if self.state == "INVENTORY":
                self.draw_inventory(surface)
            elif self.state == "PARTY_SELECT":
                self.draw_party_select(surface)

        # Desenarea ecranului de Luptă și Victorie
        elif self.state in ["COMBAT", "VICTORY"]:
            current_node_name = self.map_nodes[self.current_node_index]['name']


            bg_path = None
            sprite_base_y = 450

            if current_node_name == "Sunnydale Harbor":
                bg_path = "assets/HarborBackground.png"
                sprite_base_y = 450
            elif current_node_name == "Graveyard":
                bg_path = "assets/GraveyardBackground.png"
                sprite_base_y = 400
            elif current_node_name == "Whispering Woods":
                bg_path = "assets/WhisperingWoodsBackground.png"
                sprite_base_y = 400
            elif current_node_name == "Troll Bridge":
                bg_path = "assets/TrollBridgeBackground.png"
                sprite_base_y = 465
            elif current_node_name == "Whitewalker Mountain":
                bg_path = "assets/MountainBackground.png"
                sprite_base_y = 450
            elif current_node_name == "Dragon's Peak":
                bg_path = "assets/DragonLair.png"
                sprite_base_y = 450

            if bg_path:
                scaled_bg_key = f"{bg_path}_scaled"
                if scaled_bg_key not in self.image_cache:
                    bg_img = self.get_image(bg_path)
                    if bg_img:
                        self.image_cache[scaled_bg_key] = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
                if scaled_bg_key in self.image_cache:
                    surface.blit(self.image_cache[scaled_bg_key], (0, 0))

            title = font_medium.render(f"Combat at {current_node_name}! (SPACE to pass turn, ESC to flee)", True, (250, 100, 100))
            surface.blit(title, (50, 30))


            queue_title = font_medium.render("Turn Queue:", True, (255, 255, 255))
            surface.blit(queue_title, (50, 80))

            # Desenarea ordinii rândurilor (turn queue)
            # Coordonatele inițiale pentru afișarea barei de ordine a rândurilor (turn queue)
            x_offset = 220
            queue_y = 65
            for i, unit in enumerate(self.turn_queue):
                is_active = (i == self.current_turn_index)

                # Determinăm iconița personajului (prioritizăm casca, altfel folosim sprite-ul de bază)
                icon_path = None
                if getattr(unit, "headgear", None) and getattr(unit.headgear, "sprite_path", None):
                    icon_path = unit.headgear.sprite_path
                elif getattr(unit, "sprite_path", None):
                    icon_path = unit.sprite_path

                icon_img = self.get_image(icon_path) if icon_path else None

                # Desenăm chenarul pentru fiecare unitate din listă
                box_rect = pygame.Rect(x_offset, queue_y, 50, 50)
                if is_active:
                    # Galben îngroșat pentru unitatea a cărei rând este activ
                    pygame.draw.rect(surface, (255, 255, 50), box_rect, 3)
                else:
                    # Roșu pentru inamici, albastru deschis pentru echipa noastră
                    border_color = (255, 100, 100) if getattr(unit, 'is_enemy', False) else (100, 200, 255)
                    pygame.draw.rect(surface, border_color, box_rect, 1)

                if icon_img:
                    w, h = icon_img.get_size()

                    # Dacă unitatea este un inamic cunoscut, decupăm doar fața pentru iconiță
                    if icon_path and ("Thief.png" in icon_path or "Skeleton.png" in icon_path or "Goblin.png" in icon_path or "goblin.png" in icon_path or "WhiteWalker.png" in icon_path):
                        face_size = min(w, h // 3)
                        face_rect = pygame.Rect(w // 2 - face_size // 2, 0, face_size, face_size)
                        icon_img = icon_img.subsurface(face_rect)
                        w, h = icon_img.get_size()

                    # Scalăm iconița pentru a încăpea în chenar (50x50 px)
                    max_dim = max(w, h)
                    if max_dim > 0:
                        scale = 46.0 / max_dim
                        scaled_img = pygame.transform.smoothscale(icon_img, (int(w * scale), int(h * scale)))

                        # Centrăm iconița în chenar
                        ix = x_offset + (50 - scaled_img.get_width()) // 2
                        iy = queue_y + (50 - scaled_img.get_height()) // 2
                        surface.blit(scaled_img, (ix, iy))
                else:
                    # Fallback (text) dacă imaginea nu este găsită
                    label = font_small.render(unit.name[:3], True, (255,255,255))
                    surface.blit(label, (x_offset + 5, queue_y + 15))

                x_offset += 60


            # Desenarea membrilor echipei în luptă
            # Setăm coordonatele de bază pentru afișarea echipei
            px, py = 150, sprite_base_y
            for p in self.party.members:
                if p is not None:
                    drawn = False
                    current_sprite_path = p.sprite_path
                    
                    # Verificăm dacă este rândul personajului curent sau dacă este implicat într-o animație de atac
                    current_turn_unit = self.turn_queue[self.current_turn_index] if getattr(self, 'turn_queue', []) else None
                    is_active_turn = (p == current_turn_unit)
                    is_combat_stance = getattr(self, 'animating_unit', None) == p or is_active_turn

                    # Schimbăm sprite-ul în funcție de starea personajului (mort sau în luptă)
                    if p.current_hp <= 0:
                        current_sprite_path = "assets/DeadChar.png"
                    elif is_combat_stance and "BaseChar.png" in current_sprite_path:
                        current_sprite_path = current_sprite_path.replace("BaseChar.png", "CombatChar.png")

                    base_img = self.get_image(current_sprite_path)
                    if base_img:
                        # Scalăm imaginea de bază dacă este prea mare
                        if base_img.get_height() > 150:
                            b_scale = 108.0 / base_img.get_height()
                            base_img = pygame.transform.smoothscale(base_img, (max(1, int(base_img.get_width() * b_scale)), 108))

                        # Afișăm personajul
                        surface.blit(base_img, (px, py - base_img.get_height() + 80))
                        drawn = True

                        # Desenăm echipamentul personajului (armură, armă, cască)
                        for item in [p.armor, p.weapon, p.headgear]:
                            if item and getattr(item, "sprite_path", None):
                                item_img = self.get_image(item.sprite_path)
                                if item_img:

                                    # Setăm coordonatele de bază pentru obiecte, raportat la personaj
                                    base_x = px
                                    base_y = py - base_img.get_height() + 80

                                    # Căutăm date despre offset-uri specifice (poziționare personalizată)
                                    offset_data = None
                                    if hasattr(self, 'equipment_offsets'):
                                        if item.sprite_path in self.equipment_offsets:
                                            if current_sprite_path in self.equipment_offsets[item.sprite_path]:
                                                offset_data = self.equipment_offsets[item.sprite_path][current_sprite_path]

                                    # Dacă avem date specifice de offset, ajustăm scala, rotația și poziția
                                    if offset_data:
                                        scale_factor = offset_data.get("scale", None)
                                        if scale_factor is not None and scale_factor != 1.0:
                                            item_img = pygame.transform.smoothscale(item_img, (max(1, int(item_img.get_width() * scale_factor)), max(1, int(item_img.get_height() * scale_factor))))
                                        elif scale_factor is None and item_img.get_height() > 150:
                                            scale = 48.0 / item_img.get_height()
                                            item_img = pygame.transform.smoothscale(item_img, (int(item_img.get_width() * scale), 48))

                                        item_img = pygame.transform.rotate(item_img, offset_data.get("rot", 0))
                                        ix = base_x + offset_data.get("dx", 0)
                                        iy = base_y + offset_data.get("dy", 0)
                                    # Dacă nu avem date specifice, aplicăm offset-uri standard în funcție de tipul obiectului
                                    else:
                                        if item_img.get_height() > 150:
                                            scale = 48.0 / item_img.get_height()
                                            item_img = pygame.transform.smoothscale(item_img, (int(item_img.get_width() * scale), 48))

                                        if isinstance(item, Headgear):
                                            ix = base_x + (base_img.get_width() - item_img.get_width()) // 2
                                            iy = base_y - 12
                                            if is_combat_stance and "CombatChar" in current_sprite_path:
                                                ix += 13
                                                iy += 7
                                        elif isinstance(item, Armor):
                                            if is_combat_stance and "CombatChar" in current_sprite_path:
                                                item_img = pygame.transform.rotate(item_img, -10)
                                                ix = base_x + (base_img.get_width() - item_img.get_width()) // 2 + 14
                                                iy = base_y + 31
                                            else:
                                                ix = base_x + (base_img.get_width() - item_img.get_width()) // 2 - 3
                                                iy = base_y + 28
                                        else:
                                            # Poziționare pentru armă
                                            ix = base_x + base_img.get_width() - 20
                                            iy = base_y + 40

                                    # Afișăm obiectul echipat
                                    surface.blit(item_img, (ix, iy))

                    # Fallback dacă imaginea nu poate fi încărcată
                    if not drawn:
                        pygame.draw.rect(surface, (100, 200, 255), (px, py, 40, 80))

                    # Desenăm bara de HP (viață) doar dacă personajul este în viață
                    if p.current_hp > 0:

                        # Setările grafice pentru bara de HP
                        bar_w = 40
                        bar_h = 6
                        hp_ratio = p.current_hp / max(1, getattr(p, 'max_hp', 1))
                        bar_x = px + 15
                        
                        # Bara de fundal (viață pierdută - roșu închis)
                        pygame.draw.rect(surface, (80, 20, 20), (bar_x, py - 65, bar_w, bar_h))
                        # Bara din față (viață actuală - verde)
                        if hp_ratio > 0:
                            pygame.draw.rect(surface, (50, 200, 50), (bar_x, py - 65, int(bar_w * hp_ratio), bar_h))
                        # Conturul barei de viață
                        pygame.draw.rect(surface, (255, 255, 255), (bar_x, py - 65, bar_w, bar_h), 1)


                        # Afișăm valoarea HP ca text
                        hp_text = font_small.render(f"{p.current_hp}/{getattr(p, 'max_hp', 1)}", True, (0, 0, 0))
                        surface.blit(hp_text, (bar_x + bar_w + 5, py - 69))


                        sx = bar_x
                        for stat in p.statuses.keys():
                            icon_path = None
                            if stat == "Bleed": icon_path = "assets/BleedStatus.png"
                            elif stat == "Fire": icon_path = "assets/FireStatus.png"
                            if icon_path:
                                icon_img = self.get_image(icon_path)
                                if icon_img:
                                    icon_img = pygame.transform.smoothscale(icon_img, (16, 16))
                                    surface.blit(icon_img, (sx, py - 85))
                                    sx += 18

                    if p == getattr(self, 'animation_target', None) and getattr(self, 'animation_frames_left', 0) > 0:
                        self.draw_attack_effect(surface, px, py)

                px += 100



            # Desenarea inamicilor în luptă
            ex, ey = 550, sprite_base_y
            for e in self.enemies:
                if e is not None:
                    drawn = False
                    current_sprite_path = e.sprite_path
                    current_turn_unit = self.turn_queue[self.current_turn_index] if getattr(self, 'turn_queue', []) else None
                    is_active_turn = (e == current_turn_unit)
                    is_combat_stance = getattr(self, 'animating_unit', None) == e or is_active_turn

                    if is_combat_stance and "Thief.png" in current_sprite_path:
                        current_sprite_path = current_sprite_path.replace("Thief.png", "ThiefAttack.png")
                    elif is_combat_stance and ("Goblin.png" in current_sprite_path or "goblin.png" in current_sprite_path):
                        current_sprite_path = current_sprite_path.replace("Goblin.png", "GoblinAttack.png").replace("goblin.png", "GoblinAttack.png")
                    elif is_combat_stance and "TrollEnemy.png" in current_sprite_path:
                        current_sprite_path = current_sprite_path.replace("TrollEnemy.png", "TrollAtack.png")
                    elif is_combat_stance and "WhiteWalker.png" in current_sprite_path:
                        current_sprite_path = current_sprite_path.replace("WhiteWalker.png", "WhiteWalkerAttack.png")


                    base_img = self.get_image(current_sprite_path)
                    if base_img:


                        target_h = base_img.get_height()
                        if "Thief" in current_sprite_path:


                            target_h = 135
                        elif "Skeleton" in current_sprite_path:
                            target_h = 145
                        elif "Goblin" in current_sprite_path or "goblin" in current_sprite_path:
                            target_h = 120
                        elif "WhiteWalker" in current_sprite_path:
                            target_h = 170
                        elif "Dragon" in current_sprite_path:
                            target_h = 350
                        elif target_h > 150:


                            target_h = 108


                        if target_h != base_img.get_height():

                            b_scale = target_h / base_img.get_height()

                            base_img = pygame.transform.smoothscale(base_img, (max(1, int(base_img.get_width() * b_scale)), target_h))




                        surface.blit(base_img, (ex, ey - base_img.get_height() + 80))
                        drawn = True


                    if not drawn:
                        pygame.draw.rect(surface, (255, 100, 100), (ex, ey, 40, 80))


                    bar_w = 40
                    bar_h = 6
                    hp_ratio = e.current_hp / max(1, getattr(e, 'max_hp', 1))
                    if "WhiteWalker" in current_sprite_path:
                        bar_x = ex + 35
                        bar_y = ey - 125
                    elif "Dragon" in current_sprite_path:
                        bar_x = ex + 120
                        bar_y = ey - 280
                    else:
                        bar_x = ex + 35
                        bar_y = ey - 65
                    pygame.draw.rect(surface, (80, 20, 20), (bar_x, bar_y, bar_w, bar_h))
                    if hp_ratio > 0:
                        pygame.draw.rect(surface, (200, 50, 50), (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
                    pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 1)


                    hp_text = font_small.render(f"{e.current_hp}/{getattr(e, 'max_hp', 1)}", True, (0, 0, 0))
                    surface.blit(hp_text, (bar_x + bar_w + 5, bar_y - 4))


                    sx = bar_x
                    for stat in e.statuses.keys():
                        icon_path = None
                        if stat == "Bleed": icon_path = "assets/BleedStatus.png"
                        elif stat == "Fire": icon_path = "assets/FireStatus.png"
                        if icon_path:
                            icon_img = self.get_image(icon_path)
                            if icon_img:
                                icon_img = pygame.transform.smoothscale(icon_img, (16, 16))
                                surface.blit(icon_img, (sx, bar_y - 20))
                                sx += 18

                    if e == getattr(self, 'animation_target', None) and getattr(self, 'animation_frames_left', 0) > 0:
                        self.draw_attack_effect(surface, ex, ey)


                ex += 100

            # Afișarea ecranului de Victorie
            if self.state == "VICTORY":

                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                surface.blit(overlay, (0, 0))


                vic_text = font_large.render("VICTORY!", True, (255, 215, 0))
                surface.blit(vic_text, (WIDTH // 2 - vic_text.get_width() // 2, HEIGHT // 2 - 50))

                sub_text = font_medium.render("Click or press any key to return to map...", True, (255, 255, 255))
                surface.blit(sub_text, (WIDTH // 2 - sub_text.get_width() // 2, HEIGHT // 2 + 20))

# Punctul de pornire al aplicației
if __name__ == "__main__":
    game = Game()
    game.run()
