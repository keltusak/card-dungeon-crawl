from core import Ability, Card

power_strike = Ability(
    name="Silný útok",
    description="Získáš silnější útočnou kartu",
    ability_type="card",
    cards=[
        Card("Silný úder", damage=8)
    ]
)
fast_strike = Ability(
    name="Rychlý útok",
    description="Získáš kartu za 0 energie",
    ability_type="card",
    cards=[
        Card("Rychlý úder", damage=3, cost=0)
    ]
)
defensive_strike = Ability(
    name="Útok do obrany",
    description="Získáš útok poskytující i obranu",
    ability_type="card",
    cards=[
        Card("Rychlý úder", damage=4, block=4)
    ]
)


def bonus_strength(player):
    player.strenght += 1


muscles = Ability(
    name="Svaly",
    description="+1 k síle",
    ability_type="passive",
    effect=bonus_strength
)
