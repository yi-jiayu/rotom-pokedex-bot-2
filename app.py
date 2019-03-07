from pokedex.lookup import PokedexLookup
from pokedex.db import connect

session = connect()

_lookup = PokedexLookup(session=session)


def lookup(query):
    return _lookup.lookup(query)
