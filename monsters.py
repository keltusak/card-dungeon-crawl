import gear
import core
import abilities
import character
import random


def create_enemy_by_name(name):
    enemy_types = {
        "Goblin": {
            "hp": 12,
            "equipment": [gear.broken_sword],
        },
        "Vrah": {
            "hp": 10,
            "equipment": [gear.poison_dagger],
        },
        "Štítonoš": {
            "hp": 15,
            "equipment": [gear.broken_sword, gear.shield_e],
            "abilities": [abilities.maintaining_defense],
        },
        "Lovec lidí": {
            "hp": 13,
            "equipment": [gear.short_bow, gear.set_of_traps],
        },
        "Obří komár": {
            "hp": 5,
            "equipment": [gear.proboscis, gear.wings],
        },
        "Mraveniště": {
            "hp": 14,
            "equipment": [gear.ant_queen],
        },
        "Mravenec": {
            "hp": 1,
            "equipment": [gear.mandibles],
        },
        "Živoucí strom": {
            "hp": 20,
            "equipment": [gear.branches, gear.bark],
            "actions": 2
        },
        "Žrout": {
            "hp": 8,
            "equipment": [gear.devourers_maw],
        },
        "Goblinní zvěd": {
            "hp": 12,
            "equipment": [gear.broken_sword, gear.horn, gear.reflexis],
        },
        "Goblinní válečník": {
            "hp": 16,
            "equipment": [gear.sword, gear.shield_e, gear.war_paints],
            "abilities": [abilities.maintaining_defense],
        },
        "Pavoučí mládě": {
            "hp": 7,
            "equipment": [gear.small_fangs, gear.newborns_exoskelet],
        },
        "Pavouk s vejcem": {
            "hp": 16,
            "equipment": [gear.fangs, gear.exoskelet, gear.spiders_cocon],
            "ai": spider_ai
        },
        "Černý medvěd": {
            "hp": 20,
            "equipment": [gear.jaw],
            "actions": 2
        },

    }

    template = enemy_types[name]

    enemy = character.Character(name, template["hp"])
    for item in template["equipment"]:
        enemy.equip_item(item, suppress_print=True)
    enemy.build_deck()

    for ability in template.get("abilities", []):
        ability.apply(enemy)

    enemy.actions = template.get("actions", 1)
    enemy.ai = template.get("ai", None)
    enemy.all_cards = list(set(card.name for card in enemy.deck))

    return enemy


def create_enemy_group(dungeon_level=1):
    encounter_types = [
        {"type": "komáři", "enemies": [
            ("Obří komár", 2, 3)], "levels": [1, 2]},
        {"type": "goblini", "enemies": [("Goblin", 1, 2)], "levels": [1]},
        {"type": "bandití výběrčí", "enemies": [
            ("Štítonoš", 1, 2)], "levels": [1, 2]},
        {"type": "vrazi", "enemies": [("Vrah", 1, 2)], "levels": [1]},
        {"type": "mravenci", "enemies": [
            ("Mraveniště", 1, 1)], "levels": [1, 2]},
        # od lvl 2
        {"type": "vrazi", "enemies": [("Vrah", 2, 2)], "levels": [2]},
        {"type": "gobliní banda", "enemies": [
            ("Goblinní válečník", 1, 1), ("Goblin", 1, 2)], "levels": [2, 3]},
        {"type": "gobliní stráž", "enemies": [
            ("Goblinní válečník", 1, 1), ("Goblinní zvěd", 1, 1)], "levels": [2, 4]},
        # od lvl 3
        {"type": "komáří roj", "enemies": [
            ("Obří komár", 4, 4)], "levels": [3]},
        {"type": "Přepad", "enemies": [
            ("Štítonoš", 1, 1), ("Vrah", 1, 1), ("Lovec lidí", 1, 1)], "levels": [3, 4]},
        {"type": "lovící pavouk", "enemies": [
            ("Pavouk s vejcem", 1, 1)], "levels": [3, 4]},
        {"type": "Goblinní havěť", "enemies": [
            ("Goblinní zvěd", 1, 1), ("Žrout", 2, 3)], "levels": [3]},
        {"type": "zuřivý medvěd", "enemies": [
            ("Černý medvěd", 1, 1)], "levels": [3, 4]},
        # od lvl 4
        {"type": "gobliní kemp", "enemies": [
            ("Goblinní válečník", 1, 1), ("Goblin", 1, 2), ("Žrout", 1, 2)], "levels": [4]},
        {"type": "les", "enemies": [
            ("Živoucí strom", 1, 1),], "levels": [4]},

    ]

    possible_encounters = [
        e for e in encounter_types if dungeon_level in e["levels"]]

    if not possible_encounters:
        raise ValueError(
            f"Pro dungeon level {dungeon_level} nejsou definované žádné skupiny nepřátel.")

    encounter = random.choice(possible_encounters)

    enemies = []
    for enemy_info in encounter["enemies"]:
        name, min_count, max_count = enemy_info
        count = random.randint(min_count, max_count)
        for _ in range(count):
            enemies.append(create_enemy_by_name(name))

    print(
        f"Narazil jsi na nepřítele: {encounter['type']} ({len(enemies)})")
    input("ENTER pro pokračování...")
    return enemies


def spider_ai(enemy, player, enemies):
    enemy.draw(2)

    if not enemy.hand:
        return

    index = choose_spider_card(enemy, player)

    enemy.play_card(
        index,
        target=player,
        enemies_list=enemies,
        create_enemy_func=create_enemy_by_name,
        player=player
    )

    enemy.discard_hand()


def choose_spider_card(enemy, player):
    hand = enemy.hand

    player_has_block = player.block > 2
    for effect in player.status_effects:
        if isinstance(effect, core.Poison):
            player_poisoned = True
    player_poisoned = False

    for i, card in enumerate(hand):
        if card.name == "Vylíhnutí":
            return i

    if not player_has_block:
        for i, card in enumerate(hand):
            if card.name == "Paralizující kousnutí":
                return i

    if player_poisoned and not player_has_block:
        for i, card in enumerate(hand):
            if card.name == "Kousnutí":
                return i

    if player_poisoned:
        for i, card in enumerate(hand):
            if card.name == "Pokrytí":
                return i

    if not player_has_block:
        for i, card in enumerate(hand):
            if card.name == "Kousnutí":
                return i

    for i, card in enumerate(hand):
        if card.name == "Pokrytí":
            return i

    return random.randint(0, len(hand) - 1)
