import random
import math
import sys
import os
from collections import deque
import textwrap
import shutil
import json

# ostatní soubory
import core
import gear
import abilities
import character
import monsters



# ===== PRÁCE SE SOUBORY (SAVY)=====
ABILITY_DATABASE = {
    abilities.pain_for_all.name: abilities.pain_for_all,
    abilities.power_strike.name: abilities.power_strike,
    abilities.fast_strike.name: abilities.fast_strike,
    abilities.defensive_strike.name: abilities.defensive_strike,
    abilities.no_rest.name: abilities.no_rest,
    abilities.muscles.name: abilities.muscles,
    abilities.hard_root.name: abilities.hard_root,
    abilities.three_attack_draw.name: abilities.three_attack_draw,
    abilities.maintaining_defense.name: abilities.maintaining_defense,
}

ITEM_DATABASE = {
    gear.test_kill.name: gear.test_kill,
    # ===== ZÁKLADNÍ ZBRANĚ =====
    gear.dagger.name: gear.dagger,
    gear.sword.name: gear.sword,
    gear.broken_sword.name: gear.broken_sword,
    gear.flail.name: gear.flail,
    gear.battle_axe.name: gear.battle_axe,
    gear.mace.name: gear.mace,
    gear.poison_dagger.name: gear.poison_dagger,

    # ===== KULTISTKA =====
    gear.cultistic_blade.name: gear.cultistic_blade,
    gear.bloodthirsty_tongue.name: gear.bloodthirsty_tongue,
    gear.claw_dagger.name: gear.claw_dagger,
    gear.sacrificial_blade.name: gear.sacrificial_blade,
    gear.blade_of_blood_frenzy.name: gear.blade_of_blood_frenzy,
    gear.forbidden_texts.name: gear.forbidden_texts,
    gear.ritual_sickle.name: gear.ritual_sickle,
    gear.serpent_spear.name: gear.serpent_spear,

    # ===== PODPORA / POMOCNÉ =====
    gear.blood_vial.name: gear.blood_vial,
    gear.sacrificial_bone.name: gear.sacrificial_bone,

    # ===== MÁG =====
    gear.wooden_staff.name: gear.wooden_staff,
    gear.an_untitled_book.name: gear.an_untitled_book,

    # ===== ŠTÍTY =====
    gear.shield.name: gear.shield,
    gear.shield_with_spike.name: gear.shield_with_spike,
    gear.shield_e.name: gear.shield_e,

    # ===== ZBROJE =====
    gear.padded_armor.name: gear.padded_armor,
    gear.ritual_skirt.name: gear.ritual_skirt,
    gear.old_robe.name: gear.old_robe,
    gear.hide.name: gear.hide,
    gear.newborns_exoskelet.name: gear.newborns_exoskelet,
    gear.exoskelet.name: gear.exoskelet,
    gear.bark.name: gear.bark,

    # ===== PASTI / TRIKY =====
    gear.set_of_traps.name: gear.set_of_traps,
    gear.caltrops.name: gear.caltrops,

    # ===== POMOCNÉ ITEMY =====
    gear.war_paints.name: gear.war_paints,
    gear.abakus.name: gear.abakus,
    gear.battle_plans.name: gear.battle_plans,
    gear.rabits_paw.name: gear.rabits_paw,
    gear.madmans_eye.name: gear.madmans_eye,
    gear.ritual_statue.name: gear.ritual_statue,

    # ===== PRSTENY =====
    gear.ring_of_defense.name: gear.ring_of_defense,
    gear.wurm_ring.name: gear.wurm_ring,
    gear.poisoners_ring.name: gear.poisoners_ring,
    gear.ring_with_needle.name: gear.ring_with_needle,

    # ===== COMPANIONS =====
    gear.friendly_ant.name: gear.friendly_ant,
    gear.crow.name: gear.crow,
}

def deserialize_bestiary(data):
    return {
        name: {
            "seen": entry["seen"],
            "kills": entry["kills"],
            "seen_cards": set(entry.get("seen_cards", [])),
            "info": entry.get("info", {}),
            "all_cards": entry.get("all_cards", [])
        }
        for name, entry in data.items()
    }

def save_game(player):
    data = {
        "player": player.to_dict()
    }

    with open("save.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_game(path="save.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    p = data["player"]

    # ===== CREATE PLAYER =====
    player = character.Character(p["name"], p["max_hp"])

    # ===== BASIC STATS =====
    player.hp = p["hp"]
    player.max_hp = p["max_hp"]
    player.max_energy = p["max_energy"]
    player.extra_draw = p["extra_draw"]

    player.energy = player.max_energy
    player.strenght = p.get("strenght", 0)

    player.player_class = p.get("player_class")
    player.xp = p.get("xp", 0)
    player.lvl = p.get("lvl", 1)
    player.dungeon_level = p.get("dungeon_level", 1)

    # ===== INVENTORY =====
    player.inventory = [
        ITEM_DATABASE[name] for name in p.get("inventory", [])
        if name in ITEM_DATABASE
    ]

    # ===== EQUIPMENT (slots) =====
    player.slots = {}

    for slot, items in p.get("equipment", {}).items():
        player.slots[slot] = [
            ITEM_DATABASE[name] if name else None
            for name in items
        ]

    # ===== BESTIARY =====
    player.bestiary = p.get("bestiary", {})

    # ===== OPTIONAL FIELDS =====
    player.abilities = [
        ABILITY_DATABASE[name]
        for name in data["player"].get("abilities", [])
        if name in ABILITY_DATABASE
    ] # zatím jednoduché

    return player

#============================================================



def render_block(title, lines):
    render([f"--- {title} ---", ""] + lines + [""])


def render(lines):
    core.print_center_block("\n".join(lines))


def clear_screen():
    # Windows
    if os.name == "nt":
        os.system("cls")
    # Linux / Mac
    else:
        os.system("clear")
    print("\n")
    print("\n")


def get_terminal_width():
    return shutil.get_terminal_size().columns


def print_section(title, text, width=60):
    core.print_center_block("\n" + title.upper().center(width))
    core.print_center_block("-" * width)

    wrapped = textwrap.wrap(text, width)
    for line in wrapped:
        core.print_center_block(line)


class GameMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.grid = [["#" for _ in range(width)] for _ in range(height)]

        self.enemies = []
        self.locked_doors = []
        self.boss_rooms = []

        # fog of war
        self.visible = [[False for _ in range(width)] for _ in range(height)]
        self.explored = [[False for _ in range(width)] for _ in range(height)]

    def place_enemy(self, x, y):
        self.grid[y][x] = "E"

    def place_bonefire(self, x, y):
        self.grid[y][x] = "^"

    def place_chest(self, x, y):
        self.grid[y][x] = "▣"

    def place_door(self, x, y):
        self.grid[y][x] = "▮"

    def find_best_door_position(self, player_x, player_y):
        visited = set()
        queue = deque()
        queue.append((player_x, player_y, 0))  # x, y, score

        best_pos = (player_x, player_y)
        best_score = -1

        while queue:
            x, y, score = queue.popleft()

            if (x, y) in visited:
                continue
            visited.add((x, y))

            if self.grid[y][x] == ".":
                # bonus za nepřátele kolem
                enemy_bonus = 0
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if self.grid[ny][nx] == "E":
                            enemy_bonus += 3

                total_score = score + enemy_bonus

                if total_score > best_score:
                    best_score = total_score
                    best_pos = (x, y)

            # šíření BFS
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.grid[ny][nx] != "#":
                        queue.append((nx, ny, score + 1))

        return best_pos

    def generate_dungeon(self, room_min_count=5, room_max_count=7, room_min_size=2, room_max_size=3):
        rooms = []

        for _ in range(random.randint(room_min_count, room_max_count)):
            w = random.randint(room_min_size, room_max_size)
            h = random.randint(room_min_size, room_max_size)
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)

            new_room = RectRoom(x, y, w, h)

            if any(new_room.intersects(other) for other in rooms):
                continue

            for i in range(new_room.x1, new_room.x2):
                for j in range(new_room.y1, new_room.y2):
                    self.grid[j][i] = "."

            if rooms:
                prev_x, prev_y = rooms[-1].center()
                new_x, new_y = new_room.center()

                if random.random() < 0.5:
                    self.create_h_tunnel(prev_x, new_x, prev_y)
                    self.create_v_tunnel(prev_y, new_y, new_x)
                else:
                    self.create_v_tunnel(prev_y, new_y, prev_x)
                    self.create_h_tunnel(prev_x, new_x, new_y)

            rooms.append(new_room)
            self.add_dead_end_corridors(count=5, min_length=2, max_length=4)

        return rooms

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.grid[y][x] = "."

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.grid[y][x] = "."

    def add_dead_end_corridors(self, count=4, min_length=2, max_length=4):
        for _ in range(count):
            possible_starts = [(x, y) for y in range(self.height)
                               for x in range(self.width) if self.grid[y][x] == "."]

            if not possible_starts:
                break

            x, y = random.choice(possible_starts)
            dx, dy = random.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            length = random.randint(min_length, max_length)

            corridor_positions = []

            for _ in range(length):
                nx, ny = x + dx, y + dy

                if 0 < nx < self.width-1 and 0 < ny < self.height-1 and self.grid[ny][nx] == "#":
                    self.grid[ny][nx] = "."
                    corridor_positions.append((nx, ny))
                    x, y = nx, ny
                else:
                    # pokud jsme nedosáhli min_length, koridor se zahazuje
                    if len(corridor_positions) < min_length:
                        for cx, cy in corridor_positions:
                            self.grid[cy][cx] = "#"  # vrátíme zpět
                    break

    def generate_bonefire_positions(self, player_x, player_y, existing_fires=None, min_distance=3, max_attempts=100):
        if existing_fires is None:
            existing_fires = []

        candidates = []

        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                # Musí být volné a ne tam, kde je hráč
                if self.grid[y][x] != "." or (x, y) == (player_x, player_y):
                    continue

                # Kontrola vzdálenosti od ostatních ohnišť
                if any(abs(x - fx) + abs(y - fy) < min_distance for fx, fy in existing_fires):
                    continue

                # Kontrola 3x3 volných míst
                free_count = sum(
                    1
                    for dy in (-1, 0, 1)
                    for dx in (-1, 0, 1)
                    if self.grid[y + dy][x + dx] == "."
                )
                if free_count >= 5:
                    candidates.append((x, y))
                else:
                    # případně slepá ulička: jen jedna cesta ven
                    neighbors = [
                        (x + dx, y + dy)
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                        if 0 <= x + dx < self.width and 0 <= y + dy < self.height
                    ]
                    paths = sum(
                        1 for nx, ny in neighbors if self.grid[ny][nx] == ".")
                    if paths == 1:
                        candidates.append((x, y))

        if not candidates:
            # fallback
            return [(random.randint(0, self.width - 1), random.randint(0, self.height - 1))]

        chosen = random.choice(candidates)
        existing_fires.append(chosen)  # zaznamenáme nově vybrané ohniště
        return [chosen]

    def generate_chest_positions(self, player_x, player_y, chest_count=1, min_distance_from_doors=2):
        candidates = []

        # najdeme všechny dveře
        door_positions = [(x, y) for y in range(self.height)
                          for x in range(self.width) if self.grid[y][x] == "▮"]

        for y in range(1, self.height-1):
            for x in range(1, self.width-1):
                if self.grid[y][x] != "." or (x, y) == (player_x, player_y):
                    continue

                # kontrola vzdálenosti od dveří
                if any(abs(x - dx) + abs(y - dy) <= min_distance_from_doors for dx, dy in door_positions):
                    continue  # příliš blízko dveří

                # kontrola sousedů (slepá ulička)
                neighbors = [
                    (x + dx, y + dy)
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    if 0 <= x+dx < self.width and 0 <= y+dy < self.height
                ]
                free_neighbors = sum(
                    1 for nx, ny in neighbors if self.grid[ny][nx] == ".")
                if free_neighbors == 1:  # jen jedna cesta ven => slepá ulička
                    candidates.append((x, y))

        if not candidates:  # fallback: kdekoliv, kromě hráče
            candidates = [(x, y) for y in range(self.height)
                          for x in range(self.width) if self.grid[y][x] == "." and (x, y) != (player_x, player_y)]

        chosen = random.sample(candidates, min(chest_count, len(candidates)))
        return chosen

    # test na mapu
    def print_full_map(self):
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                row += self.grid[y][x] + " "  # přidáme mezeru mezi políčka
            core.print_center_block(row)

    def generate_objects(self, bonefire_count, chest_count, player_x, player_y, door_count=1, boss_room=None):
        existing_fires = []
        chest_positions = []
        door_positions = []

        boss_door = None
        # -------------------------------
        # 1) Normální dveře
        # -------------------------------
        for _ in range(door_count):
            x, y = self.find_best_door_position(player_x, player_y)

            # pokud je boss room, ignorujeme pozice uvnitř boss room
            if boss_room:
                if boss_room.x1 <= x <= boss_room.x2 and boss_room.y1 <= y <= boss_room.y2:
                    continue

            self.place_door(x, y)
            door_positions.append((x, y))

        # -------------------------------
        # 2) Truhly
        # -------------------------------
        for x, y in self.generate_chest_positions(player_x, player_y, chest_count=chest_count):
            self.place_chest(x, y)
            chest_positions.append((x, y))

        # -------------------------------
        # 3) Ohniště
        # -------------------------------
        for _ in range(bonefire_count):
            for x, y in self.generate_bonefire_positions(
                player_x, player_y,
                existing_fires=existing_fires,
                min_distance=3
            ):
                self.place_bonefire(x, y)
                existing_fires.append((x, y))

        # -------------------------------
        # 4) Stráže u dveří a truhel
        # -------------------------------
        for x, y in door_positions:
            if boss_door and (x, y) == boss_door:
                continue  # boss dveře nemají normální stráže
            self.place_door_guards(x, y)

        for x, y in chest_positions:
            self.place_chest_guard(x, y)

    def generate_enemies(self, count, player_x, player_y):
        for _ in range(count):
            while True:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)

                if (x, y) != (player_x, player_y) and self.grid[y][x] == ".":
                    self.place_enemy(x, y)
                    break

    def place_chest_guard(self, chest_x, chest_y):
        x, y = chest_x, chest_y
        prev = None
        last_valid = None

        while True:
            # najdi volné sousedy kromě políčka, odkud jsme přišli
            neighbors = [(x+dx, y+dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                         if 0 <= x+dx < self.width and 0 <= y+dy < self.height
                         and self.grid[y+dy][x+dx] == "." and (x+dx, y+dy) != prev]

            # pokud není žádný soused, konec koridoru
            if not neighbors:
                break

            # pokud je více než 1 soused (větvení), bereme poslední políčko před větvením
            if len(neighbors) > 1:
                break

            # posuneme se
            prev, x, y = x, neighbors[0][0], neighbors[0][1]
            last_valid = (x, y)

        # pokud jsme našli validní pozici, umístíme strážce
        if last_valid:
            self.place_enemy(*last_valid)
        else:
            # fallback: pokud žádný koridor, umístíme guard vedle truhly
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = chest_x + dx, chest_y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and self.grid[ny][nx] == ".":
                    self.place_enemy(nx, ny)
                    break

    def place_door_guards(self, door_x, door_y, total_guards=3, min_separation=2):
        # 1) BFS z dveří, uložíme vzdálenost a předchůdce pro trasu
        distances = [[None for _ in range(self.width)]
                     for _ in range(self.height)]
        predecessors = [[None for _ in range(self.width)]
                        for _ in range(self.height)]
        distances[door_y][door_x] = 0
        queue = deque([(door_x, door_y)])

        while queue:
            x, y = queue.popleft()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.grid[ny][nx] == "." and distances[ny][nx] is None:
                        distances[ny][nx] = distances[y][x] + 1
                        predecessors[ny][nx] = (x, y)
                        queue.append((nx, ny))

        # 2) Vybereme všechny "cesty" z koridorů k dveřím
        corridor_positions = []
        for y in range(self.height):
            for x in range(self.width):
                if distances[y][x] is not None and distances[y][x] > 0:
                    # Kontrola, že má alespoň dva průchozí sousedy (není roh)
                    neighbors = sum(1 for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                                    if 0 <= x+dx < self.width and 0 <= y+dy < self.height and self.grid[y+dy][x+dx] == ".")
                    if neighbors <= 2:  # typický koridor
                        corridor_positions.append((x, y, distances[y][x]))

        if not corridor_positions:
            return  # žádný koridor

        # 3) Seřadíme podle vzdálenosti od dveří (blíže první)
        corridor_positions.sort(key=lambda pos: pos[2])

        # 4) Umístění nepřátel s rozestupy
        placed = []
        for x, y, dist in corridor_positions:
            too_close = False
            for px, py in placed:
                if abs(px - x) + abs(py - y) < min_separation:
                    too_close = True
                    break
            if not too_close:
                self.place_enemy(x, y)
                placed.append((x, y))
                if len(placed) >= total_guards:
                    break

        # 5) Pokud se nepodařilo umístit všechny s min_separation, doplníme náhodně
        if len(placed) < total_guards:
            remaining = total_guards - len(placed)
            candidates = [pos for pos in corridor_positions if (
                pos[0], pos[1]) not in placed]
            random.shuffle(candidates)
            for x, y, _ in candidates[:remaining]:
                self.place_enemy(x, y)
                placed.append((x, y))

    def is_corridor_tile(self, x, y):
        if self.grid[y][x] != ".":
            return False

        up = (y > 0 and self.grid[y-1][x] == ".")
        down = (y < self.height-1 and self.grid[y+1][x] == ".")
        left = (x > 0 and self.grid[y][x-1] == ".")
        right = (x < self.width-1 and self.grid[y][x+1] == ".")

        vertical = up and down and not left and not right
        horizontal = left and right and not up and not down

        return vertical or horizontal

    def generate_enemies_in_corridors(self, count, player_x, player_y):
        corridor_tiles = []

        for y in range(self.height):
            for x in range(self.width):
                if (x, y) != (player_x, player_y) and self.is_corridor_tile(x, y):
                    corridor_tiles.append((x, y))

        for _ in range(count):
            if not corridor_tiles:
                break
            x, y = random.choice(corridor_tiles)
            self.place_enemy(x, y)
            corridor_tiles.remove((x, y))

    def get_boss_room_center(self):
        if not self.boss_rooms:
            raise ValueError("Boss room nebyla vytvořena")
        boss_room = self.boss_rooms[0]
        cx, cy = boss_room.center()
        return cx, cy

    def create_boss_room(self, rooms, start_x, start_y):
        connected_rooms = [r for r in rooms if any(self.grid[y][x] == '.'
                                                   for x in range(r.x1, r.x2+1)
                                                   for y in range(r.y1, r.y2+1))]
        if not connected_rooms:
            connected_rooms = rooms

        boss_room = max(connected_rooms, key=lambda r: abs(
            r.center()[0]-start_x) + abs(r.center()[1]-start_y))

        min_width, min_height = 5, 5
        if boss_room.width < min_width:
            boss_room.x2 = min(boss_room.x1 + min_width - 1, self.width - 1)
        if boss_room.height < min_height:
            boss_room.y2 = min(boss_room.y1 + min_height - 1, self.height - 1)

        possible_tiles = [
            (x, y)
            for x in range(boss_room.x1, boss_room.x2 + 1)
            for y in range(boss_room.y1, boss_room.y2 + 1)
            if 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] == '.'
        ]

        if possible_tiles:
            # dveře
            boss_room.door = random.choice(possible_tiles)
            dx, dy = boss_room.door
            self.grid[dy][dx] = 'X'

            # boss
            boss_tiles = [
                tile for tile in possible_tiles if tile != boss_room.door]
            if boss_tiles:
                bx, by = random.choice(boss_tiles)
                self.grid[by][bx] = 'B'
                boss_room.boss_pos = (bx, by)

        self.boss_rooms.append(boss_room)
        return boss_room

    def place_boss_door(self, boss_room):
        cx, cy = boss_room.center()
        for dx, dy in [(0, -1), (-1, 0), (1, 0), (0, 1)]:
            door_x, door_y = cx + dx, cy + dy
            if 0 <= door_x < self.width and 0 <= door_y < self.height:
                if self.grid[door_y][door_x] == ".":
                    self.grid[door_y][door_x] = "X"
                    return (door_x, door_y)
        self.grid[cy][cx - 1] = "X"
        return (cx - 1, cy)

    def update_visibility(game_map, px, py, radius=2):
        for y in range(game_map.height):
            for x in range(game_map.width):

                if math.sqrt((x - px)**2 + (y - py)**2) <= radius:
                    game_map.visible[y][x] = True
                    game_map.explored[y][x] = True
                else:
                    game_map.visible[y][x] = False

    def draw_map(game_map, px, py):
        lines = []

        for y in range(game_map.height):
            row = ""

            for x in range(game_map.width):
                char = game_map.grid[y][x]

                if x == px and y == py:
                    row += "\033[93mP\033[0m "
                elif not game_map.explored[y][x]:
                    row += "? "
                elif not game_map.visible[y][x]:
                    row += f"\033[90m{char}\033[0m "
                else:
                    if char == "#":
                        row += "\033[92m#\033[0m "
                    elif char == "E":
                        row += "\033[91mE\033[0m "
                    elif char == "^":
                        row += "\033[38;5;208m^\033[0m "
                    elif char == "▣":
                        row += "\033[38;5;94m▣\033[0m "
                    elif char == "▮":
                        row += "▮ "
                    elif char == "B":
                        row += "\033[91mB\033[0m "
                    elif char == "X":
                        row += "\033[38;5;94mX\033[0m "
                    else:
                        row += ". "

            lines.append(row.rstrip())

        map_text = "\n".join(lines)
        core.print_center_block(map_text)

    def next_level(player):
        save_game(player)
        global game_map, player_x, player_y

        player.dungeon_level += 1
        is_boss_level = player.dungeon_level % 5 == 0

        game_map = GameMap(24, 20)
        rooms = game_map.generate_dungeon()

        player_x, player_y = rooms[0].center()

        if is_boss_level:
            boss_room = game_map.create_boss_room(rooms, player_x, player_y)
            # spawn boss a jen boss dveře, žádné normální
            game_map.generate_objects(
                bonefire_count=1,
                chest_count=1,
                player_x=player_x,
                player_y=player_y,
                door_count=0,
                boss_room=boss_room
            )
            game_map.generate_enemies_in_corridors(
                count=2 + player.dungeon_level,
                player_x=player_x,
                player_y=player_y
            )
        else:
            game_map.generate_objects(
                bonefire_count=2,
                chest_count=2,
                player_x=player_x,
                player_y=player_y,
                door_count=1
            )
            game_map.generate_enemies_in_corridors(
                count=2 + player.dungeon_level,
                player_x=player_x,
                player_y=player_y
            )

    @staticmethod
    def handle_tile(game_map, x, y, player, combat_function):
        messages = []
        status = None  # defaultně žádný stav

        tile = game_map.grid[y][x]

        if tile == "E":
            enemies = monsters.create_enemy_group(player.dungeon_level)
            survived = combat_function(player, enemies)

            if survived:
                game_map.grid[y][x] = "."
                status = "enemy_dead"
            else:
                status = "player_dead"

        elif tile == "B":
            if not hasattr(game_map, "boss_spawned"):
                boss = monsters.create_boss_group(player.dungeon_level)
                cx, cy = x, y
                game_map.boss_spawned = True
            else:
                boss = next(
                    (e[2] for e in game_map.enemies if e[0] == x and e[1] == y), None)

            survived = combat_function(player, boss)

            if survived:
                game_map.enemies = [
                    e for e in game_map.enemies if e[2] != boss]
                game_map.grid[y][x] = "."
                status = "enemy_dead"
            else:
                status = "player_dead"

        elif tile == "^":
            heal_amount = 5
            player.hp = min(player.max_hp, player.hp + heal_amount)
            messages.append(
                f"Ohniště: odpočinul sis u ohniště a doplnil {heal_amount} HP (HP: {player.hp}/{player.max_hp})")
            game_map.grid[y][x] = "."

        elif tile == "▣":
            UNIVERSAL_LOOT = [
                gear.ring_of_defense, gear.wurm_ring,
                gear.rabits_paw, gear.abakus, gear.madmans_eye,
                gear.poisoners_ring, gear.ring_with_needle,
                gear.caltrops, gear.dagger

            ]

            CLASS_LOOT = {
                "vojak": [
                    gear.shield_with_spike, gear.flail, gear.war_paints,
                    gear.battle_axe, gear.battle_plans, gear.mace
                ],
                "kultistka": [
                    gear.bloodthirsty_tongue, gear.blade_of_blood_frenzy, gear.blood_vial,
                    gear.serpent_spear, gear.ritual_sickle, gear.claw_dagger, gear.sacrificial_blade,
                    gear.sacrificial_bone, gear.forbidden_texts
                ],
                "mag": [
                ]
            }

            player_pool = CLASS_LOOT.get(player.player_class, [])
            combined_pool = player_pool + UNIVERSAL_LOOT

            loot = random.choice(combined_pool)
            player.inventory.append(loot)
            messages.append(f"Otevřel jsi truhlu a našel: {loot.name}")
            game_map.grid[y][x] = "."

        if tile == "▮":
            messages.append("Vstupuješ do dalšího patra!")
            GameMap.next_level(player)

        elif tile == "X":
            boss_alive = any("B" in row for row in game_map.grid)

            if boss_alive:
                messages.append(
                    "Toto jsou zamčené dveře a zatím od nich nemáš klíč!")
            else:
                messages.append(
                    "Otevíráš dveře a před tebou se otvírá nová krajina...")
                game_map.grid[y][x] = "."  # dveře odemknuté
                GameMap.next_level(player)

        return status, messages


def show_help():
    clear_screen()

    lines = []

    # ===== NADPIS =====
    lines.append("\033[96m=== PŘÍRUČKA HRY ===\033[0m")
    lines.append("")

    # ===== OVLÁDÁNÍ =====
    lines.append("\033[93mOvládání:\033[0m")
    lines.append("WASD - pohyb po mapě")
    lines.append("Q - ukončit hru")
    lines.append("I - otevřít inventář")
    lines.append("H - zobrazit tuto příručku")
    lines.append("V boji vyber číslo karty nebo ENTER pro konec tahu")
    lines.append("")

    # ===== MAPA =====
    lines.append("\033[93mMapa a ikony:\033[0m")
    lines.append("- # - stěna")
    lines.append("- . - průchozí dlaždice / chodba")
    lines.append("- P - tvoje pozice")
    lines.append("- E - nepřítel")
    lines.append("- ^ - ohniště, doplní část zdraví")
    lines.append("- ▣ - truhla s lootem")
    lines.append("- ▮ - dveře do dalšího patra")
    lines.append("Vstup na pole s ním automaticky interaguje!")
    lines.append("")

    # ===== INVENTÁŘ =====
    lines.append("\033[93mInventář:\033[0m")
    lines.append(
        "V inventáři najdeš své vybavení a karty, které ti poskytuje.")
    lines.append("Každé vybavení může obsahovat jednu nebo více karet.")
    lines.append(
        "Pokud máš aktivní synergie mezi vybavením, zobrazí se zvlášť modře.")
    lines.append("Použití inventáře:")
    lines.append("- Můžeš si zde prohlédnout aktuální deck")
    lines.append("- Můžeš se podívat co jednotlivé vybavená umí")
    lines.append("- Můžeš měnit své aktuálně používané vybavení")
    lines.append("- Můžeš si zde spravovat své naučené schopnosti")
    lines.append("")

    # ===== SOUBOJ =====
    lines.append("\033[93mSouboj:\033[0m")
    lines.append("- V souboji hraješ se svým balíčkem, který obsahuje karty,")
    lines.append("dané tvým akutálním vybavením a aktivními schopnostmi.")
    lines.append(
        "- Po vyčerpání energie je tah předán nepříteli, který také má svůj balíček.")
    lines.append("- Boj pokračuje dokud jedna ze stran není úplně poražena")
    lines.append(
        "- Každá zahrátá karta je odložena na odhazovací balíček, který je domíchán, jakmile")
    lines.append("dobereš svůj balíček.")
    lines.append(
        "- Kdykoliv zamícháš v boji odhazovací balíček, je v rámci souboje tvojí postavě přidána únava.")
    lines.append(
        "Při každém zamíchání tvoje postavautrpí zranění ve výši tvé únavy.")
    lines.append("")

    # ===== LEVLY =====
    lines.append("\033[93mLevly:\033[0m")
    lines.append("- Za porážení nepřátel dostáváš zkušenosti")
    lines.append(
        "- Při postupu na novou úroveň se zvýší tvé dosavadní maximální zdraví a")
    lines.append(
        "máš možnost si vybrat jednu ze tří schopností, která se ti odemkne.")
    lines.append("")

    # ===== TYPY KARET =====
    lines.append("\033[93mTypy karet:\033[0m")
    lines.append("- Útočné (DMG) - způsobují poškození nepříteli")
    lines.append("- Obranné (BLOCK) - přidávají obranu na tento tah")
    lines.append(
        "- Efekty (EFFECT) - aplikují stavové efekty jako Omráčení, Úhyb, Otrava")
    lines.append(
        "- Speciální - např. DRAW (táhni karty), DISCARD (zahoď karty)")
    lines.append("")

    # ===== EFEKTY =====
    lines.append("\033[93mEfekty:\033[0m")
    lines.append("- Omráčení (Stun) - jednotka vynechá tah")
    lines.append("- Úhyb (Dodge) - šance vyhnout se útoku")
    lines.append("- Otrava (Poison) - poškození v průběhu několika kol")
    lines.append(
        "- Trny - útok na toho, kdo má tento efekt, útočníkovi způsobí zranění")
    lines.append("")

    # ===== SYNERGIE =====
    lines.append("\033[93mSynergie:\033[0m")
    lines.append(
        "- Když používáš určité kombinace vybavení, získáš bonusové karty")
    lines.append("- Např. 'Krátký Meč + Štít' = karta 'Útok a kryt'")
    lines.append("")

    # ===== CÍL =====
    lines.append("\033[93mCíl hry:\033[0m")
    lines.append("- Zlepšuj svůj deck s pomocí silnějšího vybavení")
    lines.append("- Hledej vstupy do dalších částí mapy a levlů")
    lines.append("")

    # ===== TIPY =====
    lines.append("\033[93mTipy:\033[0m")
    lines.append("- Chytře využívej svou energii na daný tah")
    lines.append("- Kombinuj vybavení pro odalování sinergií")
    lines.append(
        "- Studuj nepřátele, každý má svůj vlastní balíček karet a ti silnější dokonce i strategie")
    lines.append("")

    lines.append("Stiskni ENTER pro návrat do hry...")

    render(lines)
    input()


def show_bestiary(player):
    while True:
        clear_screen()
        core.print_center_block("\n=== BESTIÁŘ ===\n")

        enemies = list(player.bestiary.keys())

        for i, name in enumerate(enemies):
            kills = player.bestiary[name]["kills"]
            core.print_center_block(f"{i+1}. {name} (Zabit: {kills}x)")

        core.print_center_block("\n(Vyber nepřítele = 1-X, q = zpět): ")
        choice = input("\n> ")

        if choice == "q":
            return

        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(enemies):
                show_enemy_detail(player, enemies[index])
        core.print_center_block()


def show_enemy_detail(player, enemy_name):
    clear_screen()
    data = player.bestiary[enemy_name]

    kills = data['kills']
    info = data['info']

    core.print_center_block(f"\n=== {enemy_name} ===")
    core.print_center_block(f"Zabit: {kills}x\n")

    all_cards = data.get("all_cards", [])
    seen_cards = data["seen_cards"]

    if kills >= 1:
        core.print_center_block(f"Karty ({len(seen_cards)}/{len(all_cards)}):")
        for card in all_cards:
            if card in seen_cards:
                core.print_center_block(f" - {card}")
            else:
                core.print_center_block(" - ???")
    else:
        core.print_center_block("\n???")

    if kills >= 1:
        print_section("Popis", info.get('description', '???'))

    if kills >= 3:
        print_section("Lore", info.get('lore', '???'))
    else:
        text = "??? (zabij více nepřátel)"
        core.print_center_block("\n" + "LORE".center(60))
        core.print_center_block("-" * 60)
        core.print_center_block(text.center(60))

    if kills >= 6:
        print_section("Extra lore", info.get('extra_lore', '???'))
    else:
        text = "??? (zabij více nepřátel)"
        core.print_center_block("\n" + "EXTRA LORE".center(60))
        core.print_center_block("-" * 60)
        core.print_center_block(text.center(60))

    input("\nENTER pro návrat...")


def show_inventory(player):

    padding = None

    def render(lines, use_existing_padding=False):
        nonlocal padding
        if use_existing_padding and padding is not None:
            core.render_block(lines, forced_padding=padding)
        else:
            padding = core.render_block(lines)

    while True:
        clear_screen()

        lines = []

        # ===== INVENTÁŘ =====
        core.print_center_block("=== INVENTÁŘ ===")
        lines.append("")
        lines.append("Vybavené:")

        for slot, items in player.slots.items():
            for i, item in enumerate(items):
                name = item.name if item else "\033[90mPrázdné\033[0m"
                lines.append(f"{slot} [{i}]: {name}")
            lines.append("")

        lines.append("Batoh:")
        if not player.inventory:
            lines.append("Prázdný")
        else:
            for i, eq in enumerate(player.inventory):
                lines.append(f"{i}: {eq.name} ({eq.slot_type})")

        lines.append("")
        lines.append("1: Detail itemu")
        lines.append("2: Vybavit")
        lines.append("3: Sundat")
        lines.append("4: Prohlédnout deck")
        lines.append("5: Prohlédnout schopnosti")
        lines.append("6: Konec")

        render(lines)

        choice = input("> ")

        # ===== DETAIL ITEMU =====
        if choice == "1":
            if not player.inventory:
                render(["Batoh je prázdný!", "", "ENTER pro pokračování..."])
                input()
                continue

            idx = get_valid_index(
                "Index itemu z batohu: ", len(player.inventory))
            eq = player.inventory[idx]

            lines = [f"--- {eq.name} ---"]
            lines = [f"--- {eq.name} ---", ""]
            lines.extend(core.get_card_lines(eq.cards))

            render(lines, use_existing_padding=True)
            input("ENTER pro pokračování...")

        # ===== VYBAVIT =====
        elif choice == "2":
            if not player.inventory:
                render(["Batoh je prázdný!", "", "ENTER pro pokračování..."])
                input()
                continue

            idx = get_valid_index(
                "Index itemu z batohu: ", len(player.inventory))
            player.equip_item(player.inventory[idx])
            player.build_deck()

        # ===== SUNDAT =====
        elif choice == "3":
            slot = input("Slot (hand/body/belt/pocket/ring): ")

            if slot not in player.slots:
                render(["Neplatný slot!", "", "ENTER pro pokračování..."])
                input()
                continue

            lines = [f"{slot} obsah:"]
            for i, item in enumerate(player.slots[slot]):
                name = item.name if item else "Prázdné"
                lines.append(f"[{i}]: {name}")

            if all(item is None for item in player.slots[slot]):
                lines.append("")
                lines.append("Slot je prázdný!")
                render(lines + ["", "ENTER pro pokračování..."])
                input()
                continue

            render(lines)

            idx = get_valid_index(
                "Index slotu k odbavení: ", len(player.slots[slot]))
            player.unequip_item(slot, idx)
            player.build_deck()

        # ===== DECK =====
        elif choice == "4":
            clear_screen()
            player.build_deck()

            core.print_center_block("=== Aktuální deck ===")
            lines = []

            deck_exists = False
            active_synergies = []

            added_items = set()

            for slot, items in player.slots.items():
                for eq in items:
                    if not eq:
                        continue

                    if eq.two_handed:
                        if id(eq) in added_items:
                            continue
                        added_items.add(id(eq))

                    deck_exists = True
                    lines.append(f"--- {eq.name} ---")


                    lines.extend(core.get_card_lines(eq.cards))
                    lines.append("")

            equipment_names = [
                item.name for slot in player.slots.values()
                for item in slot if item
            ]

            for synergy in core.SYNERGIES:
                if all(req in equipment_names for req in synergy["requires"]):
                    active_synergies.append(synergy)

            for synergy in active_synergies:
                lines.append(
                    f"\033[94m--- Aktivní synergie: {', '.join(synergy['requires'])} ---\033[0m"
                )
                lines.extend(core.get_card_lines(synergy["cards"]))
                lines.append("")
                deck_exists = True

            active_card_abilities = [
                ab for ab in player.abilities
                if getattr(ab, "active", True) and getattr(ab, "type", None) == "card"
            ]

            if active_card_abilities:
                lines.append("\033[96m--- Karty schopností ---\033[0m")

                for ability in active_card_abilities:
                    lines.append(f"{ability.name}: {ability.description}")
                    lines.extend(core.get_card_lines(ability.cards))
                    lines.append("")
                    deck_exists = True

            if not deck_exists:
                lines.append("Deck je prázdný!")

            render(lines)

            input("\nENTER pro návrat do inventáře...")

        # ===== SCHOPNOSTI =====
        elif choice == "5":
            while True:
                clear_screen()
                
                core.print_center_block("=== SCHOPNOSTI ===")
                lines = []

                if not player.abilities:
                    lines.append("Zatím nemáš žádné schopnosti.")
                    render(lines + ["", "ENTER pro návrat..."])
                    input()
                    break

                for i, ability in enumerate(player.abilities):
                    status = "Aktivní" if getattr(
                        ability, "active", True) else "Neaktivní"
                    lines.append(
                        f"{i}: {ability.name} ({status}) - {ability.description}")
                    if getattr(ability, "type", None) == "card":
                        for card_line in core.get_card_lines(ability.cards):
                            lines.append("   " + card_line)

                lines.append("")
                lines.append("1: Přepnout aktivitu schopnosti")
                lines.append("2: Konec")

                render(lines)

                choice = input("> ")

                if choice == "1":
                    idx = get_valid_index(
                        "Index schopnosti: ", len(player.abilities))
                    ability = player.abilities[idx]
                    ability.active = not getattr(ability, "active", True)

                    status = "aktivní" if ability.active else "neaktivní"
                    render(
                        [f"{ability.name} je nyní {status}.", "", "ENTER..."])
                    input()

                elif choice == "2":
                    break

        # ===== KONEC =====
        elif choice == "6":
            break

        else:
            render(["Neplatná volba!", "", "ENTER pro pokračování..."])
            input()


def get_random_abilities(all_abilities, count=3):
    return random.sample(all_abilities, count)


def level_up(self):
    self.max_hp += 5
    self.hp += 5
    self.lvl += 1

    all_abilities = [
        abilities.pain_for_all,
        abilities.power_strike,
        abilities.fast_strike,
        abilities.defensive_strike,
        abilities.no_rest,
        abilities.muscles,
        abilities.hard_root,
        abilities.three_attack_draw,
        abilities.maintaining_defense
    ]

    owned_abilities = {ability.name for ability in self.abilities}

    available_abilities = [
        ability for ability in all_abilities
        if ability.name not in owned_abilities
    ]

    choices = get_random_abilities(available_abilities, 3)

    while True:
        clear_screen()

        # ======================
        # UI BUILD (LINES)
        # ======================
        lines = []

        lines.append("\033[94m=== DOSÁHL JSI NOVÉ ÚROVNĚ! ===\033[0m")
        lines.append("")
        lines.append("Tvé maximální zdraví se zvýšilo o 5.")
        lines.append("")
        lines.append("Vyber si jednu schopnost:")
        lines.append("")

        for i, ability in enumerate(choices, 1):
            lines.append(f"\033[96m{i}) {ability.name} - {ability.description}\033[0m")

            if getattr(ability, "type", None) == "card":
                for card_line in core.get_card_lines(ability.cards):
                    lines.append("   " + card_line)

            lines.append("")

        # ======================
        # RENDER
        # ======================
        core.render_block(lines, forced_padding=None)

        # ======================
        # INPUT
        # ======================
        choice = input("\nTvoje volba: ")

        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(choices):
                selected = choices[choice - 1]
                selected.apply(self)

                core.print_center_block(f"\nZískal jsi: {selected.name}")
                input("Pokračuj...")
                break

def get_valid_index(prompt, max_value):
    while True:
        choice = input(prompt)

        if not choice.isdigit():
            core.print_center_block("Zadej číslo!")
            continue

        idx = int(choice)

        if 0 <= idx < max_value:
            return idx
        else:
            core.print_center_block("Index mimo rozsah!")


def move_player(cmd, x, y, game_map):
    new_x, new_y = x, y

    if cmd == "w" and y > 0:
        new_y -= 1
    elif cmd == "s" and y < game_map.height - 1:
        new_y += 1
    elif cmd == "a" and x > 0:
        new_x -= 1
    elif cmd == "d" and x < game_map.width - 1:
        new_x += 1

    # kontrola průchodnosti
    if game_map.grid[new_y][new_x] == "#":
        core.print_center_block("Nemůžeš jít do zdi!")
        input("ENTER pro pokračování...")
        return x, y  # zůstane na původním poli
    else:
        return new_x, new_y


class RectRoom:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        cx = (self.x1 + self.x2) // 2
        cy = (self.y1 + self.y2) // 2
        return cx, cy

    def intersects(self, other):
        return (
            self.x1 <= other.x2 and self.x2 >= other.x1 and
            self.y1 <= other.y2 and self.y2 >= other.y1
        )

    @property
    def width(self):
        return self.x2 - self.x1 + 1

    @property
    def height(self):
        return self.y2 - self.y1 + 1


def choose_enemy(enemies):
    alive = []
    for e in enemies:
        if e.hp > 0:
            alive.append(e)

    if len(alive) == 1:
        return alive[0]

    for i, e in enumerate(alive):
        core.print_center_block(f"{i}: {e.name} (HP: {e.hp})")

    while True:
        choice = input("Vyber nepřítele: ")

        if not choice.isdigit():
            core.print_center_block("Neplatná volba")
            continue

        index = int(choice)

        if 0 <= index < len(alive):
            return alive[index]


def combat(player, enemies):

    padding = None 

    def render(lines, use_existing_padding=False):
        nonlocal padding

        if use_existing_padding and padding is not None:
            core.render_block(lines, forced_padding=padding)
        else:
            padding = core.get_padding(lines)
            core.render_block(lines, padding)

    player.reset_combat()
    for enemy in enemies:
        enemy.reset_combat()

    player.build_deck()
    for enemy in enemies:
        enemy.build_deck()

    first_turn = True

    global combat_xp
    combat_xp = 1 + player.dungeon_level

    while player.hp > 0 and any(e.hp > 0 for e in enemies):

        # ===== BESTIÁŘ =====
        for enemy in enemies:
            if enemy.name not in player.bestiary:
                player.bestiary[enemy.name] = {
                    "seen": True,
                    "kills": 0,
                    "seen_cards": set(),
                    "all_cards": enemy.all_cards,
                    "info": {
                        "description": enemy.description,
                        "lore": enemy.lore,
                        "extra_lore": enemy.extra_lore
                    }
                }

        clear_screen()

        # =======================
        # START KOLA UI
        # =======================
        lines = []

        core.print_center_block("--- Nové kolo ---")
        core.print_center_block("\n")

        player.block = 0
        player.combo_count = 0

        for ability in player.abilities:
            if ability.type == "passive" and ability.trigger == "per_turn" and ability.active:
                ability.effect(player)

        player.block += player.saved_block
        player.saved_block = 0

        # ===== PLAYER STATUS =====
        p_line = f"- {player.name} (HP: {player.hp}, Block: {player.block}, Energy: {player.energy}"

        total_str = player.strenght + player.temporary_strenght
        if total_str != 0:
            p_line += f", Total_strenght: {total_str}"

        if player.combo_count:
            p_line += f", Combo: {player.combo_count}"

        p_line += f"){core.format_status_effects(player)}"

        lines.append(p_line)
        lines.append("")
        lines.append("Nepřátelé:")

        # ===== ENEMIES STATUS =====
        for e in enemies:
            if e.hp > 0:
                e_line = f"- {e.name} (HP: {e.hp}, Block: {e.block}"

                total_str = e.strenght + e.temporary_strenght
                if total_str != 0:
                    e_line += f", Total_strenght: {total_str}"

                e_line += f"){core.format_status_effects(e)}"
                lines.append(e_line)

        render(lines)

        # =======================
        # PLAYER TURN
        # =======================
        if player.is_stunned():
            render([f"{player.name} vynechává tah kvůli omráčení!"], use_existing_padding=True)
            input("ENTER...")
            msgs = player.process_status()
            if msgs:
                render(msgs, use_existing_padding=True)
                input("ENTER...")
            continue

        msgs = player.process_status()
        if msgs:
            render(msgs, use_existing_padding=True)
            input("ENTER...")

        if player.hp <= 0:
            render(["Prohrál jsi!"], use_existing_padding=True)
            input("ENTER...")
            return False

        if first_turn:
            msgs = player.draw(3)

            if msgs:
                render(msgs, use_existing_padding=True)
                input("ENTER...")

            result = check_combat_end(player, enemies, render)
            if result is not None:
                return result
            
            render([f"Narazil jsi na {len(enemies)} nepřátel"], use_existing_padding=True)
            first_turn = False
        else:
            msgs= player.draw(2 + player.extra_draw)

            if msgs:
                render(msgs, use_existing_padding=True)
                input("ENTER...")
            
            result = check_combat_end(player, enemies, render)
            if result is not None:
                return result

        character.Character.player_turn(player, enemies)

        # =======================
        # CHECK BOSS / WIN
        # =======================
        result = check_combat_end(player, enemies, render)
        if result is not None:
            return result

        # =======================
        # ENEMY TURN HEADER
        # =======================
        clear_screen()
        core.print_center_block(
            f"{core.Colors.RED}--- Nepřátelský tah ---{core.Colors.RESET}")
        core.print_center_block("\n")

        # ===== ENEMY STATUS =====
        lines = [
            p_line,
            "",
            "Nepřátelé:"
        ]

        for e in enemies:
            if e.hp > 0:
                e_line = f"- {e.name} (HP: {e.hp}, Block: {e.block}"
                total_str = e.strenght + e.temporary_strenght
                if total_str != 0:
                    e_line += f", Total_strenght: {total_str}"
                e_line += f"){core.format_status_effects(e)}"
                lines.append(e_line)

        lines.append("")
        lines.append("Tvoje karty:")
        lines.extend(player.get_hand_lines())

        render(lines, use_existing_padding=True)

        # =======================
        # ENEMY ACTIONS
        # =======================
        for enemy in enemies:
            for ability in enemy.abilities:
                if ability.type == "passive" and ability.trigger == "after_opponent_turn" and ability.active:
                    ability.effect(enemy)

        render([""], use_existing_padding=True)
        render(["--- Nepřátelé hrají ---"], use_existing_padding=True)

        for enemy in enemies:
            enemy.block = 0

        for enemy in enemies:
            enemy.block += enemy.saved_block
            enemy.saved_block = 0

        for enemy in enemies[:]:
            if enemy.hp <= 0:
                continue

            if enemy.is_stunned():
                render([f"{enemy.name} je omráčen!"], use_existing_padding=True)
                msgs = enemy.process_status()
                if msgs:
                    render(msgs, use_existing_padding=True)
                continue

            msgs = enemy.process_status()
            if msgs:
                render(msgs, use_existing_padding=True)

            if enemy.hp <= 0:
                continue

            if enemy.ai:
                enemy.ai(enemy, player, enemies)
            else:
                enemy.draw(enemy.actions)

                for _ in range(enemy.actions):
                    if not enemy.hand:
                        break

                    index = random.randint(0, len(enemy.hand) - 1)
                    card = enemy.hand[index]

                    if card.target_type == "self":
                        target = enemy
                    elif card.target_type == "ally":
                        allies = [e for e in enemies if e.hp >
                                  0 and e != enemy]
                        target = random.choice(allies) if allies else enemy
                    else:
                        target = player

                    enemy.play_card(
                        index,
                        target=target,
                        enemies_list=enemies,
                        create_enemy_func=monsters.create_enemy_by_name,
                        player=player
                    )

        result = check_combat_end(player, enemies, render)
        if result is not None:
            return result

        input("Stiskni cokoliv pro další kolo:")

def check_combat_end(player, enemies, render):
    boss = next((e for e in enemies if e.is_boss), None)

    if player.hp <= 0:
        render(["Prohrál jsi!"], use_existing_padding=True)
        input("ENTER...")
        return False

    if boss:
        if boss.hp <= 0:
            render(["Porazil jsi bosse!"], use_existing_padding=True)
            input("ENTER...")
            for enemy in enemies:
                        if enemy.name in player.bestiary and enemy.hp <= 0:
                            player.bestiary[enemy.name]["kills"] += 1
            return True
    else:
        if all(e.hp <= 0 for e in enemies):
            render(["Vyhrál jsi!"], use_existing_padding=True)
            input("ENTER...")
            for enemy in enemies:
                        if enemy.name in player.bestiary and enemy.hp <= 0:
                            player.bestiary[enemy.name]["kills"] += 1
            return True

    return None


def select_starting_build(player):
    while True:
        clear_screen()
        core.print_center_block(
            "\n\033[94m=== VYBER POSTAVU ZA KTEROU CHCEŠ HRÁT: ===\033[0m")
        core.print_center_block("1) Voják")
        core.print_center_block("2) Kultista")
        core.print_center_block("3) Mág (Připravuje se)")

        choice = input("> ")

        if choice == "1":
            clear_screen()

            core.print_box(
                "VOJÁK",
                [
                    "HP: 20",
                    "Energie: 2",
                    "Styl: Silné útoky a blokování poškození",
                    "Startovní vybavení: Krátký meč, Štít, Vycpávaná zbroj"
                ],
                "Účastnící se dlouhé a vyčerpávající války daleko od domova už ani "
                "nevěřil, že se do něj někdy vrátí. Boje však vyčerpaly zdroje obou "
                "válčících stran, morálka se zhoršovala a nakonec už ani nebyl nikdo, "
                "kdo by udával rozkazy. Voják se jako mnoho ostatních rozhodl opustit "
                "to strašlivé místo a vrátit se domů. Ten však zdaleka nebyl takový, "
                "jak si jej pamatoval."
            )

            confirm = input("\nVybrat tuto postavu? (y/n): ")
            if confirm.lower() == "y":
                player.max_hp = 20
                player.hp = 20
                player.max_energy = 2
                player.energy = player.max_energy
                player.extra_draw = 0
                player.equip_item(gear.sword)
                player.equip_item(gear.shield)
                player.equip_item(gear.padded_armor)
                # player.equip_item(gear.battle_axe)
                # player.equip_item(gear.war_paints)
                # player.equip_item(gear.ring_of_defense)
                # player.equip_item(gear.wurm_ring)
                player.player_class = "vojak"
                return

        elif choice == "2":
            clear_screen()

            core.print_box(
                "KULTISTKA",
                [
                    "HP: 16",
                    "Energie: 3",
                    "Styl: Combo, agresivní scaling",
                    "Startovní vybavení: Kultistická čepel, Rituální soška, Rituální suknice"
                ],
                "Kultistka zasvětila svůj život temným silám, které jí na oplátku "
                "propůjčily zvláštní schopnosti. Každý útok a rituál ji "
                "posouvá blíže k moci, ale zároveň dál od lidskosti. V ruinách "
                "starého světa hledá další oběti i tajemství, která by mohla "
                "využít ve svůj prospěch."
            )

            confirm = input("\nVybrat tuto postavu? (y/n): ")
            if confirm.lower() == "y":
                player.max_hp = 16
                player.hp = 16
                player.max_energy = 3
                player.energy = player.max_energy
                player.extra_draw = 0
                player.equip_item(gear.cultistic_blade)
                player.equip_item(gear.ritual_statue)
                player.equip_item(gear.ritual_skirt)
                player.player_class = "kultistka"
                return

        elif choice == "3":
            clear_screen()

            core.print_box(
                "MÁG",
                [
                    "HP: 14",
                    "Energie: 2",
                    "Styl: Ability, manipulace balíčku",
                    "Startovní vybavení: Dřevěná hůl, Stará róba, Bezejmená kniha",
                    "Startovní bonus: +1 draw"
                ],
                "Mágovo jméno bylo kdysi velectěné. Po událostech, na které si však nedokáže vzpomenout, "
                "byl vyhnán z komnat své věže a zatracen. Nyní bloudí rozpadajícím se světem, "
                "pátrá po zapomenutém vědění a střípcích své minulosti – v naději, že obnoví svou mysl "
                "a získá zpět vše, co ztratil."
            )

            confirm = input("\nVybrat tuto postavu? (y/n): ")
            if confirm.lower() == "y":
                player.max_hp = 14
                player.hp = 14
                player.max_energy = 2
                player.energy = player.max_energy
                player.extra_draw = 1
                player.equip_item(gear.wooden_staff)
                player.equip_item(gear.an_untitled_book)
                player.equip_item(gear.old_robe)
                player.player_class = "mag"
                #player.equip_item(gear.test_kill)

                return

        else:
            core.print_center_block("Neplatná volba.")


# ===== MAIN LOOP ========
DEBUG_BOSS_FIGHT = False

clear_screen()
core.print_center_block("=== DUNGEON CRAWLER ===")
core.print_center_block("")
core.print_center_block("1) Nová hra")
core.print_center_block("2) Načíst hru")
core.print_center_block("")

choice = input("> ")

if choice == "2":
    player = load_game("save.json")

    if player is None:
        core.print_center_block("Save nenalezen, startuji novou hru...")
        input("ENTER...")
        player = character.Character("Hráč", 20)
        select_starting_build(player)
        player.is_player = True
        player.abilities = []
        player.dungeon_level = 1
        player.xp = 0
        player.lvl = 1
    else:
        core.print_center_block("Hra načtena!")
        input("ENTER...")

else:
    player = character.Character("Hráč", 20)
    select_starting_build(player)
    player.is_player = True
    player.abilities = []
    player.dungeon_level = 0
    player.xp = 0
    player.lvl = 1

player.fatigue = 0
player.reduced_energy = 0
player.combo_count = 0

GameMap.next_level(player)

# ===== DEBUG BOSS FIGHT =====
if DEBUG_BOSS_FIGHT:
    boss = monsters.create_boss_group(player.dungeon_level)

    survived = combat(player, boss)

    if not survived:
        core.print_center_block("Konec hry (debug boss)")
        exit()

    core.print_center_block("Boss poražen (debug), pokračuje hra...")
    input("ENTER...")

while player.hp > 0:
    clear_screen()

    GameMap.update_visibility(game_map, player_x, player_y)
    GameMap.draw_map(game_map, player_x, player_y)
    # game_map.print_full_map()  # pouze při testování generování map

    core.print_center_block(
        f"\nHP: {player.hp}/{player.max_hp}, XP: {player.xp}, LVL: {player.lvl}, Dungeon lvl: {player.dungeon_level}")

    cmd = input(
        "\n(Pohyb = WASD, q = konec, i = inventář, b = besiař, h = help): ").lower()

    if cmd == "q":
        break
    elif cmd == "i":
        show_inventory(player)
        continue
    elif cmd == "b":
        show_bestiary(player)
        continue
    elif cmd == "h":
        show_help()
        continue

    new_x, new_y = move_player(cmd, player_x, player_y, game_map)
    if (new_x, new_y) == (player_x, player_y):
        continue

    player_x, player_y = new_x, new_y

    clear_screen()
    GameMap.update_visibility(game_map, player_x, player_y)
    GameMap.draw_map(game_map, player_x, player_y)
    core.print_center_block(f"\nHP: {player.hp}")

    status, messages = GameMap.handle_tile(
        game_map, player_x, player_y, player, combat)

    for msg in messages:
        core.print_center_block(msg)
    if messages:
        input("ENTER pro pokračování...")

    if status == "player_dead":
        core.print_center_block("Konec hry")
        break

    if status == "enemy_dead":
        player.xp += combat_xp
        if player.is_level_up():
            core.print_center_block("Získáváš nový level")
            level_up(player)
