import random
import math
import core
import gear
import sys
import os


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

    def add_dead_end_corridors(self, count=4, max_length=3):
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
                    self.grid[ny][nx] = "."  # vytvoř chodbu
                    x, y = nx, ny
                else:
                    break

    def generate_objects(self, bonefire_count, chest_count, player_x, player_y):
        for _ in range(bonefire_count):
            while True:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                if self.grid[y][x] == "." and (x, y) != (player_x, player_y):
                    self.place_bonefire(x, y)
                    break

        for _ in range(chest_count):
            while True:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                if self.grid[y][x] == "." and (x, y) != (player_x, player_y):
                    self.place_chest(x, y)
                    break

    def generate_enemies(self, count, player_x, player_y):
        for _ in range(count):
            while True:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)

                if (x, y) != (player_x, player_y) and self.grid[y][x] == ".":
                    self.place_enemy(x, y)
                    break

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
                    # hráč červeně
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
                        print("\033[92m#\033[0m", end=" ")  # zelená stěna
                    elif char == "E":
                        print("\033[91mE\033[0m", end=" ")  # nepřítel červeně
                    elif char == "^":
                        print("\033[38;5;208m^\033[0m", end=" ")
                    elif char == "▣":
                        print("\033[38;5;94m▣\033[0m", end=" ")
                    else:
                        print(".", end=" ")

            print()

    @staticmethod
    def handle_tile(game_map, x, y, player, combat_function):
        messages = []
        status = None  # defaultně žádný stav

        tile = game_map.grid[y][x]

        if tile == "E":
            enemies = create_enemy_group()
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
            loot_options = [gear.sword, gear.shield,
                            gear.mace, gear.poison_dagger, gear.proboscis]
            loot = random.choice(loot_options)
            player.inventory.append(loot)
            messages.append(f"Otevřel jsi truhlu a našel: {loot.name}")
            game_map.grid[y][x] = "."

        return status, messages


def show_inventory(player):
    while True:
        clear_screen()

        print("\n=== INVENTÁŘ ===")

        print("\nVybavené:")
        for slot, items in player.slots.items():
            for i, item in enumerate(items):
                name = item.name if item else "\033[90mPrázdné\033[0m"
                print(f"{slot} [{i}]: {name}")

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
            for card in eq.cards:
                parts = []
                if card.damage:
                    parts.append(f"DMG:{card.damage}")
                if card.block:
                    parts.append(f"BLOCK:{card.block}")
                if card.lifesteal:
                    parts.append(f"LIFESTEAL:{card.lifesteal}")
                if card.draw:
                    parts.append(f"DRAW:{card.draw}")
                if card.discard:
                    parts.append(f"DRAW:{card.discard}")
                if card.effect:
                    chance = getattr(card, "effect_chance", 1.0)
                    parts.append(
                        f"EFFECT:{card.effect.name} ({int(chance*100)}%)")
                if card.cost:
                    parts.append(f"COST:{card.cost}")
                stats = ", ".join(parts)
                print(f"  - {card.name} ({stats})")
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
            slot = input("Slot (hand/body/belt/pocket/neck): ")
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

            for slot, items in player.slots.items():
                for eq in items:
                    if eq:  # pokud je něco vybavené
                        deck_exists = True
                        print(f"\n--- {eq.name} ---")
                        for card in eq.cards:
                            parts = []
                            if card.damage:
                                parts.append(f"DMG:{card.damage}")
                            if card.block:
                                parts.append(f"BLOCK:{card.block}")
                            if card.lifesteal:
                                parts.append(f"LIFESTEAL:{card.lifesteal}")
                            if card.draw:
                                parts.append(f"DRAW:{card.draw}")
                            if card.discard:
                                parts.append(f"DRAW:{card.discard}")
                            if card.effect:
                                chance = getattr(card, "effect_chance", 1.0)
                                parts.append(
                                    f"EFFECT:{card.effect.name} ({int(chance*100)}%)")
                            if card.cost:
                                parts.append(f"COST:{card.cost}")
                            stats = ", ".join(parts)
                            print(f"  - {card.name} ({stats})")

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
            "equipment": [gear.sword]
        },
        "Vrah": {
            "hp": 10,
            "equipment": [gear.poison_dagger]
        },
        "Strážce": {
            "hp": 16,
            "equipment": [gear.sword, gear.shield]
        },
        "Obří komár": {
            "hp": 5,
            "equipment": [gear.proboscis, gear.wings]
        }
    }

    template = enemy_types[name]

    enemy = Character(name, template["hp"])
    for item in template["equipment"]:
        enemy.equip_item(item)
    enemy.build_deck()

    return enemy


def create_enemy_group():
    encounter_types = [
        {
            "type": "komáři",
            "enemy": "Obří komár",
            "min": 1,
            "max": 3
        },
        {
            "type": "goblini",
            "enemy": "Goblin",
            "min": 1,
            "max": 2
        },
        {
            "type": "strážci",
            "enemy": "Strážce",
            "min": 1,
            "max": 2
        },
        {
            "type": "vrazi",
            "enemy": "Vrah",
            "min": 1,
            "max": 2
        }
    ]

    encounter = random.choice(encounter_types)

    count = random.randint(encounter["min"], encounter["max"])

    enemies = []
    for _ in range(count):
        enemies.append(create_enemy_by_name(encounter["enemy"]))

    print(f"Narazil jsi na skupinu: {encounter['type']} ({count}x)")

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
    def __init__(self, name, hp, síla=0):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.síla = síla

        self.block = 0
        self.status_effects = []

        self.slots = {
            "hand": [None, None],
            "body": [None],
            "belt": [None, None],
            "pocket": [None, None, None],
            "neck": [None]
        }
        self.inventory = []
        self.equipment = []

        self.deck = []
        self.hand = []
        self.discard = []

    def build_deck(self):
        self.deck = []

        for slot_list in self.slots.values():
            for item in slot_list:
                if item:
                    self.deck.extend(item.cards)

        random.shuffle(self.deck)

    def draw(self, n=3):
        for _ in range(n):
            if not self.deck:
                self.deck = self.discard
                self.discard = []
                random.shuffle(self.deck)

            if self.deck:
                self.hand.append(self.deck.pop())

    def play_card(self, index, target):
        card = self.hand.pop(index)
        card.play(self, target)
        self.discard.append(card)

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
                    f"{self.name} dostal {amount} dmg (ignoruje armor) (HP: {self.hp})")
            return amount

        reduced = max(amount - self.block, 0)
        self.block = max(self.block - amount, 0)
        self.hp -= reduced

        if not suppress_print:
            print(f"{self.name} dostal {reduced} dmg (HP: {self.hp})")
        return reduced

    def equip_item(self, item):
        slots = self.slots[item.slot_type]

        for i in range(len(slots)):
            if slots[i] is None:
                slots[i] = item

                if item in self.inventory:
                    self.inventory.remove(item)

                print(f"{self.name} vybavil {item.name}")
                return True

        print("Není volný slot")
        return False

    def unequip_item(self, slot_type, index):
        item = self.slots[slot_type][index]

        if item:
            self.inventory.append(item)
            self.slots[slot_type][index] = None
            print(f"{self.name} sundal {item.name}")
        else:
            print("Slot je prázdný")

    def reset_combat(self):
        self.deck = []
        self.hand = []
        self.discard = []
        self.status_effects = []
        self.block = 0

    def add_block(self, amount):
        self.block += amount
        print(f"{self.name} získal {amount} block")

    def apply_effect(self, effect):
        self.effects.append(effect)
        effect.apply(self)

    def is_stunned(self):
        return any(isinstance(e, core.Stun) for e in self.status_effects)

    def show_hand(self):
        print("\nTvoje karty:")
        for i, card in enumerate(self.hand):
            parts = []

            if card.damage:
                parts.append(f"DMG: {card.damage}")

            if card.block:
                parts.append(f"BLOCK: {card.block}")

            if card.effect:
                parts.append(f"EFFECT: {card.effect.name}")

            if card.cost:
                parts.append(f"COST: {card.cost}")

            stats = ", ".join(parts)

            print(f"{i}: {card.name} ({stats})")

    def player_turn(player, enemies):
        energy = 2

        while energy > 0 and player.hand:
            player.show_hand()

            choice = input("Vyber kartu (číslo nebo ENTER pro konec): ")

            if choice == "":
                break

            if not choice.isdigit():
                print("Neplatná volba")
                continue

            index = int(choice)

            if index < 0 or index >= len(player.hand):
                print("Neplatná karta")
                continue

            card = player.hand[index]

            if card.cost > energy:
                print("Nedostatek energie")
                continue

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

            energy -= card.cost

            # kontrola smrti všech enemy
            if all(e.hp <= 0 for e in enemies):
                return "enemy_dead"

            if player.hp <= 0:
                return "player_dead"

            print(f"Zbývá energie: {energy}")

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
        print(f"- {player.name} (HP: {player.hp}, Block: {player.block})")
        print("\nNepřátelé:")
        for e in enemies:
            if e.hp > 0:
                print(f"- {e.name} (HP: {e.hp}, Block: {e.block})")

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
                return True
            elif result == "player_dead":
                print("Prohrál jsi!")
                return False
        print(" ")

        # ===== ENEMY =====
        for enemy in enemies:
            enemy.block = 0
        for enemy in enemies:
            if enemy.hp <= 0:
                continue

            if enemy.is_stunned():
                print(f"{enemy.name} je omráčen!")
                enemy.process_status()
                continue

            enemy.process_status()
            enemy.draw(1)

            if enemy.hand:
                enemy.play_card(0, player)

            if player.hp <= 0:
                print("Prohrál jsi!")
                return False

        input("Stiskni cokoliv pro vstup do dalšího kola:")


# ===== MAIN LOOP ========
player = Character("Hráč", 20)
player.equipment = [gear.mace, gear.shield_with_spike,
                    gear.leather_armor, gear.abakus]
player.equip_item(gear.mace)
player.equip_item(gear.shield)
player.equip_item(gear.leather_armor)
player.equip_item(gear.abakus)


game_map = GameMap(20, 20)
rooms = game_map.generate_dungeon()
player_x, player_y = rooms[0].center()
game_map.generate_enemies_in_corridors(5, player_x, player_y)
game_map.generate_objects(2, 2, player_x, player_y,)

while player.hp > 0:
    clear_screen()

    GameMap.update_visibility(game_map, player_x, player_y)
    GameMap.draw_map(game_map, player_x, player_y)

    print(f"\nHP: {player.hp}")

    cmd = input("Pohyb (WASD, q = konec, i = inventář): ").lower()

    if cmd == "q":
        break
    elif cmd == "i":
        show_inventory(player)
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
