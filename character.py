import random
import core
from core import Colors, clear_screen, shuffle_deck, format_status_effects, print_center_block


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

        self.bestiary = {}

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

    def serialize_bestiary(self, bestiary):
        return {
            name: {
                "seen": data["seen"],
                "kills": data["kills"],
                "seen_cards": list(data.get("seen_cards", [])),
                "info": data.get("info", {}),
                "all_cards": data.get("all_cards", [])
            }
            for name, data in bestiary.items()
        }

    def to_dict(self):
        return {
            "name": self.name,

            "hp": self.hp,
            "max_hp": self.max_hp,

            "max_energy": self.max_energy,
            "extra_draw": self.extra_draw,
            "strenght": self.strenght,

            "player_class": getattr(self, "player_class", None),

            "xp": getattr(self, "xp", 0),
            "lvl": getattr(self, "lvl", 1),
            "dungeon_level": getattr(self, "dungeon_level", 1),

            "inventory": [item.name for item in self.inventory],
            "equipment": {slot: [item.name if item else None for item in items] for slot, items in self.slots.items()},
            "abilities": [a.name for a in self.abilities],

            "bestiary": self.serialize_bestiary(self.bestiary)
        }

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
        messages = []

        for _ in range(n):
            if not self.deck:
                self.deck = self.discard
                self.discard = []
                self.discard.clear()

                msgs = shuffle_deck(self.deck, shuffler=self)
                messages.extend(msgs)

            if self.deck:
                self.hand.append(self.deck.pop())

        return messages

    def discard_hand(self):
        self.discard.extend(self.hand)
        self.hand.clear()

    def apply_fatigue(self):
        if self.fatigue > 0:
            core.print_center_block(
                f"{self.name} cítí únavu a ztrácí {self.fatigue} HP!")
            input("ENTER pro pokračování...")
            self.take_damage(self.fatigue, ignore_armor=True,
                             suppress_print=True)

        self.fatigue += 1

    def play_card(self, index, target=None, enemies_list=None, create_enemy_func=None, player=None, render=None, padding=None):
        if 0 <= index < len(self.hand):
            card = self.hand.pop(index)

            card.play(
                user=self,
                target=target,
                enemies_list=enemies_list,
                create_enemy_func=create_enemy_func,
                player=player,
                render=render,
                padding=padding
            )
            self.discard.append(card)
        else:
            core.print_center_block("Neplatný index karty")

    def take_damage(self, amount, attacker=None, ignore_armor=False, suppress_print=False):
        messages = []

        for effect in self.status_effects:
            if isinstance(effect, core.Dodge):
                if random.random() < effect.chance:
                    if not suppress_print:
                        messages.append(
                            f"{self.name} se vyhnul útoku!")
                    return 0, messages #nevím jestli toto bude fungovat!!!

        if ignore_armor:
            reduced = amount
            self.hp -= amount
            if not suppress_print:
                messages.append(
                    f"{Colors.RED}{self.name} dostal {amount} dmg (ignoruje armor) (HP: {self.hp}{Colors.RESET})")
        else:
            reduced = max(amount - self.block, 0)
            self.block = max(self.block - amount, 0)
            self.hp -= reduced

            if not suppress_print:
                messages.append(f"{Colors.RED}{self.name} dostal {reduced} dmg (HP: {self.hp}{Colors.RESET})")

        if attacker and reduced > 0:
            for effect in self.status_effects:
                if isinstance(effect, core.Thorns):
                    if random.random() < effect.chance:
                        attacker.hp -= effect.damage
                        # attacker.take_damage(effect.damage, suppress_print=True)
                        if not suppress_print:
                            messages.append(
                                f"{Colors.RED}{attacker.name} se při útoku poranil a dostal {effect.damage} dmg (HP: {attacker.hp}{Colors.RESET})")

        return reduced, messages

    def equip_item(self, item, suppress_print=False):
        # pokud je obouruční, musí být volné **oba hand sloty**
        if item.slot_type == "hand" and getattr(item, "two_handed", False):
            if any(self.slots["hand"]):
                core.print_center_block(
                    "Potřebuješ volné oba hand sloty pro obouruční zbraň!")
                input("ENTER pro pokračování...")
                return False
            else:
                self.slots["hand"][0] = item
                self.slots["hand"][1] = item
                if item in self.inventory:
                    self.inventory.remove(item)
                core.print_center_block(
                    f"{self.name} vybavil obouruční zbraň {item.name}")
                return True

        # standardní logika pro jednoruké zbraně
        slots = self.slots[item.slot_type]
        for i in range(len(slots)):
            if slots[i] is None:
                slots[i] = item
                if item in self.inventory:
                    self.inventory.remove(item)
                if not suppress_print:
                    core.print_center_block(f"{self.name} vybavil {item.name}")
                return True

        core.print_center_block("Není volný slot")
        return False

    def unequip_item(self, slot_type, index):
        item = self.slots[slot_type][index]

        if item:
            # pokud je obouruční a slot je "hand", odeber oba sloty
            if slot_type == "hand" and getattr(item, "two_handed", False):
                for i in range(len(self.slots["hand"])):
                    if self.slots["hand"][i] == item:
                        self.slots["hand"][i] = None
                core.print_center_block(
                    f"{self.name} sundal obouruční zbraň: {item.name}")
            else:
                self.slots[slot_type][index] = None
                core.print_center_block(f"{self.name} sundal {item.name}")

            self.inventory.append(item)
        else:
            core.print_center_block("Slot je prázdný")

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
        return f"{Colors.GRAY}{self.name} získal {amount} block{Colors.RESET}"

    def add_temporary_strenght(self, amount):
        self.temporary_strenght += amount
        return f"{self.name} získal {amount} dočasné síly"

    def apply_effect(self, effect):
        self.status_effects.append(effect)
        effect.apply(self)

    def is_stunned(self):
        return any(isinstance(e, core.Stun) for e in self.status_effects)

    def get_hand_lines(self):
        return core.get_card_lines(self.hand)

    def has_playable_card(self):
        for card in self.hand:
            if card.cost <= self.energy:
                return True
        return False

    def player_turn(player, enemies):
        player.energy = player.max_energy
        player.energy -= player.reduced_energy
        player.reduced_energy = 0

        padding = None

        def render(lines, use_existing_padding=False):
            nonlocal padding

            if use_existing_padding and padding is not None:
                core.render_block(lines, forced_padding=padding)
            else:
                padding = core.get_padding(lines)
                core.render_block(lines, padding)

        while player.hand and player.has_playable_card():

            clear_screen()

            # =========================
            # UI BUILD
            # =========================
            lines = []

            core.print_center_block(f"{Colors.GREEN}--- Tvůj tah ---{Colors.RESET}")
            lines.append("")

            # ===== PLAYER =====
            p_line = (
                f"- {player.name} (HP: {player.hp}, "
                f"{Colors.GRAY}Block: {player.block}{Colors.RESET}, "
                f"Energy: {player.energy}"
            )

            total_str = player.strenght + player.temporary_strenght
            if total_str != 0:
                p_line += f", Total_strenght: {total_str}"

            if player.combo_count:
                p_line += f", Combo: {player.combo_count}"

            p_line += f"){format_status_effects(player)}"

            lines.append(p_line)
            lines.append("")
            lines.append("Nepřátelé:")

            # ===== ENEMIES =====
            for e in enemies:
                if e.hp > 0:
                    e_line = (
                        f"- {e.name} (HP: {e.hp}, "
                        f"{Colors.GRAY}Block: {e.block}{Colors.RESET}"
                    )

                    total_str = e.strenght + e.temporary_strenght
                    if total_str != 0:
                        e_line += f", Total_strenght: {total_str}"

                    e_line += f"){format_status_effects(e)}"
                    lines.append(e_line)

            lines.append("")
            lines.append(
                f"Deck: {len(player.deck)}, Discard: {len(player.discard)}")
            lines.append("")

            # ===== RENDER =====
            lines.append("")
            lines.append("Tvoje karty:")
            lines.extend(player.get_hand_lines())

            render(lines)

            choice = input("ENTER = ukončit tah, Vyber kartu: ")

            if choice == "":
                break

            if not choice.isdigit():
                render(["Neplatná volba"])
                input("ENTER...")
                continue

            index = int(choice) - 1 #kvůli výpisu pro uživatele, který začíná od 1

            if index < 0 or index >= len(player.hand):
                render(["Neplatná karta"])
                input("ENTER...")
                continue

            card = player.hand[index]

            if card.cost > player.energy:
                render(["Nedostatek energie"])
                input("ENTER...")
                continue

            # =========================
            # TARGET LOGIC
            # =========================
            if card.target_type == "enemy":
                alive = [e for e in enemies if e.hp > 0]

                if len(alive) == 1:
                    target = alive[0]
                else:
                    target = choose_enemy(enemies, render, padding)

                player.play_card(index, target, render=render, padding=padding)
                player.energy -= card.cost 


            elif card.target_type == "self":
                player.play_card(index, player, render=render, padding=padding)
                player.energy -= card.cost 


            elif card.target_type == "all_enemies":
                card_to_play = player.hand.pop(index)

                for e in enemies:
                    if e.hp > 0:
                        card_to_play.play(
                            user=player,
                            target=e,
                            enemies_list=enemies,
                            player=player
                        )
                player.energy -= card.cost 

                player.discard.append(card_to_play)

            # =========================
            # END CHECKS
            # =========================
            boss = next((e for e in enemies if e.is_boss), None)

            if player.hp <= 0:
                return False

            if boss:
                if boss.hp <= 0:
                    return True
            else:
                if all(e.hp <= 0 for e in enemies):
                    return True

            render([f"Zbývá energie: {player.energy}"], use_existing_padding=True)
            input("ENTER pro pokračování...")

        return None

    def process_status(self):
        messages = []

        for effect in self.status_effects:
            effect_msgs = effect.apply(self)
            if effect_msgs:
                messages.extend(effect_msgs)

        new_effects = []
        for effect in self.status_effects:
            if not effect.tick():
                new_effects.append(effect)
            else:
                if self.hp > 0:
                    messages.append(f"{self.name} se zbavil efektu {effect.name}.")

        self.status_effects = new_effects
        return messages


def choose_enemy(enemies, render, padding):
    alive = [e for e in enemies if e.hp > 0]

    if len(alive) == 1:
        return alive[0]

    lines = ["Vyber nepřítele:"]
    for i, e in enumerate(alive, 1):
        lines.append(f"{i}: {e.name} (HP: {e.hp})")

    core.print_center_block("\n".join(lines), padding)

    while True:
        choice = input("Vyber nepřítele: ")

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(alive):
                return alive[idx]

        core.print_center_block("Neplatná volba", padding)