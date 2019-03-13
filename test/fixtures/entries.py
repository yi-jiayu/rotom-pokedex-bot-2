import pytest

from entries import PokemonEntry


@pytest.fixture
def pikachu_entry(pikachu):
    return PokemonEntry(pikachu)


@pytest.fixture
def mega_sharpedo_entry(mega_sharpedo):
    return PokemonEntry(mega_sharpedo)
