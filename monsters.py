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
            "description": "Malý humanoid známý svou zákeřností.",
            "lore": (
                "Gobliní kmeny přežívají v lese a obvykle je vede nějaký šaman či silný válečník. "
                "Když se jejich kmeni daří, vydávají se na výpravy, přepadávat a plenit."
            ),
            "extra_lore": (
                "Goblini jsou často využíváni jako levná bojová síla, protože k získání jejich respektu "
                "není třeba mnoho. Pokud nestačí vize boje a zisku cenností, zastrašování je učinná alternativa."
            ),
        },

        "Vrah": {
            "hp": 10,
            "equipment": [gear.poison_dagger],
            "description": "Zákeřný bandita, který útočí ze zálohy.",
            "lore": (
                "Tihle zabijáci se potulují lesy a číhají na osamělé cestovatele. "
                "Nepatří k žádnému řádu - zabíjejí pro kořist a vlastní přežití."
            ),
            "extra_lore": (
                "Někteří z nich si značí své oběti drobnými řezy, jako by šlo o podivný rituál. "
                "Není jasné, zda jde jen o zvyk, nebo o něco temnějšího."
            ),
        },

        "Štítonoš": {
            "hp": 15,
            "equipment": [gear.broken_sword, gear.shield_e],
            "abilities": [abilities.maintaining_defense],
            "description": "Drsný výběrčí mýta se štítem a zbrojí.",
            "lore": (
                "Štítonoši stojí na cestách a nutí poutníky platit za průchod. "
                "Kdo odmítne, rychle pozná sílu jejich štítu i meče."
            ),
            "extra_lore": (
                "Mnozí z nich bývali vojáky, kteří po válce nenašli jiné uplatnění. "
                "Jejich výstroj je často poslední připomínkou dávné služby."
            ),
        },

        "Lovec lidí": {
            "hp": 13,
            "equipment": [gear.short_bow, gear.set_of_traps],
            "description": "Stopař, který loví jiné lidi jako kořist.",
            "lore": (
                "Lovci lidí se pohybují na okrajích civilizace a sledují své cíle celé dny. "
                "Používají pasti a útoky ze zálohy, aby měli jistotu úspěchu."
            ),
            "extra_lore": (
                "Někteří si vedou záznamy o svých úlovcích - rytiny na zbraních nebo kůži. "
                "Čím více značek, tím větší respekt mezi ostatními lovci."
            ),
        },

        "Obří komár": {
            "hp": 5,
            "equipment": [gear.proboscis, gear.wings],
            "description": "Přerostlý hmyz lačnící po krvi.",
            "lore": (
                "Tito komáři se množí v temných a vlhkých oblastech. "
                "Jejich bodnutí je nepříjemné a často nebezpečné."
            ),
            "extra_lore": (
                "Říká se, že někteří byli zmutováni temnou magií. "
                "Jejich krev může mít zvláštní účinky, pokud je správně zpracována."
            ),
        },

        "Mraveniště": {
            "hp": 14,
            "equipment": [gear.ant_queen],
            "description": "Centrum kolonie, odkud proudí nekonečný zástup mravenců.",
            "lore": (
                "Mraveniště ukrývá královnu a tisíce dělníků připravených bránit svůj domov. "
                "Narušení kolonie vede k okamžité reakci."
            ),
            "extra_lore": (
                "Starší kolonie dokážou prorůstat hluboko pod zemí. "
                "Některé prý sahají až do zapomenutých ruin, kde se mění v něco mnohem nebezpečnějšího."
            ),
        },
        "Mravenec": {
            "hp": 1,
            "equipment": [gear.mandibles],
            "description": "",
            "lore": "",
            "extra_lore": ""

        },
        "Živoucí strom": {
            "hp": 20,
            "equipment": [gear.branches, gear.bark],
            "actions": 2,
            "description": "",
            "lore": "",
            "extra_lore": ""
        },
        "Žrout": {
            "hp": 8,
            "equipment": [gear.devourers_maw],
            "description": "",
            "lore": "",
            "extra_lore": "",
        },
        "Goblinní zvěd": {
            "hp": 12,
            "equipment": [gear.broken_sword, gear.horn, gear.reflexis],
            "description": "",
            "lore": "",
            "extra_lore": "",
        },
        "Goblinní válečník": {
            "hp": 16,
            "equipment": [gear.sword, gear.shield_e, gear.war_paints],
            "abilities": [abilities.maintaining_defense],
            "description": "",
            "lore": "",
            "extra_lore": "",
        },
        "Pavoučí mládě": {
            "hp": 7,
            "equipment": [gear.small_fangs, gear.newborns_exoskelet],
            "description": "",
            "lore": "",
            "extra_lore": "",
        },
        "Pavouk s vejcem": {
            "hp": 16,
            "equipment": [gear.fangs, gear.exoskelet, gear.spiders_cocon],
            "ai": spider_ai,
            "description": "",
            "lore": "",
            "extra_lore": "",
        },
        "Černý medvěd": {
            "hp": 20,
            "equipment": [gear.jaw],
            "actions": 2,
            "description": "",
            "lore": "",
            "extra_lore": "",
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
    enemy.description = template.get("description", "")
    enemy.lore = template.get("lore", "")
    enemy.extra_lore = template.get("extra_lore", "")

    enemy.is_boss = False

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


def create_boss_by_name(name):
    boss_types = {
        "Král Goblinů": {
            "hp": 40,
            "equipment": [gear.goblin_crown, gear.chiefs_cutter, gear.shiny_throne],
            "abilities": [abilities.maintaining_defense],
            "description": "Vládce goblinů, známý svou silou, smyslem pro strategii a podlostí.",
            "lore": "Král Goblinů sjednotil všechny gobliní kmeny pod svou vládou.",
            "entry_text": "Vstupuješ do rozvalin starého hradu, jehož kamenné věže jsou porostlé mechem a liánami. "
            "\nVzduch je těžký od vlhkosti lesa, mezi troskami se mihotají stíny. Kdesi v dálce zaznívá chřest zbraní a hlasité vrčení - "
            "\na pak zahlédneš trůn, na němž sedí Král Goblinů, korunovaný a připravený bránit svou říši.",
            "ai": goblin_king_ai
        },
        "Temný Šaman": {
            "hp": 35,
            "equipment": [gear.spirits_of_lost, gear.dark_mist, gear.twisted_staff],
            "abilities": [],
            "actions": 2,
            "description": "Mocný mág ovládající temnou magii.",
            "lore": "Vcházíš do temné mýtiny zahalené mlhou. Staré stromy se naklánějí nad tvou cestou, jejich větve škrábou do tváře jako prsty stínů. "
            "\nVzduch je plný chladivé magie a ozvěny dávných rituálů. Uprostřed prostoru se z mlhy vynořuje Temný Šaman, "
            "\njeho oči září a ruce svírají mocný artefakt - je jasné, že les je jeho a on je připraven tě zastavit.",
            "entry_text": "",
            "ai": dark_shaman_ai
        },
        # přidej další bossy podle potřeby
    }

    template = boss_types[name]

    boss = character.Character(name, template["hp"])

    for item in template["equipment"]:
        boss.equip_item(item, suppress_print=True)
    boss.build_deck()

    boss.all_cards = list(set(card.name for card in boss.deck))

    for ability in template.get("abilities", []):
        ability.apply(boss)

    boss.actions = template.get("actions", 1)
    boss.ai = template.get("ai", None)

    boss.description = template.get("description", "")
    boss.lore = template.get("lore", "")
    boss.extra_lore = template.get("extra_lore", "")

    boss.entry_text = template.get(
        "entry_text", f"Narazil jsi na bosse: {boss.name}!")
    boss.is_boss = True

    return boss


def create_boss_group(dungeon_level=1):
    boss_encounters = [
        {"name": "Král Goblinů", "levels": [1, 5]},
        {"name": "Temný Šaman", "levels": [1, 5]},
        # později další bossové pro toto i nadcházející regiony
    ]

    possible_bosses = [
        b for b in boss_encounters if dungeon_level in b["levels"]]
    if not possible_bosses:
        raise ValueError(
            f"Pro dungeon level {dungeon_level} nejsou definovaní žádní bossové.")

    chosen_boss = random.choice(possible_bosses)
    boss = create_boss_by_name(chosen_boss["name"])
    core.clear_screen()
    print(f"{core.Colors.DARK_RED}{boss.entry_text}{core.Colors.RESET}")
    input("ENTER pro pokračování...")

    return [boss]


def goblin_king_ai(enemy, player, enemies):
    enemy.draw(3)

    if not enemy.hand:
        return

    player_hp = player.hp
    player_block = player.block
    enemy_hp = enemy.hp
    enemy_max_hp = enemy.max_hp

    chosen_index = None

    for i, card in enumerate(enemy.hand):
        if card.damage and card.damage >= player_hp - player_block:
            chosen_index = i
            break

    if chosen_index is None and enemy_hp <= enemy_max_hp // 4:
        for i, card in enumerate(enemy.hand):
            if card.block:
                chosen_index = i
                break

    if chosen_index is None:
        for i, card in enumerate(enemy.hand):
            if card.spawn_enemy:
                chosen_index = i
                break

    for i, card in enumerate(enemy.hand):
        if card.name == "Pokřiování rozkazů" and len([e for e in enemies if e.hp > 0]) > 1:
            return i

    if chosen_index is None and enemy_hp <= enemy_max_hp // 2:
        for i, card in enumerate(enemy.hand):
            if card.block:
                chosen_index = i
                break

    if chosen_index is None and enemy.block > 0:
        for i, card in enumerate(enemy.hand):
            if card.spawn_enemy:
                chosen_index = i
                break

    if chosen_index is None:
        for i, card in enumerate(enemy.hand):
            if card.damage:
                chosen_index = i
                break

    if chosen_index is None:
        chosen_index = random.randint(0, len(enemy.hand) - 1)

    # ----------- zahraj kartu ------------
    enemy.play_card(
        chosen_index,
        target=player,
        enemies_list=enemies,
        create_enemy_func=create_enemy_by_name,
        player=player
    )

    enemy.discard_hand()


def dark_shaman_ai(enemy, player, enemies):
    actions = enemy.actions

    enemy.draw(actions+1)

    for _ in range(actions):
        if not enemy.hand:
            break

        index = choose_dark_shaman_card(enemy, player, enemies)

        enemy.play_card(
            index,
            target=player,
            enemies_list=enemies,
            create_enemy_func=create_enemy_by_name,
            player=player
        )

    enemy.discard_hand()


def choose_dark_shaman_card(enemy, player, enemies):
    player_fatigue = getattr(player, "fatigue", 0)
    enemy_hp = enemy.hp
    enemy_max_hp = enemy.max_hp

    has_dodge = any(isinstance(effect, core.Dodge)
                    for effect in enemy.status_effects)

    hand = enemy.hand

    if player_fatigue >= 5:
        for i, card in enumerate(hand):
            if card.block:
                return i

    if player_fatigue >= 6:
        for i, card in enumerate(hand):
            if card.damage == "fatigue":
                return i

    for i, card in enumerate(hand):
        if card.name == "Přivolání mlhy":
            return i

    if enemy_hp <= enemy_max_hp // 2:
        for i, card in enumerate(hand):
            if getattr(card, "lifesteal", 0) > 0:
                return i

    for i, card in enumerate(hand):
        if card.effect and isinstance(card.effect, core.Stun):
            return i

    if has_dodge:
        for i, card in enumerate(hand):
            if card.name == "Přízraky mlhy":
                return i

    for i, card in enumerate(hand):
        if getattr(card, "increase_fatigue", 0) > 0:
            return i

    valid_indices = [
        i for i, card in enumerate(hand)
        if not (card.name == "Přízraky mlhy" and not has_dodge)
    ]
    return random.choice(valid_indices)
