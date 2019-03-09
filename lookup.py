from pokedex.db import tables
from pokedex.lookup import PokedexLookup

lookup = PokedexLookup()


def best_match(query):
    results = lookup.lookup(query)
    if not results:
        return None
    return results[0].object
