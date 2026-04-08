from core import Card, Stun, Poison, Dodge, Thorns, Equipment
from character import Character

# ===== Zbraně =====

wooden_staff= Equipment("Dřevěná hůl", "hand", [
    Card("Krytí", block=3, target_type="self"),
    Card("Krytí", block=3, target_type="self"),
    Card("Úder a kryt", damage=2, block=3),
    Card("Podražení nohou", damage=2, effect=Stun(1),
         effect_chance=0.4, effect_on_damage=True),
])

dagger = Equipment("Dýka", "hand", [
    Card("Bodnutí", damage=3),
    Card("Podlé bodnutí", damage=4, cost=0)
])

sword = Equipment("Krátký Meč", "hand", [
    Card("Škrábnutí", damage=2),
    Card("Bodnutí", damage=3),
    Card("Seknutí", damage=4),
    Card("Seknutí", damage=4),
])

broken_sword = Equipment("Poškozený Meč", "hand", [
    Card("Tupé ostří", damage=2),
    Card("Tupé ostří", damage=2),
    Card("Bodnutí", damage=3),
    Card("Seknutí", damage=4),
])

flail = Equipment("Řemdich", "hand", [
    Card("Švih", damage=3),
    Card("Švih", damage=3),
    Card("Rozmáchnutí", damage=2, target_type="all_enemies"),
    Card("Vyčerpávající švih", damage=6, discard=1),
])

battle_axe = Equipment("Bitevní sekera", "hand", [
    Card("Seknutí", damage=4),
    Card("Seknutí", damage=4),
    Card("Rozseknutí", damage=5),
    Card("Široký sek", damage=3, target_type="all_enemies"),
    Card("Drtivý úder", damage=7, cost=2),
], two_handed=True)

mace = Equipment("Palice", "hand", [
    Card("Slabý úder", damage=4),
    Card("Úder", damage=5),
    Card("Úder", damage=5),
    Card("Silný úder", damage=6, cost=2),
    Card("Omračovací úder", damage=3, effect=Stun(1),
         effect_chance=0.6, effect_on_damage=True),
], two_handed=True)

poison_dagger = Equipment("Otrávená dýka", "hand", [
    Card("Jedovaté bodnutí", damage=2,
         effect=Poison(2, 2), effect_on_damage=True),
    Card("Bodnutí", damage=3)
])

cultistic_blade = Equipment("Kultistovo ostří", "hand", [
    Card("Zářez", damage=2, combo=True ),
    Card("Zářez", damage=2, combo=True ),
    Card("Rituál", damage=2, energy=1, combo=True, target_type="self", cost=0),
    Card("Setnutí", damage="combo", scale=2),
])
# ====== nové karty k přidání do aktuální verze pro Kultistku a Mága =======
bloodthirsty_tongue = Equipment("Krvežíznivý jazyk", "hand", [
    Card("Zářez", damage=2, combo=1 ),
    Card("Sátí", damage=2, lifesteal=1, combo=1 ),
    Card("Krvavá daň", self_damage=3, combo=3, cost=0),
    Card("Žízeň", damage="combo", lifesteal=1, scale=1, cost=2)
])

claw_dagger = Equipment("Dýka z drápu", "hand", [
    Card("Bodnutí", damage=3, combo=1),
    Card("Rituál", damage=1, energy=1, combo=1, target_type="self", cost=0),
])

sacrificial_blade = Equipment("Obětní čepel", "hand", [
    Card("Řez do masa", damage=3, combo=1),
    Card("Krvavý rituál", self_damage=2, energy=2, combo=1, cost=0),
    Card("Bolestné probuzení", self_damage=3, draw=2, combo=2, cost=0),
    Card("Masakr", damage="combo", scale=2)
])

blade_of_blood_frenzy = Equipment("Čepel krvavého šílenství", "hand", [
    Card("Škrábanec", damage=1, combo=1, cost=0),
    Card("Zuřivý sled", damage=2, combo=2),
    Card("Zrychlený puls", energy=1, combo=2, target_type="self", cost=0),
    Card("Vyvrcholení", damage="combo", scale=2)
])

forbidden_texts = Equipment("Zakázané texty", "hand", [
    Card("Zakázaná slova", draw=2, combo=1),
    Card("Šepot", draw=1, discard=1, combo=1, target_type="self", cost=0),
    Card("Ztráta rozumu", self_damage=2, draw=3, combo=2),
    Card("Kolaps mysli", damage="combo", scale=2)
])

ritual_sickle = Equipment("Obřadní srp", "hand", [
    Card("Zářez", damage=2, combo=1),
    Card("Zářez", damage=2, combo=1),
    Card("Krvavý rituál", self_damage=2, combo=3, cost=0),
    Card("Sklizeň", damage="combo", lifesteal=0.5),
    Card("Krvavá žeň", damage="combo", scale=2, cost=2),
], two_handed=True)

serpent_spear = Equipment("Oštěp hadí bohyně", "hand", [
    Card("Jedovaté bodnutí", damage=2, combo=1, effect=Poison(2, 2), effect_on_damage=True),
    Card("Hadí tanec", combo=2, target_type="self", cost=0),
    Card("Uštknutí", damage=3, combo=1, effect=Poison(2, 2), effect_on_damage=True),
    Card("Hadí postoj", block=3, combo=1, effect=Thorns(1,3,1), target_type="self"),
    Card("Smrtící dávka", damage="combo", scale=2, cost=2),
], two_handed=True)

blood_vial = Equipment("Ampule s krví", "pocket", [
    Card("Vypití krve", self_damage=1, combo=2, cost=0),
])

sacrificial_bone = Equipment("Obětní kost", "belt", [
    Card("Vzpomínka na bolest", combo=3, cost=1, target_type="self"),
])

# ===== Štíty =====

shield = Equipment("Štít", "hand", [
    Card("Blok", block=3, target_type="self"),
    Card("Silný blok", block=4, target_type="self"),
])

shield_with_spike = Equipment("Štít s bodcem", "hand", [
    Card("Blok", block=3, target_type="self"),
    Card("Blok s bodcem", block=3, damage=3),
])


# ===== Zbroje =====

padded_armor = Equipment("Vycpávaná zbroj", "body", [
    Card("Pokrytí", block=2, target_type="self"),
    Card("Pokrytí", block=2, target_type="self"),
])

# ===== Monstra =====
proboscis = Equipment("Sosák", "hand", [
    Card("Píchnutí", damage=2),
    Card("Sátí krve", damage=2, lifesteal=1),
    Card("Sátí krve", damage=2, lifesteal=1),
    Card("Hladové sátí", damage=3, lifesteal=1.5)
])


wings = Equipment("Hmyzí křídla", "body", [
    Card("Poletování", effect=Dodge(0.5, 2), target_type="self"),
    Card("Poletování", effect=Dodge(0.5, 2), target_type="self")
])

ant_queen = Equipment("Mravenčí královna", "pocket", [
    Card("Povolání mravenců", spawn_enemy="Mravenec",
         spawn_count=2, target_type="self")
])

mandibles = Equipment("Kusadla", "hand", [
    Card("Kousnutí", damage=1)
])

horn = Equipment("Svolávací roh", "belt", [
    Card("Varovné troubení", spawn_enemy="Goblin",
         spawn_count=1, target_type="self")
])

reflexis = Equipment("Reflexy", "pocket", [
    Card("Mrštnost", effect=Dodge(0.5, 2), target_type="self"),
])

small_fangs = Equipment("Malé chelicery", "hand", [
    Card("Kousnutí", damage=2, effect=Poison(1, 3), effect_on_damage=True),
    Card("Kousnutí", damage=2, effect=Poison(1, 3), effect_on_damage=True),
])


fangs = Equipment("Chelicery", "hand", [
    Card("Kousnutí", damage=4, effect=Poison(2, 4), effect_on_damage=True),
    Card("Kousnutí", damage=4, effect=Poison(2, 4), effect_on_damage=True),
    Card("Paralyzující kousnutí", damage=3, effect=Stun(
        1), effect_chance=0.6, effect_on_damage=True),
])

newborns_exoskelet = Equipment("Nevyvynutý_exoskelet", "body", [
    Card("Pokrytí", block=3, target_type="self"),
    Card("Pokrytí", block=3, target_type="self"),
])

exoskelet = Equipment("Exoskelet", "body", [
    Card("Pokrytí", block=5, target_type="self"),
    Card("Pokrytí", block=5, target_type="self"),
])

spiders_cocon = Equipment("Kokon", "belt", [
    Card("Vylíhnutí", spawn_enemy="Pavoučí mládě",
         spawn_count=1, target_type="self")
])

jaw = Equipment("Morda", "hand", [
    Card("Kousnutí", damage=5),
    Card("Kousnutí", damage=5),
    Card("Řev", damage=3, buff_strenght=1),
    Card("Zuřivost", buff_strenght=2),
    Card("Povalení", damage=3, reduce_energy=1),
])

devourers_maw = Equipment("Žroutova tlama", "hand", [
    Card("Kousnutí", damage=2),
    Card("Škůdcovství", damage=1, devour=1),
    Card("Škůdcovství", damage=1, devour=1),
])

hide = Equipment("Medvědí kůže", "body", [
    Card("Srst", block=4, target_type="self"),
    Card("Srst", block=4, target_type="self"),
])

short_bow = Equipment("Krátký luk", "hand", [
    Card("Výstřel", damage=4),
    Card("Výstřel", damage=4)
])

shield_e = Equipment("Štít (nepřátelský)", "hand", [
    Card("Blok", block=3, target_type="ally"),
    Card("Silný blok", block=4, target_type="ally"),
])

set_of_traps = Equipment("Sada pastí", "belt", [
    Card("Síť", reduce_energy=1),
    Card("Paralyzující jehly", damage=1, effect=Stun(1), effect_chance=0.8, effect_on_damage=True),
    Card("Medvědí pasti", effect=Thorns(1, 2, 3), target_type="ally")
])

branches = Equipment("Větve", "hand", [
    Card("Švih", damage=4),
    Card("Příval úderů", damage=6),
    Card("Trní", effect=Thorns(0.7, 3, 3), target_type="self")
])

bark = Equipment("Pevná kůra", "body", [
    Card("Kůra", block=8, target_type="self"),
    Card("Kůra", block=8, target_type="self"),
])
# ===== Pomocné karty =====

war_paints = Equipment("Válečné barvy", "pocket", [
    Card("Bojový pokřik", buff_strenght=1, target_type="self")
])

abakus = Equipment("Abakus", "belt", [
    Card("Příprava", draw=2, target_type="self"),
    Card("Balance", draw=1, discard=1, target_type="self", cost=0)
])

battle_plans = Equipment("Bitevní plány", "belt", [
    Card("Taktika", draw=1, buff_strenght=1, target_type="self"),
])

caltrops = Equipment("Kaltropy", "pocket", [
    Card("Nastražení", effect=Thorns(1, 1, 2), target_type="self", cost=0),
])

rabits_paw = Equipment("Králičí packa", "pocket", [
    Card("Ochranné štěstí", effect=Dodge(0.8, 1), target_type="self", cost=0)
])

madmans_eye = Equipment("Šílencovo oko", "pocket", [
    Card("Šílené vize", damage=2, draw=2, target_type="self", cost=0)
])

ritual_statue = Equipment("Rituální soška", "belt", [
    Card("Šepot", draw=1, discard=1, combo=True, target_type="self", cost=0),
    Card("Prozření", draw="combo", target_type="self")
])
# ===== Prsteny =====

ring_of_defense = Equipment("Prsten ochrany", "ring", [
    Card("Bariera", block=4, target_type="self")
])

wurm_ring = Equipment("Prstenočerv", "ring", [
    Card("Přisátí", damage=2, lifesteal=1)
])

poisoners_ring = Equipment("Travičův prsten", "ring", [
    Card("Tajná ampule", effect=Poison(2, 2))
])

ring_with_needle = Equipment("Prsten s jehlou", "ring", [
    Card("Otrávené bodnutí", damage=1, effect=Poison(3, 3), effect_on_damage=True)
])

# ===== Společníci =====

friendly_ant = Equipment("Mravenec", "companion", [
    Card("Kousnutí", draw=1, damage=1, cost=0)
])

crow = Equipment("Vrána", "companion", [
    Card("Klovnutí", damage=2, effect=Dodge(0.4, 1), cost=1),
    Card("Průzkum", draw=1, discard=1, cost=0)
])
