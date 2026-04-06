import random
import core
from core import Colors, clear_screen, shuffle_deck, format_status_effects

class Character:
    def __init__(self, name, hp, strenght=0, temporary_strenght=0, max_energy=2):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.strenght = strenght
        self.temporary_strenght = temporary_strenght
        
        self.saved_block = 0
        self.combo_count = 0
        self.energy = max_energy

        self.block = 0
        self.abilities = []
        self.status_effects = []

        # pomocné proměnné pro ability
        self.attack_cards_played = 0

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

        # --- ITEMY ---
        for slot_list in self.slots.values():
            for item in slot_list:
                if not item:
                    continue

                if item.two_handed:
                    if id(item) in added_items:
                        continue
                    added_items.add(id(item))

                self.deck.extend(item.cards)

        # --- SYNERGIE ---
        equipment_names = [item.name for slot in self.slots.values()
                           for item in slot if item]

        for synergy in core.SYNERGIES:
            if all(req in equipment_names for req in synergy["requires"]):
                self.deck.extend(synergy["cards"])

        # --- ABILITIES ---
        for ability in self.abilities:
            if getattr(ability, "active", True) and ability.type == "card":
                self.deck.extend(ability.cards)

        random.shuffle(self.deck)

    def is_level_up(self):
        if self.xp >= self.lvl*5:
            self.xp = self.xp - self.lvl*5
            return True
        return False

    def draw(self, n=3):
        for _ in range(n):
            if not self.deck:
                self.deck = self.discard
                self.discard = []
                shuffle_deck(self.deck, shuffler=self)

            if self.deck:
                self.hand.append(self.deck.pop())

    def discard_hand(self):
        self.discard.extend(self.hand)
        self.hand.clear()

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

    def take_damage(self, amount, attacker=None, ignore_armor=False, suppress_print=False):
        for effect in self.status_effects:
            if isinstance(effect, core.Dodge):
                if random.random() < effect.chance:
                    if not suppress_print:
                        print(f"{self.name} se vyhnul útoku!")
                    return 0

        if ignore_armor:
            reduced = amount
            self.hp -= amount
            if not suppress_print:
                print(f"{Colors.RED}{self.name} dostal {amount} dmg (ignoruje armor) (HP: {self.hp}{Colors.RESET})")
        else:
            reduced = max(amount - self.block, 0)
            self.block = max(self.block - amount, 0)
            self.hp -= reduced

            if not suppress_print:
                print(f"{Colors.RED}{self.name} dostal {reduced} dmg (HP: {self.hp}{Colors.RESET})")

        if attacker and reduced > 0:
            for effect in self.status_effects:
                if isinstance(effect, core.Thorns):
                    if random.random() < effect.chance:
                        attacker.hp -= effect.damage
                        #attacker.take_damage(effect.damage, suppress_print=True)
                        if not suppress_print:
                            print(f"{Colors.RED}{attacker.name} se při útoku poranil a dostal {effect.damage} dmg (HP: {attacker.hp}{Colors.RESET})")


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
        self.fatigue = 0
        self.attack_cards_played = 0

    def add_block(self, amount):
        self.block += amount
        print(f"{Colors.GRAY}{self.name} získal {amount} block{Colors.RESET}")

    def add_temporary_strenght(self, amount):
        self.temporary_strenght += amount
        print(f"{self.name} získal {amount} dočasné síly")

    def apply_effect(self, effect):
        self.status_effects.append(effect)
        effect.apply(self)

    def is_stunned(self):
        return any(isinstance(e, core.Stun) for e in self.status_effects)

    def show_hand(self):
        print("\nTvoje karty:")
        core.print_cards(self.hand)

    def has_playable_card(self):
        for card in self.hand:
            if card.cost <= self.energy:
                return True
        return False

    def player_turn(player, enemies):
        player.energy = player.max_energy
        player.energy -= player.reduced_energy
        player.reduced_energy = 0

        while player.hand and player.has_playable_card():
            clear_screen()

            print(f"\n{Colors.GREEN}--- Tvůj tah ---{Colors.RESET}")
            print(
                f"- {player.name} (HP: {player.hp}, {Colors.GRAY}Block: {player.block}{Colors.RESET}, Energy: {player.energy}"
                + (f", Total_strenght: {player.strenght + player.temporary_strenght}"
                   if (player.strenght + player.temporary_strenght) != 0 else "")
                + (f", Combo: {player.combo_count}"if (player.combo_count) != 0 else "")
                + f"){format_status_effects(player)}"
            )

            print("\nNepřátelé:")
            for e in enemies:
                if e.hp > 0:
                    print(
                        f"- {e.name} (HP: {e.hp}, {Colors.GRAY}Block: {e.block}{Colors.RESET}"
                        + (f", Total_strenght: {e.strenght + e.temporary_strenght}"
                           if (e.strenght + e.temporary_strenght) != 0 else "")
                        + f"){format_status_effects(e)}"
                    )

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
                if self.hp > 0:
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

