from core import Card, Stun, Poison, Dodge, Equipment

# ===== Zbraně =====
sword = Equipment("Krátký Meč", "hand", [
    Card("Píchnutí", damage=2),
    Card("Bodnutí", damage=3),
    Card("Bodnutí", damage=3),
    Card("Seknutí", damage=4),
])

mace = Equipment("Palice", "hand", [
    Card("Slabý úder", damage=4),
    Card("Úder", damage=5),
    Card("Silný úder", damage=6, cost=2),
    Card("Omračovací úder", damage=3, effect=Stun(1),
         effect_chance=0.6, effect_on_damage=True),
])

poison_dagger = Equipment("Otrávená dýka", "hand", [
    Card("Jedovaté bodnutí", damage=2,
         effect=Poison(2, 3), effect_on_damage=True),
    Card("Bodnutí", damage=3)
])

proboscis = Equipment("Sosák", "hand", [
    Card("Píchnutí", damage=2),
    Card("Sátí krve", damage=2, lifesteal=1),
    Card("Sátí krve", damage=2, lifesteal=1),
    Card("Hladové sátí", damage=3, lifesteal=1.5)
])

# ===== Štíty =====
shield = Equipment("Štít", "hand", [
    Card("Blok", block=2, target_type="self"),
    Card("Blok", block=2, target_type="self"),
])

shield_with_spike = Equipment("Štít s bodcem", "hand", [
    Card("Blok", block=2, target_type="self"),
    Card("Blok s bodcem", block=2, damage=2),
])


# ===== Zbroje =====
leather_armor = Equipment("Kožená zbroj", "body", [
    Card("Pokrytí", block=3, target_type="self"),
    Card("Pokrytí", block=3, target_type="self"),
])

# ===== Monstra =====
wings = Equipment("Hmyzí křídla", "body", [
    Card("Poletování", effect=Dodge(0.5, 2), target_type="self"),
    Card("Poletování", effect=Dodge(0.5, 2), target_type="self")
])

# ===== pomocné karty =====

# ===== artefakty =====
amulet_of_defense = Equipment("Talisman ochrany", "neck", [
    Card("Bariera", block=4, target_type="self")
])
