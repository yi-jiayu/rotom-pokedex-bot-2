import pytest

from pokedex.db import connect

from entries import *


@pytest.fixture
def session():
    return connect()


@pytest.fixture
def pokemon(session):
    return util.get(session, tables.Pokemon, 'bulbasaur')


@pytest.fixture
def pokemon_species(session):
    return util.get(session, tables.PokemonSpecies, 'bulbasaur')


@pytest.fixture
def pokemon_form(session):
    return util.get(session, tables.PokemonForm, 'sharpedo-mega')


@pytest.fixture
def ability(session):
    return util.get(session, tables.Ability, 'pixilate')


@pytest.fixture
def item(session):
    return util.get(session, tables.Item, 'soul-dew')


@pytest.fixture
def move(session):
    return util.get(session, tables.Move, 'psycho-boost')


@pytest.fixture
def pokemon_entry(pokemon):
    return PokemonEntry(pokemon)


@pytest.fixture
def item_entry(item):
    return ItemEntry(item)


@pytest.fixture
def ability_entry(ability):
    return AbilityEntry(ability)


@pytest.fixture
def move_entry(move):
    return MoveEntry(move)


@pytest.fixture
def gloom_entry(session):
    gloom = util.get(session, tables.Pokemon, 'gloom')
    return PokemonEntry(gloom)


@pytest.fixture
def silcoon_entry(session):
    silcoon = util.get(session, tables.Pokemon, 'silcoon')
    return PokemonEntry(silcoon)


@pytest.fixture
def machamp_entry(session):
    machamp = util.get(session, tables.Pokemon, 'machamp')
    return PokemonEntry(machamp)


@pytest.fixture
def scizor_entry(session):
    scizor = util.get(session, tables.Pokemon, 'scizor')
    return PokemonEntry(scizor)


class TestEntry:
    def test_from_pokemon_species_model(self, pokemon_species):
        entry = Entry.from_model(pokemon_species)
        assert isinstance(entry, PokemonEntry)
        assert entry.pokemon == pokemon_species.default_pokemon

    def test_from_pokemon_form_model(self, pokemon_form):
        entry = Entry.from_model(pokemon_form)
        assert isinstance(entry, PokemonEntry)
        assert entry.pokemon == pokemon_form.pokemon

    def test_from_item_model(self, item):
        entry = Entry.from_model(item)
        assert isinstance(entry, ItemEntry)
        assert entry.item == item

    def test_from_ability_model(self, ability):
        entry = Entry.from_model(ability)
        assert isinstance(entry, AbilityEntry)
        assert entry.ability == ability

    def test_from_move_model(self, move):
        entry = Entry.from_model(move)
        assert isinstance(entry, MoveEntry)
        assert entry.move == move


class TestPokemonEntry:
    def test_slug(self, pokemon_entry):
        expected = 'pokemon/1'
        actual = pokemon_entry.slug
        assert actual == expected

    def test_title(self, pokemon_entry):
        expected = 'Bulbasaur (#001)'
        actual = pokemon_entry.title()
        assert actual == expected

    def test_description(self, pokemon_entry):
        expected = 'Grass/Poison'
        actual = pokemon_entry.description()
        assert actual == expected

    def test_thumbnail(self, pokemon_entry):
        expected = 'https://assets.pokemon.com/assets/cms2/img/pokedex/detail/001.png'
        actual = pokemon_entry.thumbnail()
        assert actual == expected

    def test_from_pokemon_id(self):
        entry = PokemonEntry.from_pokemon_id(1)
        assert entry.pokemon.id == 1

    def test_from_nonexistent_pokemon_id(self):
        entry = PokemonEntry.from_pokemon_id(-1)
        assert entry is None

    def test_nonexistent_section(self, pokemon_entry: PokemonEntry):
        assert pokemon_entry.section('nonexistent') is None

    def test_image_url(self, pokemon_entry):
        assert pokemon_entry.image_url() == 'https://assets.pokemon.com/assets/cms2/img/pokedex/full/001.png'

    def test_form_image_url(self, mega_sharpedo_entry):
        assert mega_sharpedo_entry.image_url() == 'https://assets.pokemon.com/assets/cms2/img/pokedex/full/319_f2.png'

    def test_default_section(self, pokemon_entry: PokemonEntry):
        actual = pokemon_entry.default_section()
        expected = Section(
            content='''*Bulbasaur (#001)*
Seed Pokémon
Type: Grass/Poison
Weaknesses: Flying (2x), Fire (2x), Psychic (2x), Ice (2x)
Resistances: Fighting (0.5x), Water (0.5x), Grass (0.25x), Electric (0.5x), Fairy (0.5x)
Abilities: Overgrow
Hidden ability: Chlorophyll
Height: 0.7 m
Weight: 6.9 kg
[Image](https://assets.pokemon.com/assets/cms2/img/pokedex/full/001.png)''',
            children=[
                SectionReference('Base stats', 'pokemon/1/base_stats'),
                SectionReference('Evolutions', 'pokemon/1/evolutions'),
                SectionReference('Locations', 'pokemon/1/locations'),
            ])
        assert actual == expected

    def test_base_stats_section(self, pokemon_entry: PokemonEntry):
        actual = pokemon_entry.section('base_stats')
        expected = Section(
            content='''*Bulbasaur (#001)*
```
HP:       45 ======
Attack:   49 =======
Defense:  49 =======
Sp. Atk:  65 ==========
Sp. Def:  65 ==========
Speed:    45 ======
Total:   318
```''',
            parent=SectionReference('', 'pokemon/1/'),
            siblings=[
                SectionReference('Evolutions', 'pokemon/1/evolutions'),
                SectionReference('Locations', 'pokemon/1/locations'),
            ]
        )
        assert actual == expected

    def test_inline_result(self, pokemon_entry):
        expected = {
            'type': 'article',
            'id': 'pokemon/1',
            'title': 'Bulbasaur (#001)',
            'description': 'Grass/Poison',
            'input_message_content': {
                'message_text': '''*Bulbasaur (#001)*
Seed Pokémon
Type: Grass/Poison
Weaknesses: Flying (2x), Fire (2x), Psychic (2x), Ice (2x)
Resistances: Fighting (0.5x), Water (0.5x), Grass (0.25x), Electric (0.5x), Fairy (0.5x)
Abilities: Overgrow
Hidden ability: Chlorophyll
Height: 0.7 m
Weight: 6.9 kg
[Image](https://assets.pokemon.com/assets/cms2/img/pokedex/full/001.png)''',
                'parse_mode': 'Markdown',
            },
            'reply_markup': {
                'inline_keyboard': [
                    [{'text': 'Base stats', 'callback_data': 'pokemon/1/base_stats'}],
                    [{'text': 'Evolutions', 'callback_data': 'pokemon/1/evolutions'}],
                    [{'text': 'Locations', 'callback_data': 'pokemon/1/locations'}],
                ],
            },
            'thumb_url': 'https://assets.pokemon.com/assets/cms2/img/pokedex/detail/001.png'}
        actual = inline_result_for_entry(pokemon_entry)
        assert actual == expected

    def test_evolutions(self, gloom_entry):
        expected = Section(
            content='''Oddish (#043)
`└` *Gloom (#044)* at level 21
`  └` Vileplume (#045) using a Leaf Stone
`  └` Bellossom (#182) using a Sun Stone''',
            parent=SectionReference('', 'pokemon/44/'),
            children=[SectionReference('Oddish (#043)', 'pokemon/43/'),
                      SectionReference('Vileplume (#045)', 'pokemon/45/'),
                      SectionReference('Bellossom (#182)', 'pokemon/182/')]
        )
        actual = gloom_entry.section('evolutions')
        assert actual == expected

    def test_evolutions_trade(self, machamp_entry):
        expected = Section(
            content='''Machop (#066)
`└` Machoke (#067) at level 28
`  └` *Machamp (#068)* when traded''',
            parent=SectionReference('', 'pokemon/68/'),
            children=[SectionReference(name='Machop (#066)', path='pokemon/66/'),
                      SectionReference(name='Machoke (#067)', path='pokemon/67/')])
        actual = machamp_entry.section('evolutions')
        assert actual == expected

    def test_evolutions_trade_with_item(self, scizor_entry):
        expected = Section(
            content='''Scyther (#123)
`└` *Scizor (#212)* when traded holding a Metal Coat''',
            parent=SectionReference('', 'pokemon/212/'),
            children=[SectionReference(name='Scyther (#123)', path='pokemon/123/')])
        actual = scizor_entry.section('evolutions')
        assert actual == expected

    def test_locations(self, pikachu_entry):
        content = '''*Pikachu (#025)*
Locations

*Red, Blue:* Viridian Forest, Power Plant
*Ruby, Sapphire, Emerald:* Safari Zone
*FireRed, LeafGreen:* Viridian Forest, Power Plant
*Diamond, Pearl, Platinum:* Trophy Garden
*HeartGold, SoulSilver:* Viridian Forest
*X, Y:* Santalune Forest, Route 3'''
        expected = Section(
            content,
            parent=SectionReference('', 'pokemon/25/'),
            siblings=[
                SectionReference('Base stats', 'pokemon/25/base_stats'),
                SectionReference('Evolutions', 'pokemon/25/evolutions')
            ])
        actual = pikachu_entry.section('locations')
        assert actual == expected

    def test_locations_not_found_in_the_wild(self, scizor_entry):
        content = '''*Scizor (#212)*
Locations

Not found in the wild'''
        expected = Section(
            content,
            parent=SectionReference('', 'pokemon/212/'),
            siblings=[
                SectionReference('Base stats', 'pokemon/212/base_stats'),
                SectionReference('Evolutions', 'pokemon/212/evolutions')
            ])
        actual = scizor_entry.section('locations')
        assert actual == expected

    def test_learnset_section(self, pikachu_entry):
        expected = '''```
Level,Move,Type,Cat.,Pwr.,Acc.,PP
1,Growl,Normal,Status,-,100%,40
1,Thunder Shock,Electric,Special,40,100%,30
5,Tail Whip,Normal,Status,-,100%,30
10,Thunder Wave,Electric,Status,-,90%,20
13,Quick Attack,Normal,Physical,40,100%,30
18,Electro Ball,Electric,Special,-,100%,10
21,Double Team,Normal,Status,-,-%,15
26,Slam,Normal,Physical,80,75%,20
29,Thunderbolt,Electric,Special,90,100%,15
34,Feint,Normal,Physical,30,100%,10
37,Agility,Psychic,Status,-,-%,30
42,Discharge,Electric,Special,80,100%,15
45,Light Screen,Psychic,Status,-,-%,30
50,Thunder,Electric,Special,110,70%,10
```'''
        actual = pikachu_entry.learnset()
        assert actual == expected


class TestItemEntry:
    def test_slug(self, item_entry):
        expected = 'item/202'
        actual = item_entry.slug
        assert actual == expected

    def test_title(self, item_entry):
        expected = 'Soul Dew (item)'
        actual = item_entry.title()
        assert actual == expected

    def test_description(self, item_entry):
        expected = "Raises Latias and Latios's Special Attack and Special Defense by 50%."
        actual = item_entry.description()
        assert actual == expected

    def test_thumbnail(self, item_entry):
        assert item_entry.thumbnail() is None

    def test_default_section(self, item_entry):
        expected = Section('''*Soul Dew* (item)
Held by Latias or Latios: Increases the holder's Special Attack and Special Defense by 50%.''')
        actual = item_entry.default_section()
        assert actual == expected

    def test_inline_result(self, item_entry):
        expected = {
            'type': 'article',
            'id': 'item/202',
            'title': 'Soul Dew (item)',
            'input_message_content': {
                'message_text': '''*Soul Dew* (item)
Held by Latias or Latios: Increases the holder's Special Attack and Special Defense by 50%.''',
                'parse_mode': 'Markdown',
            },
            'description': "Raises Latias and Latios's Special Attack and Special Defense by 50%.",
        }
        actual = inline_result_for_entry(item_entry)
        assert actual == expected


class TestAbilityEntry:
    def test_slug(self, ability_entry):
        expected = 'ability/182'
        actual = ability_entry.slug
        assert actual == expected

    def test_title(self, ability_entry):
        expected = 'Pixilate (ability)'
        actual = ability_entry.title()
        assert actual == expected

    def test_description(self, ability_entry):
        expected = "Turns the bearer's Normal moves into Fairy moves and strengthens them to 1.3× their power."
        actual = ability_entry.description()
        assert actual == expected

    def test_thumbnail(self, ability_entry):
        assert ability_entry.thumbnail() is None

    def test_default_section(self, ability_entry):
        expected = Section('''*Pixilate* (ability)
Turns the bearer's Normal-type moves into Fairy moves.  Moves changed by this ability have 1.3× their power.''')
        actual = ability_entry.default_section()
        assert actual == expected

    def test_inline_result(self, ability_entry):
        expected = {
            'type': 'article',
            'id': 'ability/182',
            'title': 'Pixilate (ability)',
            'input_message_content': {
                'message_text': '''*Pixilate* (ability)
Turns the bearer's Normal-type moves into Fairy moves.  Moves changed by this ability have 1.3× their power.''',
                'parse_mode': 'Markdown',
            },
            'description': "Turns the bearer's Normal moves into Fairy moves and strengthens them to 1.3× their power.",
        }
        actual = inline_result_for_entry(ability_entry)
        assert actual == expected


class TestMoveEntry:
    def test_slug(self, move_entry):
        expected = 'move/354'
        actual = move_entry.slug
        assert actual == expected

    def test_title(self, move_entry):
        expected = 'Psycho Boost (move)'
        actual = move_entry.title()
        assert actual == expected

    def test_description(self, move_entry):
        expected = "Lowers the user's Special Attack by two stages after inflicting damage."
        actual = move_entry.description()
        assert actual == expected

    def test_thumbnail(self, move_entry):
        assert move_entry.thumbnail() is None

    def test_default_section(self, move_entry):
        expected = Section('''*Psycho Boost* (move)
Type: Psychic
Power: 140
Accuracy: 90
PP: 5
Inflicts regular damage, then lowers the user's Special Attack by two stages.''')
        actual = move_entry.default_section()
        assert actual == expected

    def test_inline_result(self, move_entry):
        expected = {
            'type': 'article',
            'id': 'move/354',
            'title': 'Psycho Boost (move)',
            'input_message_content': {
                'message_text': '''*Psycho Boost* (move)
Type: Psychic
Power: 140
Accuracy: 90
PP: 5
Inflicts regular damage, then lowers the user's Special Attack by two stages.''',
                'parse_mode': 'Markdown',
            },
            'description': "Lowers the user's Special Attack by two stages after inflicting damage.",
        }
        actual = inline_result_for_entry(move_entry)
        assert actual == expected


@pytest.mark.parametrize(('section', 'reply_markup'), [
    (Section(''), None),
    (Section('', children=[('Base stats', 'pokemon/1/base_stats')]),
     [('Base stats', 'pokemon/1/base_stats')]),
    (Section('', parent=('', 'pokemon/1/')),
     [('Back', 'pokemon/1/')]),
])
def test_reply_markup_for_section(section, reply_markup):
    expected = {'inline_keyboard': [[{'text': text, 'callback_data': data}]
                                    for text, data in reply_markup]} if reply_markup else None
    assert reply_markup_for_section(section) == expected
