import random
import os
import textwrap
import shutil
import re

ANSI_ESCAPE = re.compile(r'\033\[[0-9;]*m')

UI_WIDTH = 70

def get_padding(lines, min_width=60):
    term_width = shutil.get_terminal_size().columns
    max_len = max(visible_length(line) for line in lines)
    max_len = max(max_len, min_width)
    return max((term_width - max_len) // 2, 0)

def render_block(lines, forced_padding=None, min_width=60):
    term_width = shutil.get_terminal_size().columns

    if forced_padding is not None:
        padding = forced_padding
    else:
        max_len = max(visible_length(line) for line in lines)
        max_len = max(max_len, min_width)
        padding = max((term_width - max_len) // 2, 0)

    for line in lines:
        print(" " * padding + line)

    return padding

def print_center_block(text="", padding=None):
    width = shutil.get_terminal_size().columns
    lines = text.splitlines()

    if not lines:
        print()
        return

    if padding is None:
        max_len = max(visible_length(line) for line in lines)
        padding = max((width - max_len) // 2, 0)

    for line in lines:
        print(" " * padding + line)

    return padding

def centered_input(prompt):
    width = shutil.get_terminal_size().columns
    padding = width // 2 - len(prompt) // 2
    return input(" " * max(padding, 0) + prompt)

def visible_length(text):
    return len(ANSI_ESCAPE.sub('', text))


def clear_screen():
    # Windows
    if os.name == "nt":
        os.system("cls")
    # Linux / Mac
    else:
        os.system("clear")
    print("\n")
    print("\n")


def print_box(title, stats, description, width=60):
    lines = []

    lines.append("=" * width)
    lines.append(title.center(width))
    lines.append("=" * width)

    for stat in stats:
        wrapped = textwrap.wrap(stat, width)
        for line in wrapped:
            lines.append(line.ljust(width))

    lines.append("-" * width)

    wrapped_text = textwrap.wrap(description, width)
    for line in wrapped_text:
        lines.append(line.ljust(width))

    lines.append("=" * width)

    padding = get_padding(lines)
    render_block(lines, padding)


class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"
    DARK_RED = "\033[31m"
    RESET = "\033[0m"


class Ability:
    def __init__(self, name, description, ability_type, active=True, effect=None, trigger="passive", cards=None):
        self.name = name
        self.description = description
        self.type = ability_type  # "card" / "passive"
        self.effect = effect
        # "per_turn", "on_acquire", "manual", "start_of_combat", "on_attack_played"
        self.trigger = trigger
        self.active = active
        self.cards = cards or []
        self.used = False

    def apply(self, player):
        if self.effect:
            self.effect(player)

        player.abilities.append(self)


class Card:
    def __init__(self, name, damage=0, self_damage=0, block=0, energy=0, reduce_energy=0, effect=None, effect_chance=1.0,
                 effect_on_damage=False, lifesteal=0, devour=0, target_type="enemy", spawn_enemy=None,
                 spawn_count=0, draw=0, discard=0, buff_strenght=0, increase_fatigue=0, combo=0, scale=1, base=0, cost=1):

        self.name = name
        self.damage = damage
        self.self_damage = self_damage
        self.block = block
        self.energy = energy
        self.reduce_energy = reduce_energy
        self.effect = effect
        self.effect_chance = effect_chance
        self.effect_on_damage = effect_on_damage
        self.lifesteal = lifesteal
        self.devour = devour
        self.target_type = target_type
        self.draw = draw
        self.discard = discard
        self.spawn_enemy = spawn_enemy
        self.spawn_count = spawn_count
        self.buff_strenght = buff_strenght
        self.increase_fatigue = increase_fatigue

        self.combo = combo
        self.scale = scale
        self.base = base

        self.cost = cost

    def get_valid_targets(user, target_type, player, enemies):
        if target_type == "enemy":
            return [e for e in enemies if e.hp > 0]

        elif target_type == "ally":
            if user is player:
                return [player]
            else:
                return [e for e in enemies if e.hp > 0]

        elif target_type == "self":
            return [user]

        elif target_type == "any":
            return [player] + [e for e in enemies if e.hp > 0]

    def get_damage(self, user, target):
        # klasický damage
        if isinstance(self.damage, int):
            return self.damage

        if self.damage == "fatigue":
            base = getattr(self, "base", 0)
            scale = getattr(self, "scale", 1)
            fatigue = getattr(target, "fatigue", 0)
            return base + fatigue * scale

        if self.damage == "combo":
            base = getattr(self, "base", 0)
            scale = getattr(self, "scale", 1)
            return base + user.combo_count * scale

        return 0

    def get_draw(self, user):
        if isinstance(self.draw, int):
            return self.draw

        if self.draw == "combo":
            return user.combo_count  # nebo jiná logika

        return 0

    def get_block(self, user, target):
        if self.block == "fatigue":
            base = getattr(self, "base", 0)
            scale = getattr(self, "scale", 1)
            fatigue = getattr(target, "fatigue", 0)
            return base + fatigue * scale

        if isinstance(self.block, int):
            return self.block

        return 0

    def play(self, user, target, enemies_list=None, create_enemy_func=None, player=None, aoe=False, padding=None, render=None):

        lines = []

        def msg(text):
            lines.append(text)

        def render(lines, use_existing_padding=False):
            nonlocal padding

            if use_existing_padding and padding is not None:
                render_block(lines, forced_padding=padding)
            else:
                padding = get_padding(lines)
                render_block(lines, padding)

        lines.append(f"{user.name} používá {self.name}")

        if player and not getattr(user, "is_player", False):
            if user.name not in player.bestiary:
                player.bestiary[user.name] = {
                    "seen": True, "kills": 0, "seen_cards": set()}
            player.bestiary[user.name]["seen_cards"].add(self.name)

        dmg_done = 0
        base_damage = self.get_damage(user, target)

        if base_damage > 0:
            user.attack_cards_played += 1

            total_damage = base_damage + \
                getattr(user, "strenght", 0) + \
                getattr(user, "temporary_strenght", 0)

            dmg_done, dmg_msgs = target.take_damage(total_damage, attacker=user)

            lines.extend(dmg_msgs)

            for ability in user.abilities:
                if ability.type == "passive" and ability.trigger == "on_attack_played" and ability.active:
                    ability.effect(user)

        if self.self_damage:
            user.hp -= self.self_damage
            msg(f"{Colors.RED}{user.name} si způsobil zranění za {self.self_damage} (HP: {user.hp}{Colors.RESET})")

        if self.spawn_enemy and enemies_list is not None and create_enemy_func is not None:
            for _ in range(self.spawn_count):
                new_enemy = create_enemy_func(self.spawn_enemy)
                enemies_list.append(new_enemy)
            msg(f"{user.name} vyvolal nepřítele: {self.spawn_count} x {new_enemy.name}!")

        if self.block:
            block_value = self.get_block(user, target)
            if self.target_type == "ally":
                msg(target.add_block(block_value))
            else:
                msg(user.add_block(block_value))

        if self.combo:
            user.combo_count += self.combo

        if self.energy:
            user.energy += self.energy

        if self.reduce_energy:
            target.reduced_energy += self.reduce_energy
            msg(f"{target.name} byl na nadcházející kolo připraven o {self.reduce_energy} energii/e")

        if self.increase_fatigue:
            target.fatigue += self.increase_fatigue
            msg(f"{target.name} cítí únavu (aktuální únava: {target.fatigue})")

        if self.buff_strenght:
            if self.target_type == "all_enemies":
                for e in enemies_list:
                    if e != user and e.hp > 0:
                        e.add_temporary_strenght(self.buff_strenght)
            else:
                user.add_temporary_strenght(self.buff_strenght)

        if self.lifesteal > 0 and dmg_done > 0:
            heal_amount = int(dmg_done * self.lifesteal)
            user.hp = min(user.max_hp, user.hp + heal_amount)
            msg(f"{user.name} se léčí o {heal_amount} HP díky lifestealu (HP: {user.hp})")

        if self.devour > 0:
            for _ in range(self.devour):
                if not target.discard:
                    break
                removed_card = target.discard.pop(
                    random.randint(0, len(target.discard)-1))
                msg(f"Karta {removed_card.name} byla dočasně odstraněna z {target.name}ova odhazovacího balíčku")

        draw_amount = self.get_draw(user)
        if draw_amount > 0:
            msg(f"{user.name} dobral {draw_amount} kartu/karty díky {self.name}")
            user.draw(draw_amount)

        if self.discard > 0 and not aoe:
            if not user.hand:
                msg("Nemáš žádné karty k zahození.")
            else:
                for _ in range(self.discard):
                    if not user.hand:
                        msg("Došly ti karty k zahození.")
                        break

                    discard_lines = []
                    discard_lines.append("Aktuální ruka:")
                    discard_lines.extend(get_card_lines(user.hand))

                    if render:
                        render(discard_lines, use_existing_padding=True)
                    else:
                        print_center_block("\n".join(discard_lines), padding)

                    #input taky centrovaný
                    choice = input(
                        f"Vyber kartu k zahození (0-{len(user.hand)-1}): "
                    )

                    if choice.isdigit():
                        idx = int(choice)
                        if 0 <= idx < len(user.hand):
                            discarded = user.hand.pop(idx)
                            user.discard.append(discarded)
                            msg(f"Zahodil jsi kartu: {discarded.name}")
                            break

        if self.effect:
            if getattr(self, "effect_on_damage", False) and dmg_done <= 0:
                msg(f"{target.name} nebyl zasažen, efekt {self.effect.name} se neuplatní.")
            else:
                if random.random() <= self.effect_chance:
                    copied_effect = self.effect.copy()

                    if self.target_type == "self":
                        user.status_effects.append(copied_effect)
                        msg(f"{user.name} získal efekt: {copied_effect.name}")
                    else:
                        target.status_effects.append(copied_effect)
                        msg(f"{target.name} získal efekt: {copied_effect.name}")

                    if isinstance(copied_effect, Stun):
                        copied_effect.apply(
                            target if self.target_type != "self" else user)
                else:
                    msg(f"{self.effect.name} se nepodařilo aplikovat ({int(self.effect_chance*100)}% šance)")

        render(lines, use_existing_padding=True)

def shuffle_deck(deck, shuffler):
    random.shuffle(deck)

    messages = []

    if hasattr(shuffler, "is_player") and shuffler.is_player:
        if hasattr(shuffler, "fatigue") and shuffler.fatigue > 0:
            messages.append(
                f"{Colors.RED}{shuffler.name} cítí únavu a ztrácí {shuffler.fatigue} HP!{Colors.RESET}"
            )
            shuffler.hp -= shuffler.fatigue

        shuffler.fatigue += 1

    return messages

def format_status_effects(character):
    if not character.status_effects:
        return ""

    effects = []
    for effect in character.status_effects:
        effects.append(f"{effect.name}({effect.duration})")

    return " | " + ", ".join(effects)


class Status_Effect:
    def __init__(self, name, duration):
        self.name = name
        self.duration = duration

    def description(self):
        return f"{self.name} ({self.duration} kol)"

    def apply(self, target):
        """Přepis v podtřídách pro konkrétní efekt"""
        pass

    def tick(self):
        self.duration -= 1
        return self.duration <= 0

    def copy(self):
        return type(self)(**self.__dict__)


class Poison(Status_Effect):
    def __init__(self, damage_per_turn, duration):
        super().__init__("Otrava", duration)
        self.damage_per_turn = damage_per_turn

    def description(self):
        return f"{self.damage_per_turn} dmg/kol po dobu {self.duration} kol"

    def apply(self, target):
        dmg_done, msgs = target.take_damage(
            self.damage_per_turn,
            ignore_armor=True,
            suppress_print=True
        )

        messages = []

        messages.append(
            f"{Colors.RED}{target.name} trpí otravou a obdržel {dmg_done} dmg (block ignorován) (HP: {target.hp}){Colors.RESET}"
        )

        # případné další zprávy (např. thorns apod.)
        messages.extend(msgs)

        return messages

    def copy(self):
        return Poison(self.damage_per_turn, self.duration)


class Stun(Status_Effect):
    def __init__(self, duration):
        super().__init__("Omráčení", duration)

    def description(self):
        return f"cíl nemůže hrát ({self.duration} kol)"

    def copy(self):
        return Stun(self.duration)


class Thorns(Status_Effect):
    def __init__(self, chance, damage, duration=1):
        super().__init__("Trny", duration)
        self.damage = damage
        self.chance = chance

    def description(self):
        return f"({self.duration} kola) {int(self.chance*100)}% šance způsobit útočníkovi ({self.damage}) poškození."

    def copy(self):
        return Thorns(self.chance, self.damage, self.duration)


class Dodge(Status_Effect):
    def __init__(self, chance, duration=1):
        super().__init__("Úhyb", duration)
        self.chance = chance

    def description(self):
        return f"{int(self.chance*100)}% šance vyhnout se útoku ({self.duration} kol)"

    def copy(self):
        return Dodge(self.chance, self.duration)


class Equipment:
    def __init__(self, name, slot_type, cards, two_handed=False):
        self.name = name
        self.slot_type = slot_type
        self.two_handed = two_handed
        self.cards = cards

def print_cards(cards):
    lines = get_card_lines(cards)
    for line in lines:
        print_center_block(line)

def get_card_lines(cards):
    if not cards:
        return ["Žádné karty."]

    lines = [""]

    for i, card in enumerate(cards, 1):

        parts = []

        # ===== DAMAGE =====
        if card.damage:
            if isinstance(card.damage, int):
                dmg_str = str(card.damage)
            else:
                base = getattr(card, "base", 0)
                scale = getattr(card, "scale", 1)

                if base == 0 and scale == 1:
                    dmg_str = f"{card.damage}"
                elif base == 0:
                    dmg_str = f"combo*{scale}"
                elif scale == 0:
                    dmg_str = f"{base}"
                else:
                    dmg_str = f"{base} + combo*{scale}"

            parts.append(f"DMG:{dmg_str}")

        # ===== OTHER STATS =====
        if card.self_damage:
            parts.append(f"SELF DMG:{card.self_damage}")

        if card.block:
            parts.append(f"BLOCK:{card.block}")

        if card.lifesteal:
            parts.append(f"LIFESTEAL:{card.lifesteal}")

        if card.energy:
            parts.append(f"ENERGY:+{card.energy}")

        if card.buff_strenght:
            parts.append(f"BUFF STRENGTH:{card.buff_strenght}")

        if card.effect:
            chance = getattr(card, "effect_chance", 1.0)
            effect_desc = card.effect.description()
            parts.append(
                f"EFFECT:{card.effect.name} ({int(chance*100)}%) - {effect_desc}"
            )

        if getattr(card, "draw", 0):
            parts.append(f"DRAW:{card.draw}")

        if getattr(card, "discard", 0):
            parts.append(f"DISCARD:{card.discard}")

        if getattr(card, "target_type", None) == "all_enemies":
            parts.append("AOE")

        if card.combo:
            parts.append(f"COMBO:{card.combo}")

        parts.append(f"COST:{card.cost}")

        stats = ", ".join(parts)

        lines.append(f"{i}: {card.name} ({stats})")

    return lines

SYNERGIES = [
    {
        "requires": ["Krátký Meč", "Štít s bodcem"],
        "cards": [
            Card("Útok a kryt", damage=4, block=4)
        ]
    },
    {
        "requires": ["Řemdich", "Štít"],
        "cards": [
            Card("Rozmáchnutí zpoza krytu", damage=2,
                 block=1, target_type="all_enemies")
        ]
    },
    {
        "requires": ["Krátký Meč", "Štít"],
        "cards": [
            Card("Útok a kryt", damage=4, block=4)
        ]
    },
    {
        "requires": ["Krátký Meč", "Dýka"],
        "cards": [
            Card("Obranné postavení", block=4, cost=0)
        ]
    },
    {
        "requires": ["Abakus", "Bitevní plány"],
        "cards": [
            Card("Stratéguv triumf", draw=3)  # potom vylepšit
        ]
    },
    {
        "requires": ["Prstenočerv", "Mravenec"],
        "cards": [
            Card("Požehnání malých", effect=Dodge(0.3, 3),
                 target_type="self")  # potom vylepšit
        ]
    },
]
