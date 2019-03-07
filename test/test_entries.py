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
    def test_from_id(self):
        entry = PokemonEntry.from_id(1)
        assert entry.pokemon.id == 1

    def test_from_nonexistent_id(self):
        entry = PokemonEntry.from_id(-1)
        assert entry is None

    def test_nonexistent_section(self, pokemon_entry: PokemonEntry):
        assert pokemon_entry.section('nonexistent') is None

    def test_default_section(self, pokemon_entry: PokemonEntry):
        actual = pokemon_entry.default_section()
        expected = Section(
            content='''*Bulbasaur (#001)*
Type: Grass/Poison
Weaknesses: Flying (2x), Fire (2x), Psychic (2x), Ice (2x)
Resistances: Fighting (0.5x), Water (0.5x), Grass (0.25x), Electric (0.5x), Fairy (0.5x)
Abilities: Overgrow
Hidden ability: Chlorophyll
Height: 0.7 m
Weight: 6.9 kg
[Image](https://assets.pokemon.com/assets/cms2/img/pokedex/full/001.png)''',
            children=[SectionReference('Base stats', 'pokemon/1/base_stats')])
        assert actual == expected

    def test_base_stats_section(self, pokemon_entry: PokemonEntry):
        actual = pokemon_entry.section('base_stats')
        expected = Section(
            content='''*Bulbasaur (#001)*
HP:              45
Attack:          49
Defense:         49
Special Attack:  65
Special Defense: 65
Speed:           45''',
            parent=SectionReference('', 'pokemon/1/')
        )
        assert actual == expected


class TestItemEntry:
    def test_default_section(self, item_entry):
        expected = Section('''*Soul Dew* (item)
Held by Latias or Latios: Increases the holder's Special Attack and Special Defense by 50%.''')
        actual = item_entry.default_section()
        assert actual == expected


class TestAbilityEntry:
    def test_default_section(self, ability_entry):
        expected = Section('''*Pixilate* (ability)
Turns the bearer's Normal-type moves into Fairy moves.  Moves changed by this ability have 1.3× their power.''')
        actual = ability_entry.default_section()
        assert actual == expected


class TestMoveEntry:
    def test_default_section(self, move_entry):
        expected = Section('''*Psycho Boost* (move)
Type: Psychic
Power: 140
Accuracy: 90
PP: 5
Inflicts regular damage, then lowers the user's Special Attack by two stages.''')
        actual = move_entry.default_section()
        assert actual == expected
