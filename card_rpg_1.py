import random
import math
import sys
import os
from collections import deque
import textwrap
import shutil

# ostatní soubory
import core
import gear
import abilities
import character
import monsters


def clear_screen():
    # Windows
    if os.name == "nt":
        os.system("cls")
    # Linux / Mac
    else:
        os.system("clear")


def get_terminal_width():
    return shutil.get_terminal_size().columns


def center_text(text, width):
    return text.center(width)


def print_box(title, stats, description, width=60):
    print("=" * width)
    print(title.center(width))
    print("=" * width)

    for stat in stats:
        print(stat.ljust(width))

    print("-" * width)

    wrapped_text = textwrap.wrap(description, width)
    for line in wrapped_text:
        print(line)

    print("=" * width)


def print_section(title, text, width=60):
    print("\n" + title.upper().center(width))
    print("-" * width)

    wrapped = textwrap.wrap(text, width)
    for line in wrapped:
        print(line)


class GameMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.grid = [["#" for _ in range(width)] for _ in range(height)]

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
            print(row)

    def generate_objects(self, bonefire_count, chest_count, player_x, player_y, door_count=1):
        existing_fires = []
        chest_positions = []
        door_positions = []

        # 1) Položení všech dveří
        for _ in range(door_count):
            x, y = self.find_best_door_position(player_x, player_y)
            self.place_door(x, y)
            door_positions.append((x, y))

        # 2) Položení všech truhel
        for x, y in self.generate_chest_positions(player_x, player_y, chest_count=chest_count):
            self.place_chest(x, y)
            chest_positions.append((x, y))

        # 3) Položení všech ohnišť

        # 4) Teprve nyní umístíme guardy
        for x, y in door_positions:
            pass
            self.place_door_guards(x, y)

        for x, y in chest_positions:
            self.place_chest_guard(x, y)

        for _ in range(bonefire_count):
            for x, y in self.generate_bonefire_positions(player_x, player_y, existing_fires=existing_fires, min_distance=3):
                self.place_bonefire(x, y)

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

    def update_visibility(game_map, px, py, radius=2):
        for y in range(game_map.height):
            for x in range(game_map.width):

                if math.sqrt((x - px)**2 + (y - py)**2) <= radius:
                    game_map.visible[y][x] = True
                    game_map.explored[y][x] = True
                else:
                    game_map.visible[y][x] = False

    def draw_map(game_map, px, py):
        for y in range(game_map.height):
            for x in range(game_map.width):
                char = game_map.grid[y][x]

                if x == px and y == py:
                    print("\033[93mP\033[0m", end=" ")
                elif not game_map.explored[y][x]:
                    # neprozkoumané
                    print("?", end=" ")
                elif not game_map.visible[y][x]:
                    # prozkoumané, ale mimo dohled - šedě
                    print(f"\033[90m{char}\033[0m", end=" ")
                else:
                    # právě viditelné
                    if char == "#":
                        print("\033[92m#\033[0m", end=" ")
                    elif char == "E":
                        print("\033[91mE\033[0m", end=" ")
                    elif char == "^":
                        print("\033[38;5;208m^\033[0m", end=" ")
                    elif char == "▣":
                        print("\033[38;5;94m▣\033[0m", end=" ")
                    elif char == "▮":
                        print("▮", end=" ")
                    else:
                        print(".", end=" ")
            print()

    def next_level(player):
        global game_map, player_x, player_y

        player.dungeon_level += 1

        game_map = GameMap(24, 20)
        rooms = game_map.generate_dungeon()

        player_x, player_y = rooms[0].center()

        game_map.generate_enemies_in_corridors(
            2 + player.dungeon_level, player_x, player_y)
        game_map.generate_objects(2, 2, player_x, player_y, door_count=1)

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

        return status, messages


def show_help():
    clear_screen()
    print("\033[96m=== PŘÍRUČKA HRY ===\033[0m\n")  # světle modrý nadpis

    print("\033[93mOvládání:\033[0m")  # žluté nadpisy
    print("WASD - pohyb po mapě")
    print("Q - ukončit hru")
    print("I - otevřít inventář")
    print("H - zobrazit tuto příručku")
    print("V boji vyber číslo karty nebo ENTER pro konec tahu\n")

    print("\033[93mMapa a ikony:\033[0m")
    print("- # - stěna")
    print("- . - průchozí dlaždice / chodba")
    print("- P - tvoje pozice")
    print("- E - nepřítel")
    print("- ^ - ohniště, doplní část zdraví")
    print("- ▣ - truhla s lootem")
    print("- ▮ - dveře do dalšího patra")
    print("Vstup na pole s ním automaticky interaguje!\n")

    print("\033[93mInventář:\033[0m")
    print("V inventáři najdeš své vybavení a karty, které ti poskytuje.")
    print("Každé vybavení může obsahovat jednu nebo více karet.")
    print("Pokud máš aktivní synergie mezi vybavením, zobrazí se zvlášť modře.")
    print("Použití inventáře:")
    print("- Můžeš si zde prohlédnout aktuální deck")
    print("- Můžeš se podívat co jednotlivé vybavená umí")
    print("- Můžeš měnit své aktuálně používané vybavení")
    print("- Můžeš si zde spravovat své naučené schopnosti\n")

    print("\033[93mSouboj:\033[0m")
    print("- V souboji hraješ se svým balíčkem, který obsahuje karty,\n"
          "dané tvým akutálním vybavením a aktivními schopnostmi.")
    print("- Po vyčerpání energie je tah předán nepříteli, který také má svůj balíček.")
    print("- Boj pokračuje dokud jedna ze stran není úplně poražena")
    print("- Každá zahrátá karta je odložena na odhazovací balíček, který je domíchán, jakmile\n"
          "dobereš svůj balíček.")
    print("- Kdykoliv zamícháš v boji odhazovací balíček, je v rámci souboje tvojí postavě přidána únava.\n"
          "Při každém zamíchání tvoje postavautrpí zranění ve výši tvé únavy.\n")

    print("\033[93mLevly:\033[0m")
    print("- Za porážení nepřátel dostáváš zkušenosti")
    print("- Při postupu na novou úroveň se zvýší tvé dosavadní maximální zdraví a")
    print("máš možnost si vybrat jednu ze tří schopností, která se ti odemkne.\n")

    print("\033[93mTypy karet:\033[0m")
    print("- Útočné (DMG) - způsobují poškození nepříteli")
    print("- Obranné (BLOCK) - přidávají obranu na tento tah")
    print("- Efekty (EFFECT) - aplikují stavové efekty jako Omráčení, Úhyb, Otrava")
    print("- Speciální - např. DRAW (táhni karty), DISCARD (zahoď karty)\n")

    print("\033[93mEfekty:\033[0m")
    print("- Omráčení (Stun) - jednotka vynechá tah")
    print("- Úhyb (Dodge) - šance vyhnout se útoku")
    print("- Otrava (Poison) - poškození v průběhu několika kol")
    print("- Trny - útok na toho, kdo má tento efekt, útočníkovi způsobí zranění\n")

    print("\033[93mSynergie:\033[0m")
    print("- Když používáš určité kombinace vybavení, získáš bonusové karty")
    print("- Např. 'Krátký Meč + Štít' = karta 'Útok a kryt'\n")

    print("\033[93mCíl hry:\033[0m")
    print("- Zlepšuj svůj deck s pomocí silnějšího vybavení")
    print("- Hledej vstupy do dalších částí mapy a levlů\n")

    print("\033[93mTipy:\033[0m")
    print("- Chytře využívej svou energii na daný tah")
    print("- Kombinuj vybavení pro odalování sinergií")
    print("- Studuj nepřátele, každý má svůj vlastní balíček karet a ti silnější dokonce i strategie\n")

    input("Stiskni ENTER pro návrat do hry...")


def show_bestiary(player):
    while True:
        clear_screen()
        print("\n=== BESTIÁŘ ===\n")

        enemies = list(player.bestiary.keys())

        for i, name in enumerate(enemies):
            kills = player.bestiary[name]["kills"]
            print(f"{i+1}. {name} (Zabit: {kills}x)")

        print("\n(Vyber nepřítele = 1-X, q = zpět): ")
        choice = input("\n> ")

        if choice == "q":
            return

        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(enemies):
                show_enemy_detail(player, enemies[index])
        print()


def show_enemy_detail(player, enemy_name):
    clear_screen()
    data = player.bestiary[enemy_name]

    kills = data['kills']
    info = data['info']

    print(f"\n=== {enemy_name} ===")
    print(f"Zabit: {kills}x\n")

    all_cards = data.get("all_cards", [])
    seen_cards = data["seen_cards"]

    if kills >= 1:
        print(f"Karty ({len(seen_cards)}/{len(all_cards)}):")
        for card in all_cards:
            if card in seen_cards:
                print(f" - {card}")
            else:
                print(" - ???")
    else:
        print("\n???")

    if kills >= 1:
        print_section("Popis", info.get('description', '???'))

    if kills >= 3:
        print_section("Lore", info.get('lore', '???'))
    else:
        print("\nLORE".center(60))
        print("-" * 60)
        print("??? (zabij více nepřátel)")

    if kills >= 6:
        print_section("Extra lore", info.get('extra_lore', '???'))
    else:
        print("\nEXTRA LORE".center(60))
        print("-" * 60)
        print("??? (zabij více nepřátel)")

    input("\nENTER pro návrat...")


def show_inventory(player):
    while True:
        clear_screen()

        print("\n=== INVENTÁŘ ===")

        print("\nVybavené:")
        for slot, items in player.slots.items():
            for i, item in enumerate(items):
                name = item.name if item else "\033[90mPrázdné\033[0m"
                print(f"{slot} [{i}]: {name}")

            print()

        print("\nBatoh:")
        if not player.inventory:
            print("Prázdný")
        else:
            for i, eq in enumerate(player.inventory):
                print(f"{i}: {eq.name} ({eq.slot_type})")

        print("\n1: Detail itemu")
        print("2: Vybavit")
        print("3: Sundat")
        print("4: Prohlédnout deck")
        print("5: Prohlédnout schopnosti")
        print("6: Konec")

        choice = input("> ")

        if choice == "1":
            if not player.inventory:
                print("Batoh je prázdný!")
                input("ENTER pro pokračování...")
                continue

            idx = get_valid_index(
                "Index itemu z batohu: ", len(player.inventory))
            eq = player.inventory[idx]

            print(f"\n--- {eq.name} ---")
            core.print_cards(eq.cards)

            input("ENTER pro pokračování...")

        elif choice == "2":
            if not player.inventory:
                print("Batoh je prázdný!")
                input("ENTER pro pokračování...")
                continue
            idx = get_valid_index(
                "Index itemu z batohu: ", len(player.inventory))
            player.equip_item(player.inventory[idx])
            player.build_deck()

        elif choice == "3":
            slot = input("Slot (hand/body/belt/pocket/ring): ")
            if slot not in player.slots:
                print("Neplatný slot!")
                input("ENTER pro pokračování...")
                continue

            print(f"\n{slot} obsah:")
            for i, item in enumerate(player.slots[slot]):
                name = item.name if item else "Prázdné"
                print(f"[{i}]: {name}")

            if all(item is None for item in player.slots[slot]):
                print("Slot je prázdný!")
                input("ENTER pro pokračování...")
                continue

            idx = get_valid_index(
                "Index slotu k odbavení: ", len(player.slots[slot]))
            player.unequip_item(slot, idx)
            player.build_deck()

        elif choice == "4":
            clear_screen()
            player.build_deck()

            print("\n--- Aktuální deck ---")
            deck_exists = False
            active_synergies = []

            added_items = set()
            for slot, items in player.slots.items():
                for eq in items:
                    if not eq:
                        continue

                    # dvouruční item – zobraz jen jednou
                    if eq.two_handed:
                        if id(eq) in added_items:
                            continue
                        added_items.add(id(eq))

                    deck_exists = True
                    print(f"\n--- {eq.name} ---")
                    core.print_cards(eq.cards)

            equipment_names = [item.name for slot in player.slots.values()
                               for item in slot if item]
            for synergy in core.SYNERGIES:
                if all(req in equipment_names for req in synergy["requires"]):
                    active_synergies.append(synergy)

            for synergy in active_synergies:
                print(
                    f"\n\033[94m--- Aktivní synergie: {', '.join(synergy['requires'])} ---\033[0m")
                core.print_cards(synergy["cards"])
                deck_exists = True

            active_card_abilities = [
                ab for ab in player.abilities
                if getattr(ab, "active", True) and getattr(ab, "type", None) == "card"
            ]

            if active_card_abilities:
                print("\n\033[96m--- Karty schopností ---\033[0m")
                for ability in active_card_abilities:
                    print(f"{ability.name}: {ability.description}")
                    core.print_cards(ability.cards)
                    print()
                    deck_exists = True

            if not deck_exists:
                print("Deck je prázdný!")

            input("\nENTER pro návrat do inventáře...")

        elif choice == "5":
            while True:
                clear_screen()
                print("\n=== SCHOPNOSTI ===")

                if not player.abilities:
                    print("Zatím nemáš žádné schopnosti.")
                    input("\nENTER pro návrat do inventáře...")
                    return

                for i, ability in enumerate(player.abilities):
                    status = "Aktivní" if getattr(
                        ability, "active", True) else "Neaktivní"
                    print(f"{i}: {ability.name} ({status}) - {ability.description}")

                print("\n1: Přepnout aktivitu schopnosti")
                print("2: Konec")

                choice = input("> ")

                if choice == "1":
                    idx = get_valid_index(
                        "Index schopnosti: ", len(player.abilities))
                    ability = player.abilities[idx]
                    ability.active = not getattr(ability, "active", True)
                    status = "aktivní" if ability.active else "neaktivní"
                    print(f"{ability.name} je nyní {status}.")
                    input("ENTER pro pokračování...")
                elif choice == "2":
                    break

        elif choice == "6":
            break

        else:
            print("Neplatná volba!")


def get_random_abilities(all_abilities, count=3):
    return random.sample(all_abilities, count)


def level_up(self):
    self.max_hp += 5
    self.hp += 5
    self.lvl += 1

    all_abilities = [
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
        print("\n\033[94m=== DOSÁHL JSI NOVÉ ÚROVNĚ! ===\033[0m")
        print("Tvé dosavadní maximalní zdraví se zvýšílo o 5.\n")
        print("Vyber si jednu schopnost:\n")

        for i, ability in enumerate(choices, 1):
            print(
                f"\033[96m{i}) {ability.name} - {ability.description}\033[0m")
            if getattr(ability, "type", None) == "card":
                core.print_cards(ability.cards)
            print()

        choice = input("\nTvoje volba: ")

        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(choices):
                selected = choices[choice - 1]
                selected.apply(self)
                print(f"\nZískal jsi: {selected.name}")
                input("Pokračuj...")
                break


def get_valid_index(prompt, max_value):
    while True:
        choice = input(prompt)

        if not choice.isdigit():
            print("Zadej číslo!")
            continue

        idx = int(choice)

        if 0 <= idx < max_value:
            return idx
        else:
            print("Index mimo rozsah!")


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
        print("Nemůžeš jít do zdi!")
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


def choose_enemy(enemies):
    alive = []
    for e in enemies:
        if e.hp > 0:
            alive.append(e)

    if len(alive) == 1:
        return alive[0]

    for i, e in enumerate(alive):
        print(f"{i}: {e.name} (HP: {e.hp})")

    while True:
        choice = input("Vyber nepřítele: ")

        if not choice.isdigit():
            print("Neplatná volba")
            continue

        index = int(choice)

        if 0 <= index < len(alive):
            return alive[index]


def combat(player, enemies):
    player.reset_combat()
    for enemy in enemies:
        enemy.reset_combat()

    player.build_deck()
    for enemy in enemies:
        enemy.build_deck()

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

    first_turn = True

    global combat_xp
    combat_xp = 1+player.dungeon_level

    while player.hp > 0 and any(e.hp > 0 for e in enemies):
        clear_screen()
        print("\n--- Nové kolo ---")

        player.block = 0
        player.combo_count = 0

        for ability in player.abilities:
            if ability.type == "passive" and ability.trigger == "per_turn" and ability.active:
                ability.effect(player)

        player.block += player.saved_block

        player.saved_block = 0

        print(
            f"- {player.name} (HP: {player.hp}, {core.Colors.GRAY}Block: {player.block}{core.Colors.RESET}, Energy: {player.energy}"
            + (f", Total_strenght: {player.strenght + player.temporary_strenght}"
               if (player.strenght + player.temporary_strenght) != 0 else "")
            + (f", Combo: {player.combo_count}"if (player.combo_count) != 0 else "")
            + f"){core.format_status_effects(player)}"
        )
        print("\nNepřátelé:")
        for e in enemies:
            if e.hp > 0:
                print(
                    f"- {e.name} (HP: {e.hp}, {core.Colors.GRAY}Block: {e.block}{core.Colors.RESET}"
                    + (f", Total_strenght: {e.strenght + e.temporary_strenght}"
                       if (e.strenght + e.temporary_strenght) != 0 else "")
                    + f"){core.format_status_effects(e)}"
                )
        print()

        # ===== PLAYER =====
        if player.is_stunned():
            print(f"{player.name} vynechává tah kvůli omráčení!")
            input("ENTER pro pokračování...")
            player.process_status()
            if player.hp <= 0:
                print("Prohrál jsi!")
                return False
        else:
            player.process_status()
            if player.hp <= 0:
                print("Prohrál jsi!")
                return False
            if first_turn:
                player.draw(3)
                print(f"Narazil jsi na {len(enemies)} nepřátel")
                first_turn = False
            else:
                player.draw(2 + player.extra_draw)
                if player.hp <= 0:
                    print("Prohrál jsi!")
                    input("ENTER pro pokračování...")
                    return False

            result = character.Character.player_turn(player, enemies)

            if player.hp <= 0:
                print("Prohrál jsi!")
                input("ENTER pro pokračování...")
                return False

            elif result == "enemy_dead":
                print("Vyhrál jsi!")
                input("ENTER pro pokračování...")
                for enemy in enemies:
                    if enemy.name in player.bestiary:
                        player.bestiary[enemy.name]["kills"] += 1
                return True
            elif result == "player_dead":
                print("Prohrál jsi!")
                input("ENTER pro pokračování...")
                return False
        clear_screen()
        print(f"\n{core.Colors.RED}--- Nepřátelský tah ---{core.Colors.RESET}")
        print(
            f"- {player.name} (HP: {player.hp}, {core.Colors.GRAY}Block: {player.block}{core.Colors.RESET}, Energy: {player.energy}"
            + (f", Total_strenght: {player.strenght + player.temporary_strenght}"
               if (player.strenght + player.temporary_strenght) != 0 else "")
            + f"){core.format_status_effects(player)}"
        )
        print("\nNepřátelé:")
        for e in enemies:
            if e.hp > 0:
                print(
                    f"- {e.name} (HP: {e.hp}, {core.Colors.GRAY}Block: {e.block}{core.Colors.RESET}"
                    + (f", Total_strenght: {e.strenght + e.temporary_strenght}"
                       if (e.strenght + e.temporary_strenght) != 0 else "")
                    + f"){core.format_status_effects(e)}"
                )
        player.show_hand()

        for enemy in enemies:
            for ability in enemy.abilities:
                if ability.type == "passive" and ability.trigger == "after_opponent_turn" and ability.active:
                    ability.effect(enemy)

        # ===== ENEMY =====
        print("\n--- Nepřátelé hrají ---\n")
        for enemy in enemies:
            enemy.block = 0

        # start of turn ability později

        for enemy in enemies:
            enemy.block += enemy.saved_block

        for enemy in enemies:
            enemy.saved_block = 0

        for enemy in enemies[:]:
            if enemy.hp <= 0:
                continue

            # Zpracování stunu
            if enemy.is_stunned():
                print(
                    f"{core.Colors.YELLOW}{enemy.name} je omráčen!{core.Colors.RESET}")
                enemy.process_status()
                if enemy.hp <= 0:
                    continue
                continue

            enemy.process_status()
            if enemy.hp <= 0:
                continue

            if enemy.ai:
                # nepřátelé s prioritami hraných karet
                enemy.ai(enemy, player, enemies)
            else:
                # běžní nepřátelé
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
                        if allies:
                            target = random.choice(allies)
                        else:
                            target = enemy
                    else:
                        target = player

                    enemy.play_card(
                        index,
                        target=target,
                        enemies_list=enemies,
                        create_enemy_func=monsters.create_enemy_by_name,
                        player=player
                    )

            if player.hp <= 0:
                print("Prohrál jsi!")
                input("ENTER pro pokračování...")
                return False

        if all(enemy.hp <= 0 for enemy in enemies):
            print("Vyhrál jsi!")
            input("ENTER pro pokračování...")
            for enemy in enemies:
                if enemy.name in player.bestiary:
                    player.bestiary[enemy.name]["kills"] += 1
            return True

        for ability in player.abilities:
            if ability.trigger == "after_opponent_turn" and ability.active:
                ability.effect(player)

        input("Stiskni cokoliv pro vstup do dalšího kola:")


def select_starting_build(player):
    while True:
        clear_screen()
        print("\n\033[94m=== VYBER POSTAVU ZA KTEROU CHCEŠ HRÁT: ===\033[0m")
        print("1) Voják")
        print("2) Kultista")
        print("3) Mág")

        choice = input("> ")

        if choice == "1":
            clear_screen()

            print_box(
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
                player.player_class = "vojak"
                return

        elif choice == "2":
            clear_screen()

            print_box(
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

            print_box(
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

                return

        else:
            print("Neplatná volba.")


# ===== MAIN LOOP ========
clear_screen()
player = character.Character("Hráč", 20)
select_starting_build(player)
player.is_player = True
player.abilities = []
player.dungeon_level = 1
player.fatigue = 0
player.reduced_energy = 0
player.combo_count = 0
player.xp = 0
player.lvl = 1

game_map = GameMap(24, 20)
rooms = game_map.generate_dungeon()
player_x, player_y = rooms[0].center()
game_map.generate_objects(2, random.randint(1, 3), player_x, player_y,)
game_map.generate_enemies_in_corridors(2, player_x, player_y)


while player.hp > 0:
    clear_screen()

    GameMap.update_visibility(game_map, player_x, player_y)
    GameMap.draw_map(game_map, player_x, player_y)
    # game_map.print_full_map()  # pouze při testování generování map

    print(
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
    print(f"\nHP: {player.hp}")

    status, messages = GameMap.handle_tile(
        game_map, player_x, player_y, player, combat)

    for msg in messages:
        print(msg)
    if messages:
        input("ENTER pro pokračování...")

    if status == "player_dead":
        print("Konec hry")
        break

    if status == "enemy_dead":
        player.xp += combat_xp
        if player.is_level_up():
            print("Získáváš nový level")
            level_up(player)
