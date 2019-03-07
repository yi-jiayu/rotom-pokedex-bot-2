from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from collections import namedtuple
from typing import List, Optional

from pokedex.db import tables, util

from sqlalchemy.orm.exc import NoResultFound

from app import session
from type_efficacy import get_type_effectiveness


def format_type_effectiveness(type_effectiveness):
    weaknesses = ', '.join(f'{t} ({e:.2g}x)' for t, e in type_effectiveness.items() if e > 1)
    resistances = ', '.join(f'{t} ({e:.2g}x)' for t, e in type_effectiveness.items() if 1 > e > 0)
    immunities = ', '.join(f'{t} ({e:.2g}x)' for t, e in type_effectiveness.items() if e == 0)
    return '\n'.join(
        f'{k}: {v}' for k, v in (('Weaknesses', weaknesses),
                                 ('Resistances', resistances),
                                 ('Immunities', immunities)) if v)


def pokemon_full_image_url(pokemon_id):
    return f'https://assets.pokemon.com/assets/cms2/img/pokedex/full/{pokemon_id:03}.png'


def format_pokemon_base_stats(pokemon):
    base_stats = '\n'.join(f'{f"{s.stat.name}:":16} {s.base_stat}' for s in pokemon.stats)
    return f'''*{pokemon.name} (#{pokemon.id:03})*
{base_stats}'''


SectionReference = namedtuple('SectionReference', ['name', 'path'])


@dataclass
class Section:
    content: str
    parent: Optional[SectionReference] = None
    siblings: List[SectionReference] = field(default_factory=list)
    children: List[SectionReference] = field(default_factory=list)


class Entry(metaclass=ABCMeta):
    def section(self, path) -> Optional[Section]:
        return self.default_section()

    @abstractmethod
    def default_section(self) -> Section:
        pass

    @staticmethod
    def from_model(m) -> Optional['Entry']:
        if isinstance(m, tables.PokemonSpecies):
            return PokemonEntry(m.default_pokemon)
        elif isinstance(m, tables.PokemonForm):
            return PokemonEntry(m.pokemon)
        elif isinstance(m, tables.Item):
            return ItemEntry(m)
        elif isinstance(m, tables.Ability):
            return AbilityEntry(m)
        elif isinstance(m, tables.Move):
            return MoveEntry(m)


class PokemonEntry(Entry):
    def __init__(self, pokemon: tables.Pokemon):
        self.pokemon = pokemon
        self.prefix = f'pokemon/{pokemon.id}'

    @staticmethod
    def from_id(id_: int) -> Optional['PokemonEntry']:
        try:
            pokemon = util.get(session, tables.Pokemon, id=id_)
            return PokemonEntry(pokemon)
        except NoResultFound:
            return None

    def default_section(self) -> Section:
        return Section(
            content=self.summary(),
            children=[SectionReference('Base stats', f'{self.prefix}/base_stats')]
        )

    def section(self, path: str) -> Optional[Section]:
        if path == '':
            return self.default_section()
        elif path == 'base_stats':
            return Section(
                content=self.base_stats(),
                parent=SectionReference('', f'{self.prefix}/'),
            )

    def summary(self):
        type_effectiveness = get_type_effectiveness(session, self.pokemon)
        s = f'''*{self.pokemon.name} (#{self.pokemon.id:03})*
Type: {'/'.join(t.name for t in self.pokemon.types)}
{format_type_effectiveness(type_effectiveness)}
Abilities: {', '.join(a.name for a in self.pokemon.abilities)}
Hidden ability: {self.pokemon.hidden_ability and self.pokemon.hidden_ability.name}
Height: {self.pokemon.height / 10} m
Weight: {self.pokemon.weight / 10} kg'''
        if self.pokemon.id < 10000:
            s += f'\n[Image]({pokemon_full_image_url(self.pokemon.id)})'
        return s

    def base_stats(self):
        base_stats = '\n'.join(f'{f"{s.stat.name}:":16} {s.base_stat}' for s in self.pokemon.stats)
        return f'''*{self.pokemon.name} (#{self.pokemon.id:03})*
```
{base_stats}
```'''


class ItemEntry(Entry):
    def __init__(self, item: tables.Item):
        self.item = item

    def default_section(self) -> Section:
        return Section(self.summary())

    def summary(self):
        return f'''*{self.item.name}* (item)
{self.item.effect}'''


class AbilityEntry(Entry):
    def __init__(self, ability) -> None:
        self.ability = ability

    def default_section(self) -> Section:
        return Section(self.summary())

    def summary(self):
        return f'''*{self.ability.name}* (ability)
{self.ability.effect}'''


class MoveEntry(Entry):
    def __init__(self, move):
        self.move = move

    def default_section(self) -> Section:
        return Section(self.summary())

    def summary(self):
        return f'''*{self.move.name}* (move)
Type: {self.move.type.name}
Power: {self.move.power}
Accuracy: {self.move.accuracy}
PP: {self.move.pp}
{self.move.effect}'''
