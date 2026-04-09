from core import Ability, Card

pain_for_all = Ability(
    name="Bolest pro všechny",
    description="Odemyká kartu:",
    ability_type="card",
    cards=[
        Card("Bolest pro všechny", damage=6,
             self_damage=3, target_type="all_enemies")
    ]
)

power_strike = Ability(
    name="Silný útok",
    description="Odemyká kartu:",
    ability_type="card",
    cards=[
        Card("Silný úder", damage=6)
    ]
)

fast_strike = Ability(
    name="Rychlý útok",
    description="Odemyká kartu:",
    ability_type="card",
    cards=[
        Card("Rychlý úder", damage=4, cost=0)
    ]
)

defensive_strike = Ability(
    name="Útok do obrany",
    description="Odemyká kartu:",
    ability_type="card",
    cards=[
        Card("Útok a kryt", damage=4, block=4)
    ]
)

no_rest = Ability(
    name="Bez odpočinku",
    description="Odemyká kartu, která po zahrátí přidá energii:",
    ability_type="card",
    cards=[
        Card("Bez odpočinku", energy=1, target_type="self", cost=0)
    ]
)


def bonus_strength(player):
    player.strenght += 1


muscles = Ability(
    name="Svaly",
    description="+1 k síle",
    ability_type="passive",
    effect=bonus_strength,
    trigger="on_acquire"
)


def refreshing_armor(player):
    player.block += 1


hard_root = Ability(
    name="Tuhý kořínek",
    description="každé kolo získáš 1 block",
    ability_type="passive",
    effect=refreshing_armor,
    trigger="per_turn"
)


def draw_on_third_attack(player):
    if player.attack_cards_played >= 3:
        player.draw(1)
        player.attack_cards_played = 0  # reset counter


three_attack_draw = Ability(
    name="Rytmus boje",
    description="Za každou třetí útočnou kartu, kterou zahraješ si lízneš kartu.",
    ability_type="passive",
    effect=draw_on_third_attack,
    trigger="on_attack_played"
)


def keep_defense(character):
    if character.block > 0:
        character.saved_block = min(character.block, 2)
    else:
        character.saved_block = 0

    return character.saved_block


maintaining_defense = Ability(
    name="Zachování obrany",
    description="Pokud při vstupu do dalšího kola máš nějaký block, nejvýše dva body se ti z něj zachvají.",
    ability_type="passive",
    effect=keep_defense,
    trigger="after_opponent_turn"
)
