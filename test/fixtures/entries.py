import pytest

from entries import PokemonEntry


@pytest.fixture
def pikachu_entry(pikachu):
    return PokemonEntry(pikachu)
