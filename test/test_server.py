import pytest

from pokedex.db import connect, tables, util

from server import *


@pytest.fixture
def session():
    return connect()


@pytest.fixture
def pokemon(session):
    return util.get(session, tables.Pokemon, 'torterra')


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


class TestPokemon:
    def test_format_pokemon(self, session, pokemon):
        expected = '''*Torterra (#389)*
Type: Grass/Ground
Weaknesses: Flying (2x), Bug (2x), Fire (2x), Ice (4x)
Resistances: Ground (0.5x), Rock (0.5x)
Immunities: Electric (0x)
Abilities: Overgrow
Hidden ability: Shell Armor
Height: 2.2 m
Weight: 310.0 kg
[Image](https://assets.pokemon.com/assets/cms2/img/pokedex/full/389.png)'''
        actual = format_pokemon(session, pokemon)
        assert actual == expected

    def test_format_pokemon2(self, session, pokemon_form):
        expected = '''*Mega Sharpedo (#10070)*
Type: Water/Dark
Weaknesses: Fighting (2x), Bug (2x), Grass (2x), Electric (2x), Fairy (2x)
Resistances: Ghost (0.5x), Steel (0.5x), Fire (0.5x), Water (0.5x), Ice (0.5x), Dark (0.5x)
Immunities: Psychic (0x)
Abilities: Strong Jaw
Hidden ability: None
Height: 2.5 m
Weight: 130.3 kg'''
        actual = format_pokemon(session, pokemon_form.pokemon)
        assert actual == expected

    def test_format_pokemon_inline_result(self, session, pokemon):
        expected = {
            'type': 'article',
            'id': 'pokemon#389',
            'title': 'Torterra (#389)',
            'input_message_content': {
                'message_text': '''*Torterra (#389)*
Type: Grass/Ground
Weaknesses: Flying (2x), Bug (2x), Fire (2x), Ice (4x)
Resistances: Ground (0.5x), Rock (0.5x)
Immunities: Electric (0x)
Abilities: Overgrow
Hidden ability: Shell Armor
Height: 2.2 m
Weight: 310.0 kg
[Image](https://assets.pokemon.com/assets/cms2/img/pokedex/full/389.png)''',
                'parse_mode': 'Markdown'
            },
            'description': 'Grass/Ground',
            'thumb_url': 'https://assets.pokemon.com/assets/cms2/img/pokedex/detail/389.png',
        }
        actual = format_pokemon_inline_result(session, pokemon)
        assert actual == expected

    def test_format_pokemon_inline_result2(self, session, pokemon_form):
        """When the Pokémon is an alternate form, there should be no thumb_url and image."""
        actual = format_pokemon_inline_result(session, pokemon_form.pokemon)
        assert 'thumb_url' not in actual


class TestAbility:
    def test_format_ability(self, ability):
        expected = '''*Pixilate* (ability)
Turns the bearer's Normal-type moves into Fairy moves.  Moves changed by this ability have 1.3× their power.'''
        actual = format_ability(ability)
        assert actual == expected

    def test_format_ability_inline_result(self, ability):
        expected = {
            'type': 'article',
            'id': 'ability#182',
            'title': 'Pixilate (ability)',
            'input_message_content': {
                'message_text': '''*Pixilate* (ability)
Turns the bearer's Normal-type moves into Fairy moves.  Moves changed by this ability have 1.3× their power.''',
                'parse_mode': 'Markdown',
            },
            'description': "Turns the bearer's Normal moves into Fairy moves and strengthens them to 1.3× their power.",
        }
        actual = format_ability_inline_result(ability)
        assert actual == expected


class TestItem:
    def test_format_item(self, item):
        expected = '''*Soul Dew* (item)
Held by Latias or Latios: Increases the holder's Special Attack and Special Defense by 50%.'''
        actual = format_item(item)
        assert actual == expected

    def test_format_item_inline_result(self, item):
        expected = {
            'type': 'article',
            'id': 'item#202',
            'title': 'Soul Dew (item)',
            'input_message_content': {
                'message_text': '''*Soul Dew* (item)
Held by Latias or Latios: Increases the holder's Special Attack and Special Defense by 50%.''',
                'parse_mode': 'Markdown',
            },
            'description': "Raises Latias and Latios's Special Attack and Special Defense by 50%.",
        }
        actual = format_item_inline_result(item)
        assert actual == expected


class TestMove:
    def test_format_move(self, move):
        expected = '''*Psycho Boost* (move)
Type: Psychic
Power: 140
Accuracy: 90
PP: 5
Inflicts regular damage, then lowers the user's Special Attack by two stages.'''
        actual = format_move(move)
        assert actual == expected

    def test_format_move_inline_result(self, move):
        expected = {
            'type': 'article',
            'id': 'move#354',
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
        actual = format_move_inline_Result(move)
        assert actual == expected
