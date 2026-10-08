import random
import json
import os

# Dicționar global pentru statisticile obiectelor
ITEM_STATS = {}
# Verifică dacă există fișierul items.json și îl citește pentru a popula ITEM_STATS
if os.path.exists("items.json"):
    with open("items.json", "r") as f:
        ITEM_STATS = json.load(f)

# Clasa Weapon (Armă) definește proprietățile și bonusurile pe care o armă le oferă unui personaj
class Weapon:
    def __init__(self, name: str, attack_bonus: int, sprite_path: str, magic_bonus: int = 0, speed_bonus: int = 0, defense_bonus: int = 0, hp_bonus: int = 0, crit_bonus: int = 0):
        stats = ITEM_STATS.get(sprite_path, {})
        self.name = stats.get("name", name)
        self.attack_bonus = stats.get("attack_bonus", attack_bonus)
        self.magic_bonus = stats.get("magic_bonus", magic_bonus)
        self.speed_bonus = stats.get("speed_bonus", speed_bonus)
        self.defense_bonus = stats.get("defense_bonus", defense_bonus)
        self.hp_bonus = stats.get("hp_bonus", hp_bonus)
        self.crit_bonus = stats.get("crit_bonus", crit_bonus)
        self.allowed_classes = stats.get("allowed_classes", None)
        self.sprite_path = sprite_path

# Clasa Armor (Armură) definește echipamentul pentru corp și protecția oferită
class Armor:
    def __init__(self, name: str, defense_bonus: int, sprite_path: str, attack_bonus: int = 0, magic_bonus: int = 0, speed_bonus: int = 0, hp_bonus: int = 0, crit_bonus: int = 0):
        stats = ITEM_STATS.get(sprite_path, {})
        self.name = stats.get("name", name)
        self.defense_bonus = stats.get("defense_bonus", defense_bonus)
        self.attack_bonus = stats.get("attack_bonus", attack_bonus)
        self.magic_bonus = stats.get("magic_bonus", magic_bonus)
        self.speed_bonus = stats.get("speed_bonus", speed_bonus)
        self.hp_bonus = stats.get("hp_bonus", hp_bonus)
        self.crit_bonus = stats.get("crit_bonus", crit_bonus)
        self.allowed_classes = stats.get("allowed_classes", None)
        self.sprite_path = sprite_path

# Clasa Headgear (Cască/Pălărie) definește echipamentul pentru cap și bonusurile aferente
class Headgear:
    def __init__(self, name: str, defense_bonus: int, sprite_path: str, attack_bonus: int = 0, magic_bonus: int = 0, speed_bonus: int = 0, hp_bonus: int = 0, crit_bonus: int = 0):
        stats = ITEM_STATS.get(sprite_path, {})
        self.name = stats.get("name", name)
        self.defense_bonus = stats.get("defense_bonus", defense_bonus)
        self.attack_bonus = stats.get("attack_bonus", attack_bonus)
        self.magic_bonus = stats.get("magic_bonus", magic_bonus)
        self.speed_bonus = stats.get("speed_bonus", speed_bonus)
        self.hp_bonus = stats.get("hp_bonus", hp_bonus)
        self.crit_bonus = stats.get("crit_bonus", crit_bonus)
        self.allowed_classes = stats.get("allowed_classes", None)
        self.sprite_path = sprite_path

# Clasa principală Unit reprezintă un personaj din joc (fie jucător, fie inamic)
class Unit:
    def __init__(self, name: str, hp: int, base_attack: int, base_defense: int, sprite_path: str, crit_chance: int = 5, base_magic: int = 0, base_speed: int = 10, is_enemy: bool = False):
        self.name = name
        self.base_max_hp = hp
        self.base_attack = base_attack
        self.base_defense = base_defense
        self.base_magic = base_magic
        self.base_speed = base_speed
        self.sprite_path = sprite_path
        self.base_crit_chance = crit_chance
        self.is_enemy = is_enemy
        self.weapon = None
        self.armor = None
        self.headgear = None
        self.statuses = {}
        self.current_hp = self.max_hp

    # Calculează viața maximă adunând HP-ul de bază cu bonusurile de la echipament
    @property
    def max_hp(self) -> int:
        wpn = self.weapon.hp_bonus if self.weapon else 0
        arm = self.armor.hp_bonus if self.armor else 0
        hdg = self.headgear.hp_bonus if self.headgear else 0
        return self.base_max_hp + wpn + arm + hdg

    @property
    def attack_power(self) -> int:
        wpn = self.weapon.attack_bonus if self.weapon else 0
        arm = self.armor.attack_bonus if self.armor else 0
        hdg = self.headgear.attack_bonus if self.headgear else 0
        return self.base_attack + wpn + arm + hdg

    @property
    def magic_power(self) -> int:
        wpn = self.weapon.magic_bonus if self.weapon else 0
        arm = self.armor.magic_bonus if self.armor else 0
        hdg = self.headgear.magic_bonus if self.headgear else 0
        return self.base_magic + wpn + arm + hdg

    @property
    def defense_power(self) -> int:
        wpn = self.weapon.defense_bonus if self.weapon else 0
        arm = self.armor.defense_bonus if self.armor else 0
        hdg = self.headgear.defense_bonus if self.headgear else 0
        return self.base_defense + wpn + arm + hdg

    @property
    def speed(self) -> int:
        wpn = self.weapon.speed_bonus if self.weapon else 0
        arm = self.armor.speed_bonus if self.armor else 0
        hdg = self.headgear.speed_bonus if self.headgear else 0
        return self.base_speed + wpn + arm + hdg

    @property
    def crit_chance(self) -> int:
        wpn = self.weapon.crit_bonus if self.weapon else 0
        arm = self.armor.crit_bonus if self.armor else 0
        hdg = self.headgear.crit_bonus if self.headgear else 0
        return self.base_crit_chance + wpn + arm + hdg

    # Calculează șansa de a eschiva (evita) atacurile pe baza vitezei (șansa maximă limitată la 50%)
    @property
    def dodge_chance(self) -> int:
        return min(50, max(0, self.speed - 10))

    # Echipează o armă personajului
    def equip_weapon(self, weapon: Weapon):
        self.weapon = weapon
        # Funcția 'hasattr(obiect, "nume_atribut")' verifică dacă un atribut (în acest caz 'current_hp') a fost deja definit.
        # Această verificare este utilă în timpul creării personajului (__init__), când arma e echipată înainte de a seta 'current_hp', pentru a evita o eroare.
        # De asemenea, asigură că viața curentă nu depășește noua viață maximă.
        if hasattr(self, 'current_hp') and self.current_hp > self.max_hp:
            self.current_hp = self.max_hp

    # Echipează o armură
    def equip_armor(self, armor: Armor):
        self.armor = armor
        if hasattr(self, 'current_hp') and self.current_hp > self.max_hp:
            self.current_hp = self.max_hp

    # Echipează o cască sau o pălărie
    def equip_headgear(self, headgear: Headgear):
        self.headgear = headgear
        if hasattr(self, 'current_hp') and self.current_hp > self.max_hp:
            self.current_hp = self.max_hp

    # Funcție apelată atunci când unitatea primește daune. Returnează True dacă unitatea moare.
    def take_damage(self, incoming_damage: int) -> bool:
        # Verifică dacă unitatea se ferește de atac
        if random.randint(1, 100) <= self.dodge_chance:
            print(f"{self.name} a ESCHIVAT atacul!")
            return False

        # Scade apărarea din daunele primite și actualizează viața curentă
        actual_damage = max(1, incoming_damage - self.defense_power)
        self.current_hp = max(0, self.current_hp - actual_damage)
        return self.current_hp <= 0

    # Aplică un efect de status asupra personajului (ex. Sângerare, Foc) pentru un anumit număr de runde (duration).
    def apply_status(self, status_name: str, duration: int):
        # Dacă personajul are deja acest status, se păstrează durata cea mai mare (nu se adună).
        if status_name in self.statuses:
            self.statuses[status_name] = max(self.statuses[status_name], duration)
        else:
            # Dacă personajul nu are acest status, este adăugat în dicționar.
            self.statuses[status_name] = duration
            
    # Procesează efectele de status (cum ar fi Sângerare sau Foc) și aplică daune la fiecare rând (rundă)
    def process_statuses(self):
        expired = [] # O listă temporară pentru a ține minte statusurile care expiră în această rundă
        for status, duration in self.statuses.items():
            # Aplicăm efectele specifice în funcție de tipul de status
            if status == "Bleed":
                damage = 3
                self.current_hp -= damage
            elif status == "Fire":
                damage = 12
                self.current_hp -= damage
                
            # Scădem durata statusului cu o rundă
            self.statuses[status] -= 1
            
            # Dacă durata a ajuns la 0, înseamnă că statusul a expirat și trebuie eliminat
            if self.statuses[status] <= 0:
                expired.append(status)
                
        # Ștergem din dicționarul de statusuri tot ce a expirat
        for status in expired:
            del self.statuses[status]

    def display_status(self):
        wpn = self.weapon.name if self.weapon else "Unarmed"
        arm = self.armor.name if self.armor else "Unarmored"
        hdg = self.headgear.name if self.headgear else "Barehead"
        
        print(f"[{self.name}] | HP: {self.current_hp}/{self.max_hp} | ATK: {self.attack_power} | MAG: {self.magic_power} | DEF: {self.defense_power} | SPD: {self.speed} | CRIT: {self.crit_chance}% | DODGE: {self.dodge_chance}%")
        print(f"      Gear -> Wpn: {wpn} | Arm: {arm} | Head: {hdg}")


# --- CLASELE JUCĂTORILOR (PLAYER CLASSES) ---
# Fiecare clasă moștenește proprietățile de bază din Unit și are propriile statistici și echipament

# Clasa Crusader (Cruciat) - Un tanc cu apărare și viață mare
class Crusader(Unit):
    def __init__(self, name="Crusader"):
        super().__init__(name=name, hp=60, base_attack=6, base_defense=4, sprite_path="assets/BaseChar.png", crit_chance=5, base_magic=2, base_speed=5)
        self.equip_weapon(Weapon("Crusader Sword", attack_bonus=6, sprite_path="assets/CrusaderSword.png", defense_bonus=1, speed_bonus=-1, crit_bonus=5, magic_bonus=1, hp_bonus=10))
        self.equip_armor(Armor("Crusader Armor", defense_bonus=6, sprite_path="assets/CrusaderArmor.png", speed_bonus=-4, hp_bonus=15, attack_bonus=2, magic_bonus=0, crit_bonus=0))
        self.equip_headgear(Headgear("Greathelm", defense_bonus=3, sprite_path="assets/GreatHelm.png", attack_bonus=1, hp_bonus=5, speed_bonus=-1, magic_bonus=0, crit_bonus=0))
        self.current_hp = self.max_hp

# Clasa Mage (Mag) - Un personaj axat pe putere magică, dar fragil
class Mage(Unit):
    def __init__(self, name="Mage"):
        super().__init__(name=name, hp=30, base_attack=2, base_defense=2, sprite_path="assets/BaseChar.png", crit_chance=5, base_magic=12, base_speed=10)
        self.equip_weapon(Weapon("Wooden Staff", attack_bonus=1, sprite_path="assets/MageStaff.png", magic_bonus=8, defense_bonus=1, speed_bonus=1, crit_bonus=2, hp_bonus=5))
        self.equip_armor(Armor("Archmage Robes", defense_bonus=2, sprite_path="assets/MageRobes.png", magic_bonus=4, hp_bonus=10, speed_bonus=2, attack_bonus=0, crit_bonus=1))
        self.equip_headgear(Headgear("Wizard Hat", defense_bonus=1, sprite_path="assets/MageHat.png", magic_bonus=2, hp_bonus=5, speed_bonus=1, attack_bonus=0, crit_bonus=2))
        self.current_hp = self.max_hp

# Clasa Rogue (Asasin) - Se bazează pe viteză mare și lovituri critice
class Rogue(Unit):
    def __init__(self, name="Rogue"):
        super().__init__(name=name, hp=40, base_attack=8, base_defense=2, sprite_path="assets/BaseChar.png", crit_chance=15, base_magic=0, base_speed=15)
        self.equip_weapon(Weapon("Rusty Dagger", attack_bonus=5, sprite_path="assets/RogueSword.png", speed_bonus=3, crit_bonus=10, defense_bonus=0, magic_bonus=0, hp_bonus=0))
        self.equip_armor(Armor("Shadow Tunic", defense_bonus=3, sprite_path="assets/RogueArmor.png", speed_bonus=4, attack_bonus=3, crit_bonus=5, hp_bonus=10, magic_bonus=2))
        self.equip_headgear(Headgear("Rogue Helmet", defense_bonus=1, sprite_path="assets/RogueHelmet.png", speed_bonus=2, crit_bonus=5, hp_bonus=5, attack_bonus=1, magic_bonus=0))
        self.current_hp = self.max_hp

# Clasa Cleric (Cleric) - Un personaj de suport cu echilibru între atac și magie
class Cleric(Unit):
    def __init__(self, name="Cleric"):
        super().__init__(name=name, hp=45, base_attack=4, base_defense=3, sprite_path="assets/cleric.png", crit_chance=5, base_magic=8, base_speed=8)
        self.equip_weapon(Weapon("Holy Mace", attack_bonus=4, sprite_path="assets/weapons/holy_mace.png", magic_bonus=4, defense_bonus=1, hp_bonus=10, speed_bonus=-1, crit_bonus=5))
        self.equip_armor(Armor("Blessed Chainmail", defense_bonus=5, sprite_path="assets/armor/chainmail.png", magic_bonus=2, hp_bonus=15, speed_bonus=-2, attack_bonus=1, crit_bonus=0))
        self.equip_headgear(Headgear("Halo", defense_bonus=2, sprite_path="assets/headgear/halo.png", magic_bonus=2, hp_bonus=10, speed_bonus=1, attack_bonus=0, crit_bonus=2))
        self.current_hp = self.max_hp

# Clasa Archer (Arcaș) - Oferă daune fizice bune de la distanță și are viteză mare
class Archer(Unit):
    def __init__(self, name="Archer"):
        super().__init__(name=name, hp=35, base_attack=7, base_defense=2, sprite_path="assets/BaseChar.png", crit_chance=10, base_magic=0, base_speed=12)
        self.equip_weapon(Weapon("Shortbow", attack_bonus=7, sprite_path="assets/StartingBow.png", speed_bonus=2, crit_bonus=5, defense_bonus=1, magic_bonus=0, hp_bonus=5))
        self.equip_armor(Armor("Archer Armor", defense_bonus=3, sprite_path="assets/ArcherArmor.png", speed_bonus=2, hp_bonus=10, attack_bonus=2, crit_bonus=5, magic_bonus=0))
        self.equip_headgear(Headgear("Archer Helmet", defense_bonus=2, sprite_path="assets/ArcherHelmet.png", speed_bonus=1, crit_bonus=5, hp_bonus=5, attack_bonus=1, magic_bonus=0))
        self.current_hp = self.max_hp


# --- GESTIONAREA ECHIPEI (PARTY MANAGEMENT) ---

# Clasa Party gestionează grupul de personaje jucabile
class Party:
    def __init__(self):
        self.max_size = 3
        # Sloturi fixe: Față/Front (0), Mijloc/Middle (1), Spate/Back (2)
        self.members = [None, None, None]
        self.inventory = []

    # Adaugă un membru în echipă pe o anumită poziție (0, 1 sau 2)
    def add_member(self, unit: Unit, position: int):
        if position < 0 or position >= self.max_size:
            print("Invalid position.")
            return False
        if self.members[position] is not None:
            print(f"Position {position} is already occupied!")
            return False
        
        self.members[position] = unit
        return True

    def display_party(self):
        print(f"\n--- Current Party ---")
        positions = ["Front", "Middle", "Back"]
        for i, member in enumerate(self.members):
            if member:
                print(f"[{positions[i]}] ", end="")
                member.display_status()
            else:
                print(f"[{positions[i]}] EMPTY")