import random


class Card:
    def __init__(self, name, damage=0, block=0, effect=None, effect_chance=1.0,
                 effect_on_damage=False, lifesteal=0, target_type="enemy", draw=0, discard=0, cost=1):
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
        self.cost = cost

    def play(self, user, target):
        print(f"{user.name} používá {self.name}")

        dmg_done = 0
        total_damage = self.damage + getattr(user, "strength", 0)
        if total_damage:
            dmg_done = target.take_damage(total_damage)

        if self.block:
            user.add_block(self.block)

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
                for i, card in enumerate(user.hand):
                    print(f"{i}: {card.name}")
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

    def apply(self, target):
        dmg_done = target.take_damage(
            self.damage_per_turn,
            ignore_armor=True,
            suppress_print=True  # tisk jen zde
        )
        print(
            f"{target.name} trpí otravou a obdržel {dmg_done} dmg (armor ignorován) - (HP: {target.hp}).")

    def copy(self):
        return Poison(self.damage_per_turn, self.duration)


class Stun(Status_Effect):
    def __init__(self, duration):
        super().__init__("Omráčení", duration)

    def copy(self):
        return Stun(self.duration)


class Dodge(Status_Effect):
    def __init__(self, chance, duration=1):
        super().__init__("Úhyb", duration)
        self.chance = chance

    def copy(self):
        return Dodge(self.chance, self.duration)


class Equipment:
    def __init__(self, name, slot_type, cards):
        self.name = name
        self.slot_type = slot_type
        self.cards = cards
