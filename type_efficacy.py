from pokedex.db import tables


def get_type_effectiveness(session, pokemon):
    type_efficacies = session.query(tables.TypeEfficacy, tables.Type). \
        join(tables.Type, tables.TypeEfficacy.damage_type_id == tables.Type.id). \
        filter(tables.TypeEfficacy.target_type_id.in_(t.id for t in pokemon.types))
    type_effectiveness = {}
    for te, t in type_efficacies:
        type_effectiveness[t.name] = type_effectiveness.get(t.name, 1) * te.damage_factor / 100
    return type_effectiveness
