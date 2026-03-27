import random


class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"
    RESET = "\033[0m"


class Card:
    def __init__(self, name, damage=0, block=0, effect=None, effect_chance=1.0,
                 effect_on_damage=False, lifesteal=0, target_type="enemy",
                 spawn_enemy=None, spawn_count=0, draw=0, discard=0, buff_strenght=0, cost=1):
        self.name = name
        self.damage = damage
        self.block = block
        self.effect = effect
        self.effect_chance = effect_chance
        self.effect_on_damage = effect_on_damage
        self.lifesteal = lifesteal
        self.target_type = target_type
        self.draw = draw
        self.discard = discard
        self.spawn_enemy = spawn_enemy
        self.spawn_count = spawn_count
        self.buff_strenght = buff_strenght
        self.cost = cost

    def play(self, user, target, enemies_list=None, create_enemy_func=None):
        print(f"{user.name} používá {self.name}")

        dmg_done = 0
        if getattr(self, "damage", 0) > 0:
            total_damage = self.damage + \
                getattr(user, "strenght", 0) + \
                getattr(user, "temporary_strenght", 0)
            dmg_done = target.take_damage(total_damage)

        if self.spawn_enemy and enemies_list is not None and create_enemy_func is not None:
            for _ in range(self.spawn_count):
                new_enemy = create_enemy_func(self.spawn_enemy)
                enemies_list.append(new_enemy)
            print(
                f"{user.name} vyvolal nepřítele: {self.spawn_count} x {new_enemy.name}!")

        if self.block:
            user.add_block(self.block)

        if self.buff_strenght:
            user.add_temporary_strenght(self.buff_strenght)

        if self.lifesteal > 0 and dmg_done > 0:
            heal_amount = int(dmg_done * self.lifesteal)
            user.hp = min(user.max_hp, user.hp + heal_amount)
            print(
                f"{user.name} se léčí o {heal_amount} HP díky lifestealu (HP: {user.hp})")

        if self.draw > 0:
            print(f"{user.name} dobral {self.draw} kartu/karty díky {self.name}")
            user.draw(self.draw)

        if self.discard > 0:
            for _ in range(self.discard):
                if not user.hand:
                    break

                print("\nAktuální ruka:")
                print_cards(user.hand)  # <-- tady nahradíme výpis názvů

                while True:
                    choice = input(
                        f"Vyber kartu k zahazení (0-{len(user.hand)-1}): ")
                    if choice.isdigit():
                        idx = int(choice)
                        if 0 <= idx < len(user.hand):
                            discarded = user.hand.pop(idx)
                            user.discard.append(discarded)
                            print(f"Zahodil jsi kartu: {discarded.name}")
                            break
                    print("Neplatná volba, zkus to znovu.")

        if self.effect:
            if getattr(self, "effect_on_damage", False) and dmg_done <= 0:
                print(
                    f"{target.name} nebyl zasažen, efekt {self.effect.name} se neuplatní.")
            else:
                if random.random() <= self.effect_chance:
                    copied_effect = self.effect.copy()

                    if self.target_type == "self":
                        user.status_effects.append(copied_effect)
                        print(f"{user.name} získal efekt: {copied_effect.name}")
                    else:
                        target.status_effects.append(copied_effect)
                        print(f"{target.name} získal efekt: {copied_effect.name}")

                    if isinstance(copied_effect, Stun):
                        copied_effect.apply(
                            target if self.target_type != "self" else user)
                else:
                    print(
                        f"{self.effect.name} se nepodařilo aplikovat ({int(self.effect_chance*100)}% šance)")


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
        dmg_done = target.take_damage(
            self.damage_per_turn,
            ignore_armor=True,
            suppress_print=True  # tisk jen zde
        )
        print(
            f"{Colors.RED}{target.name} trpí otravou a obdržel {dmg_done} dmg (armor ignorován) - (HP: {target.hp}{Colors.RESET}).")
        input("ENTER pro pokračování...")

    def copy(self):
        return Poison(self.damage_per_turn, self.duration)


class Stun(Status_Effect):
    def __init__(self, duration):
        super().__init__("Omráčení", duration)

    def description(self):
        return f"cíl nemůže hrát ({self.duration} kol)"

    def copy(self):
        return Stun(self.duration)


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
    if not cards:
        print("Žádné karty.")
        return

    for i, card in enumerate(cards):
        parts = []

        if card.damage:
            parts.append(f"DMG:{card.damage}")
        if card.block:
            parts.append(f"BLOCK:{card.block}")
        if card.lifesteal:
            parts.append(f"LIFESTEAL:{card.lifesteal}")
        if card.buff_strenght:
            parts.append(f"BUFF STRENGHT:{card.buff_strenght}")
        if card.effect:
            chance = getattr(card, "effect_chance", 1.0)
            effect_desc = card.effect.description()
            parts.append(
                f"EFFECT:{card.effect.name} ({int(chance*100)}%) - {effect_desc}")
        if getattr(card, "draw", 0):
            parts.append(f"DRAW:{card.draw}")
        if getattr(card, "discard", 0):
            parts.append(f"DISCARD:{card.discard}")
        if card.cost:
            parts.append(f"COST:{card.cost}")
        if getattr(card, "target_type", None) == "all_enemies":
            parts.append("AOE")

        stats = ", ".join(parts)
        print(f"{i}: {card.name} ({stats})")


SYNERGIES = [
    {
        "requires": ["Krátký Meč", "Štít"],
        "cards": [
            Card("Útok a kryt", damage=4, block=4, cost=1)
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
            Card("Stratéguv triumf", draw=3, cost=1)  # potom vylepšit
        ]
    },
]
