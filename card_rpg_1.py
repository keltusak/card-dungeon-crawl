import random
import math
import core
import gear
import sys
import os
from collections import deque


def clear_screen():
    # Windows
    if os.name == "nt":
        os.system("cls")
    # Linux / Mac
    else:
        os.system("clear")


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
            self.add_dead_end_corridors(count=5, max_length=3)

        return rooms

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.grid[y][x] = "."

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.grid[y][x] = "."

    def add_dead_end_corridors(self, count=4, max_length=4):
        for _ in range(count):
            possible_starts = [(x, y) for y in range(self.height)
                               for x in range(self.width) if self.grid[y][x] == "."]

            if not possible_starts:
                break

            x, y = random.choice(possible_starts)

            dx, dy = random.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            length = random.randint(1, max_length)

            for _ in range(length):
                nx, ny = x + dx, y + dy

                if 0 < nx < self.width-1 and 0 < ny < self.height-1 and self.grid[ny][nx] == "#":
                    self.grid[ny][nx] = "."
                    x, y = nx, ny
                else:
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
                    paths = sum(1 for nx, ny in neighbors if self.grid[ny][nx] == ".")
                    if paths == 1:
                        candidates.append((x, y))

        if not candidates:
            # fallback
            return [(random.randint(0, self.width - 1), random.randint(0, self.height - 1))]

        chosen = random.choice(candidates)
        existing_fires.append(chosen)  # zaznamenáme nově vybrané ohniště
        return [chosen]

    def generate_chest_positions(self, player_x, player_y, chest_count=1):
        candidates = []

        for y in range(1, self.height-1):
            for x in range(1, self.width-1):
                if self.grid[y][x] != "." or (x, y) == (player_x, player_y):
                    continue

                # kontrola sousedů
                neighbors = [
                    (x + dx, y + dy)
                    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]
                    if 0 <= x+dx < self.width and 0 <= y+dy < self.height
                ]
                free_neighbors = sum(1 for nx, ny in neighbors if self.grid[ny][nx] == ".")
                
                if free_neighbors == 1:  # jen jedna cesta ven => slepá ulička
                    candidates.append((x, y))

        if not candidates:  # fallback: jen kdekoliv
            candidates = [(x, y) for y in range(self.height) for x in range(self.width) if self.grid[y][x] == "." and (x,y)!=(player_x, player_y)]

        chosen = random.sample(candidates, min(chest_count, len(candidates)))
        return chosen

    #test na mapu
    def print_full_map(self):
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                row += self.grid[y][x] + " "  # přidáme mezeru mezi políčka
            print(row)

    def generate_objects(self, bonefire_count, chest_count, player_x, player_y, door_count=1):
        existing_fires = []

        for x, y in self.generate_chest_positions(player_x, player_y, chest_count=chest_count):
            self.place_chest(x, y)
            self.place_chest_guard(x, y)

        for _ in range(bonefire_count):
            for x, y in self.generate_bonefire_positions(player_x, player_y, existing_fires=existing_fires, min_distance=3):
                self.place_bonefire(x, y)

        for _ in range(door_count):
            while True:
                x, y = self.find_best_door_position(player_x, player_y)
                self.place_door(x, y)
                self.place_door_guards(x, y)
                break

    def generate_enemies(self, count, player_x, player_y):
        for _ in range(count):
            while True:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)

                if (x, y) != (player_x, player_y) and self.grid[y][x] == ".":
                    self.place_enemy(x, y)
                    break
    
    def place_chest_guard(self, chest_x, chest_y):
        neighbors = [
            (chest_x + dx, chest_y + dy)
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]
            if 0 <= chest_x + dx < self.width and 0 <= chest_y + dy < self.height
        ]
        random.shuffle(neighbors)

        for nx, ny in neighbors:
            if self.grid[ny][nx] == ".":
                self.place_enemy(nx, ny)
                return

    def place_door_guards(self, door_x, door_y, first_wave_count=2, second_wave_count=2):
        # BFS vzdálenosti od dveří
        distances = [[None for _ in range(self.width)] for _ in range(self.height)]
        distances[door_y][door_x] = 0
        queue = deque([(door_x, door_y)])

        while queue:
            x, y = queue.popleft()
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:  # sousední políčka
                nx, ny = x+dx, y+dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.grid[ny][nx] == "." and distances[ny][nx] is None:
                        distances[ny][nx] = distances[y][x] + 1
                        queue.append((nx, ny))

        # Seznam dostupných políček (x, y, vzdálenost)
        available_positions = [(x, y, distances[y][x]) for y in range(self.height)
                            for x in range(self.width) if distances[y][x] is not None and distances[y][x] > 0]

        if not available_positions:
            return  # není kam umístit

        # --- První vlna ---
        first_wave_candidates = [pos for pos in available_positions if 1 <= pos[2] <= 3]
        random.shuffle(first_wave_candidates)
        first_wave = first_wave_candidates[:first_wave_count]

        for x, y, _ in first_wave:
            self.place_enemy(x, y)

        # --- Druhá vlna ---
        blocked_positions = {(x, y) for x, y, _ in first_wave}
        max_first_distance = max(pos[2] for pos in first_wave) if first_wave else 0
        second_wave_candidates = [pos for pos in available_positions
                                if (pos[0], pos[1]) not in blocked_positions and pos[2] > max_first_distance]
        random.shuffle(second_wave_candidates)
        second_wave = second_wave_candidates[:second_wave_count]

        for x, y, _ in second_wave:
            self.place_enemy(x, y)

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
            3 + player.dungeon_level, player_x, player_y)
        game_map.generate_objects(2, 2, player_x, player_y, door_count=1)

    @staticmethod
    def handle_tile(game_map, x, y, player, combat_function):
        messages = []
        status = None  # defaultně žádný stav

        tile = game_map.grid[y][x]

        if tile == "E":
            enemies = create_enemy_group(player.dungeon_level)
            survived = combat_function(player, enemies)

            if survived:
                game_map.grid[y][x] = "."
            else:
                status = "player_dead"

        elif tile == "^":
            heal_amount = 5
            player.hp = min(player.max_hp, player.hp + heal_amount)
            messages.append(
                f"Bonefire: doplnil jsi {heal_amount} HP (HP: {player.hp})")
            game_map.grid[y][x] = "."

        elif tile == "▣":
            loot_options = [gear.ring_of_defense, gear.abakus, gear.madmans_eye, gear.war_paints,
                            gear.wurm_ring, gear.poisoners_ring, gear.ring_with_needle, gear.dagger,
                            gear.shield_with_spike, gear.caltrops, gear.flail, gear.rabits_paw]
            loot = random.choice(loot_options)
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
    print("- Můžeš měnit své aktuálně používané vybavení\n")

    print("\033[93mTypy karet:\033[0m")
    print("- Útočné (DMG) - způsobují poškození nepříteli")
    print("- Obranné (BLOCK) - přidávají obranu na tento tah")
    print("- Efekty (EFFECT) - aplikují stavové efekty jako Omráčení, Úhyb, Otrava")
    print("- Speciální - např. DRAW (táhni karty), DISCARD (odstraň karty)\n")

    print("\033[93mEfekty:\033[0m")
    print("- Omráčení (Stun) - jednotka vynechá tah")
    print("- Úhyb (Dodge) - šance vyhnout se útoku")
    print("- Otrava (Poison) - poškození v průběhu několika kol\n")

    print("\033[93mSynergie:\033[0m")
    print("- Když máš určité kombinace vybavení, získáš bonusové karty")
    print("- Např. 'Krátký Meč + Štít' = karta 'Útok a kryt'\n")

    print("\033[93mCíl hry:\033[0m")
    print("- Zlepšuj svůj deck")
    print("- Hledej vstupy do dalších levlů\n")

    print("\033[93mTipy:\033[0m")
    print("- Chytře využívej svou energii na daný tah")
    print("- Kombinuj vybavení pro silnější synergie")
    print("- Studuj nepřátele, každý má svůj vlastní balíček karet\n")

    input("Stiskni ENTER pro návrat do hry...")


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
        print("5: Konec")

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

            if not deck_exists:
                print("Deck je prázdný!")

            input("\nENTER pro návrat do inventáře...")

        elif choice == "5":
            break

        else:
            print("Neplatná volba!")


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


def create_enemy():
    enemy_names = ["Goblin", "Vrah", "Strážce", "Obří komár"]
    return create_enemy_by_name(random.choice(enemy_names))


def create_enemy_by_name(name):
    enemy_types = {
        "Goblin": {
            "hp": 12,
            "equipment": [gear.broken_sword]
        },
        "Vrah": {
            "hp": 10,
            "equipment": [gear.poison_dagger]
        },
        "Strážce": {
            "hp": 15,
            "equipment": [gear.broken_sword, gear.shield]
        },
        "Obří komár": {
            "hp": 5,
            "equipment": [gear.proboscis, gear.wings]
        },
        "Mraveniště": {
            "hp": 14,
            "equipment": [gear.ant_queen],
        },
        "Mravenec": {
            "hp": 1,
            "equipment": [gear.mandibles],
        },
        "Goblinní zvěd": {
            "hp": 12,
            "equipment": [gear.broken_sword, gear.horn, gear.reflexis]
        },
        "Goblinní válečník": {
            "hp": 16,
            "equipment": [gear.sword, gear.shield, gear.war_paints]
        },
        "Pavoučí mládě": {
            "hp": 7,
            "equipment": [gear.small_fangs, gear.exoskelet],
        },
        "Pavouk s vejcem": {
            "hp": 16,
            "equipment": [gear.fangs, gear.exoskelet, gear.spiders_cocon],
        },
    }

    template = enemy_types[name]

    enemy = Character(name, template["hp"])
    for item in template["equipment"]:
        enemy.equip_item(item, suppress_print=True)
    enemy.build_deck()

    return enemy


def create_enemy_group(dungeon_level=1):
    encounter_types = [
        {"type": "komáři", "enemies": [("Obří komár", 1, 3)], "levels": [1, 2]},
        {"type": "goblini", "enemies": [("Goblin", 1, 2)], "levels": [1, 2]},
        {"type": "strážci", "enemies": [("Strážce", 1, 2)], "levels": [1, 2]},
        {"type": "vrazi", "enemies": [("Vrah", 1, 2)], "levels": [1, 2, 3]},
        {"type": "mravenci", "enemies": [("Mraveniště", 1, 1)], "levels": [1, 2]},
        #od lvl 2
        {"type": "gobliní průzkumník", "enemies":[("Goblinní zvěd", 1, 1)], "levels": [2, 3]},
        {"type": "gobliní hlídka", "enemies": [("Goblinní válečník", 1, 1), ("Goblin", 1, 1)], "levels": [2, 3]},
        {"type": "gobliní stráž","enemies": [("Goblinní válečník", 1, 1), ("Goblinní zvěd", 1, 1)],"levels": [2, 3]},
        {"type": "Lovící pavouk","enemies": [("Pavouk s vejcem", 1, 1)],"levels": [3]},
    ]

    possible_encounters = [
        e for e in encounter_types if dungeon_level in e["levels"]]

    if not possible_encounters:
        raise ValueError(
            f"Pro dungeon level {dungeon_level} nejsou definované žádné skupiny nepřátel.")

    encounter = random.choice(possible_encounters)

    enemies = []
    for enemy_info in encounter["enemies"]:
        name, min_count, max_count = enemy_info
        count = random.randint(min_count, max_count)
        for _ in range(count):
            enemies.append(create_enemy_by_name(name))

    print(
        f"Narazil jsi na skupinu: {encounter['type']} ({len(enemies)} nepřátel)")
    return enemies


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


class Character:
    def __init__(self, name, hp, strenght=0, temporary_strenght=0):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.strenght = strenght
        self.temporary_strenght = temporary_strenght

        self.block = 0
        self.status_effects = []

        self.slots = {
            "hand": [None, None],
            "body": [None],
            "belt": [None, None],
            "pocket": [None, None, None],
            "ring": [None, None],
            "companion": [None]
        }
        self.inventory = []
        self.equipment = []

        self.deck = []
        self.hand = []
        self.discard = []


    def build_deck(self):
        self.deck = []

        added_items = set()

        for slot_list in self.slots.values():
            for item in slot_list:
                if not item:
                    continue

                # dvouruční item – přidej jen jednou
                if item.two_handed:
                    if id(item) in added_items:
                        continue
                    added_items.add(id(item))

                # normální itemy se přidají vždy
                self.deck.extend(item.cards)

        # --- SYNERGIE ---
        equipment_names = [item.name for slot in self.slots.values()
                        for item in slot if item]

        for synergy in core.SYNERGIES:
            if all(req in equipment_names for req in synergy["requires"]):
                self.deck.extend(synergy["cards"])

        random.shuffle(self.deck)

    def draw(self, n=3):
        for _ in range(n):
            if not self.deck:
                self.deck = self.discard
                self.discard = []
                shuffle_deck(self.deck, shuffler=self)
                
            if self.deck:
                self.hand.append(self.deck.pop())

    def apply_fatigue(self):
        if self.fatigue > 0:
            print(f"{self.name} cítí únavu a ztrácí {self.fatigue} HP!")
            input("ENTER pro pokračování...")
            self.hp -= self.fatigue
            if self.hp < 0:
                self.hp = 0
        self.fatigue += 1


    def play_card(self, index, target=None, enemies_list=None, create_enemy_func=None):
        if 0 <= index < len(self.hand):
            card = self.hand.pop(index)
            # předáme všechny potřebné argumenty kartě
            card.play(user=self, target=target, enemies_list=enemies_list,
                      create_enemy_func=create_enemy_func)
            self.discard.append(card)
        else:
            print("Neplatný index karty")

    def take_damage(self, amount, ignore_armor=False, suppress_print=False):
        for effect in self.status_effects:
            if isinstance(effect, core.Dodge):
                if random.random() < effect.chance:
                    if not suppress_print:
                        print(f"{self.name} se vyhnul útoku!")
                    return 0

        if ignore_armor:
            self.hp -= amount
            if not suppress_print:
                print(
                    f"{Colors.RED}{self.name} dostal {amount} dmg (ignoruje armor) (HP: {self.hp}{Colors.RESET})")
            return amount

        reduced = max(amount - self.block, 0)
        self.block = max(self.block - amount, 0)
        self.hp -= reduced

        if not suppress_print:
            print(
                f"{Colors.RED}{self.name} dostal {reduced} dmg (HP: {self.hp}{Colors.RESET})")
        return reduced

    def equip_item(self, item, suppress_print=False):
        # pokud je obouruční, musí být volné **oba hand sloty**
        if item.slot_type == "hand" and getattr(item, "two_handed", False):
            if any(self.slots["hand"]):
                print("Potřebuješ volné oba hand sloty pro obouruční zbraň!")
                input("ENTER pro pokračování...")
                return False
            else:
                self.slots["hand"][0] = item
                self.slots["hand"][1] = item
                if item in self.inventory:
                    self.inventory.remove(item)
                print(f"{self.name} vybavil obouruční zbraň {item.name}")
                return True

        # standardní logika pro jednoruké zbraně
        slots = self.slots[item.slot_type]
        for i in range(len(slots)):
            if slots[i] is None:
                slots[i] = item
                if item in self.inventory:
                    self.inventory.remove(item)
                if not suppress_print:
                    print(f"{self.name} vybavil {item.name}")
                return True

        print("Není volný slot")
        return False

    def unequip_item(self, slot_type, index):
        item = self.slots[slot_type][index]

        if item:
            # pokud je obouruční a slot je "hand", odeber oba sloty
            if slot_type == "hand" and getattr(item, "two_handed", False):
                for i in range(len(self.slots["hand"])):
                    if self.slots["hand"][i] == item:
                        self.slots["hand"][i] = None
                print(f"{self.name} sundal obouruční zbraň: {item.name}")
            else:
                self.slots[slot_type][index] = None
                print(f"{self.name} sundal {item.name}")

            self.inventory.append(item)
        else:
            print("Slot je prázdný")

    def reset_combat(self):
        self.deck = []
        self.hand = []
        self.discard = []
        self.status_effects = []
        self.block = 0
        self.temporary_strenght = 0
        player.fetigue = 0

    def add_block(self, amount):
        self.block += amount
        print(f"{Colors.GRAY}{self.name} získal {amount} block{Colors.RESET}")

    def add_temporary_strenght(self, amount):
        self.temporary_strenght += amount
        print(f"{self.name} získal {amount} dočasné síly")

    def apply_effect(self, effect):
        self.effects.append(effect)
        effect.apply(self)

    def is_stunned(self):
        return any(isinstance(e, core.Stun) for e in self.status_effects)

    def show_hand(self):
        print("\nTvoje karty:")
        core.print_cards(player.hand)

    def has_playable_card(self):
        for card in player.hand:
            if card.cost <= self.energy:
                return True
        return False

    def player_turn(player, enemies):
        player.energy = 2

        while player.hand and player.has_playable_card():
            clear_screen()

            print(f"\n{Colors.GREEN}--- Tvůj tah ---{Colors.RESET}")
            print(f"- {player.name} (HP: {player.hp}, {Colors.GRAY}Block: {player.block}{Colors.RESET}, Energy: {player.energy}){format_status_effects(player)}")

            print("\nNepřátelé:")
            for e in enemies:
                if e.hp > 0:
                    print(f"- {e.name} (HP: {e.hp}, {Colors.GRAY}Block: {e.block}{Colors.RESET}){format_status_effects(e)}")
            
            player.show_hand()

            print("\n(ENTER = ukončit tah)")
            choice = input("Vyber kartu: ")

            if choice == "":
                break

            if not choice.isdigit():
                print("Neplatná volba")
                input("ENTER...")
                continue

            index = int(choice)

            if index < 0 or index >= len(player.hand):
                print("Neplatná karta")
                input("ENTER...")
                continue

            card = player.hand[index]

            if card.cost > player.energy:
                print("Nedostatek energie")
                input("ENTER...")
                continue

            # ===== TARGET =====
            if card.target_type == "enemy":
                target = choose_enemy(enemies)
                player.play_card(index, target)

            elif card.target_type == "self":
                player.play_card(index, player)

            elif card.target_type == "all_enemies":
                for e in enemies:
                    if e.hp > 0:
                        card.play(player, e)
                player.hand.pop(index)
                player.discard.append(card)

            player.energy -= card.cost

            # ===== KONTROLY =====
            if all(e.hp <= 0 for e in enemies):
                return "enemy_dead"

            if player.hp <= 0:
                return "player_dead"

            print(f"\nZbývá energie: {player.energy}")

            input("\nENTER pro pokračování...")

        return None

    def process_status(self):
        for effect in self.status_effects:
            effect.apply(self)

        new_effects = []
        for effect in self.status_effects:
            if not effect.tick():
                new_effects.append(effect)
            else:
                print(f"{self.name} se zbavil efektu {effect.name}.")

        self.status_effects = new_effects


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

def shuffle_deck(deck, shuffler):
        random.shuffle(deck)

        if shuffler is player:  
            if hasattr(player, "fetigue"):
                if player.fetigue > 0:
                    print(f"{Colors.RED}{player.name} cítí únavu a ztrácí {player.fetigue} HP!{Colors.RESET}")
                    input("ENTER pro pokračování...")
                    player.hp -= player.fetigue
                    if player.hp < 0:
                        player.hp = 0
                    print(f"HP hráče: {player.hp}/{player.max_hp}")
                player.fetigue += 1

class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"
    RESET = "\033[0m"

def format_status_effects(character):
    if not character.status_effects:
        return ""

    effects = []
    for effect in character.status_effects:
        effects.append(f"{effect.name}({effect.duration})")

    return " | " + ", ".join(effects)

def combat(player, enemies):
    player.reset_combat()
    for enemy in enemies:
        enemy.reset_combat()

    player.build_deck()
    for enemy in enemies:
        enemy.build_deck()

    first_turn = True

    while player.hp > 0 and any(e.hp > 0 for e in enemies):
        clear_screen()
        print("\n--- Nové kolo ---")
        player.block = 0
        print(f"- {player.name} (HP: {player.hp}, {Colors.GRAY}Block: {player.block}{Colors.RESET}, Energy: {player.energy}){format_status_effects(player)}")
        print("\nNepřátelé:")
        for e in enemies:
            if e.hp > 0:
                print(f"- {e.name} (HP: {e.hp}, {Colors.GRAY}Block: {e.block}{Colors.RESET})"
                    f"{format_status_effects(e)}")
        print()

        # ===== PLAYER =====
        if player.is_stunned():
            print(f"{player.name} vynechává tah kvůli omráčení!")
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
                print(f"Narazil jsi na {enemy.name}")
                first_turn = False
            else:
                player.draw(2)

            result = Character.player_turn(player, enemies)

            if result == "enemy_dead":
                print("Vyhrál jsi!")
                input("ENTER pro pokračování...")
                return True
            elif result == "player_dead":
                print("Prohrál jsi!")
                input("ENTER pro pokračování...")
                return False
        clear_screen()
        print(f"\n{Colors.RED}--- Nepřátelský tah ---{Colors.RESET}")
        print(f"- {player.name} (HP: {player.hp}, {Colors.GRAY}Block: {player.block}{Colors.RESET}, Energy: {player.energy}){format_status_effects(player)}")
        print("\nNepřátelé:")
        for e in enemies:
            if e.hp > 0:
                print(f"- {e.name} (HP: {e.hp}, {Colors.GRAY}Block: {e.block}{Colors.RESET}){format_status_effects(e)}")
        player.show_hand()

        # ===== ENEMY =====
        print("\n--- Nepřátelé hrají ---\n")

        for enemy in enemies:
            enemy.block = 0

        for enemy in enemies[:]:
            if enemy.hp <= 0:
                continue

            # Zpracování stunu
            if enemy.is_stunned():
                print(f"{Colors.YELLOW}{enemy.name} je omráčen!{Colors.RESET}")
                enemy.process_status()
                if enemy.hp <= 0:
                    continue
                continue

            enemy.process_status()
            if enemy.hp <= 0:
                continue
            
            enemy.draw(1)

            if enemy.hand:
                enemy.play_card(
                    0,
                    target=player,
                    enemies_list=enemies,
                    create_enemy_func=create_enemy_by_name
                )

            if player.hp <= 0:
                print("Prohrál jsi!")
                input("ENTER pro pokračování...")
                return False
            
        if all(enemy.hp <= 0 for enemy in enemies):
                print("Vyhrál jsi!")
                input("ENTER pro pokračování...")
                return True

        input("Stiskni cokoliv pro vstup do dalšího kola:")

# ===== MAIN LOOP ========
player = Character("Hráč", 20)
player.dungeon_level = 1
player.fetigue = 0
player.energy = 2
player.equip_item(gear.mace)
player.equip_item(gear.leather_armor)
player.equip_item(gear.poisoners_ring)

game_map = GameMap(24, 20)
rooms = game_map.generate_dungeon()
player_x, player_y = rooms[0].center()
game_map.generate_objects(2, 2, player_x, player_y,)
game_map.generate_enemies_in_corridors(3, player_x, player_y)


while player.hp > 0:
    clear_screen()

    GameMap.update_visibility(game_map, player_x, player_y)
    GameMap.draw_map(game_map, player_x, player_y)
    #game_map.print_full_map()    -pouze při testování generování map

    print(f"\nHP: {player.hp}, Dungeon lvl: {player.dungeon_level}")

    cmd = input("\nPohyb (WASD, q = konec, i = inventář, h = help): ").lower()

    if cmd == "q":
        break
    elif cmd == "i":
        show_inventory(player)
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
        input("ENTER pro pokračování...")
        break
