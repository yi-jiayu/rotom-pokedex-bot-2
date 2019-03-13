import pytest

from pokedex.db import tables, util


@pytest.fixture
def pikachu(session):
    return util.get(session, tables.Pokemon, 'pikachu')


@pytest.fixture
def mega_sharpedo(session):
    return util.get(session, tables.Pokemon, 'sharpedo-mega')
