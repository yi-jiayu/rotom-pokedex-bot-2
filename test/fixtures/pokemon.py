import pytest

from pokedex.db import tables, util


@pytest.fixture
def pikachu(session):
    return util.get(session, tables.Pokemon, 'pikachu')
