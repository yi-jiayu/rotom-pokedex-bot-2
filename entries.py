from abc import ABCMeta, abstractmethod
from collections import namedtuple
from dataclasses import dataclass, field
from itertools import groupby
from operator import itemgetter
from typing import Dict, List, Optional

from pokedex.db import tables, util

from sqlalchemy.orm.exc import NoResultFound

from app import session
from type_efficacy import get_type_effectiveness

STAT_NAMES = ('HP', 'Attack', 'Defense', 'Sp. Atk', 'Sp. Def', 'Speed')


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


SectionReference = namedtuple('SectionReference', ['name', 'path'])


@dataclass
class Section:
    content: str
    parent: Optional[SectionReference] = None
    siblings: List[SectionReference] = field(default_factory=list)
    children: List[SectionReference] = field(default_factory=list)


class Entry(metaclass=ABCMeta):
    slug: str

    def section(self, path) -> Optional[Section]:
        return self.default_section()

    @abstractmethod
    def default_section(self) -> Section:
        pass

    @abstractmethod
    def title(self):
        pass

    @abstractmethod
    def description(self):
        pass

    @abstractmethod
    def thumbnail(self):
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
        self.slug = f'pokemon/{pokemon.id}'
        self._title = f'{self.pokemon.name} (#{self.pokemon.id:03})'

    def title(self):
        return self._title

    def description(self):
        return '/'.join(t.name for t in self.pokemon.types)

    def thumbnail(self) -> str:
        return self.image_url().replace('full', 'detail')

    def image_url(self) -> str:
        if self.pokemon.id < 10000:
            return f'https://assets.pokemon.com/assets/cms2/img/pokedex/full/{self.pokemon.id:03}.png'
        else:
            species_id = self.pokemon.default_form.species.id
            form_order = self.pokemon.default_form.form_order
            return f'https://assets.pokemon.com/assets/cms2/img/pokedex/full/{species_id:03}_f{form_order}.png'

    @staticmethod
    def from_pokemon_id(id_: int) -> Optional['PokemonEntry']:
        try:
            pokemon = util.get(session, tables.Pokemon, id=id_)
            return PokemonEntry(pokemon)
        except NoResultFound:
            return None

    def default_section(self) -> Section:
        return Section(
            content=self.summary(),
            children=[
                SectionReference('Base stats', f'{self.slug}/base_stats'),
                SectionReference('Evolutions', f'{self.slug}/evolutions'),
                SectionReference('Locations', f'{self.slug}/locations'),
            ]
        )

    def section(self, path: str) -> Optional[Section]:
        if path == '':
            return self.default_section()
        elif path == 'base_stats':
            return Section(
                content=self.base_stats(),
                parent=SectionReference('', f'{self.slug}/'),
                siblings=[
                    SectionReference('Evolutions', f'{self.slug}/evolutions'),
                    SectionReference('Locations', f'{self.slug}/locations'),
                ],
            )
        elif path == 'evolutions':
            return self.evolutions_section()
        elif path == 'locations':
            return Section(
                self.locations(),
                parent=SectionReference('', f'{self.slug}/'),
                siblings=[
                    SectionReference('Base stats', f'{self.slug}/base_stats'),
                    SectionReference('Evolutions', f'{self.slug}/evolutions'),
                ],
            )

    def summary(self):
        type_effectiveness = get_type_effectiveness(session, self.pokemon)
        s = f'''*{self._title}*
{self.pokemon.species.genus}
Type: {'/'.join(t.name for t in self.pokemon.types)}
{format_type_effectiveness(type_effectiveness)}
Abilities: {', '.join(a.name for a in self.pokemon.abilities)}
Hidden ability: {self.pokemon.hidden_ability and self.pokemon.hidden_ability.name}
Height: {self.pokemon.height / 10} m
Weight: {self.pokemon.weight / 10} kg
[Image]({self.image_url()})'''
        return s

    def base_stats(self):
        stats = [s.base_stat for s in self.pokemon.stats]
        total = sum(stats)
        highest_stat = max(stats)
        unit = highest_stat / 10
        bars = [int(value / unit) for value in stats]
        base_stats = '\n'.join(
            f'{f"{STAT_NAMES[i]}:":8} {value:3} {"=" * bars}' for i, (value, bars) in enumerate(zip(stats, bars)))
        return f'''*{self._title}*
```
{base_stats}
Total:   {total}
```'''

    @staticmethod
    def _evolution_method(pokemon_evolution: tables.PokemonEvolution) -> str:
        if pokemon_evolution.evolution_trigger_id == 1 and pokemon_evolution.minimum_level:
            return f' at level {pokemon_evolution.minimum_level}'
        elif pokemon_evolution.evolution_trigger_id == 3:
            return f' using a {pokemon_evolution.trigger_item.name}'
        elif pokemon_evolution.evolution_trigger_id == 2:
            s = ' when traded'
            if pokemon_evolution.held_item:
                s += f' holding a {pokemon_evolution.held_item.name}'
            return s
        return ''

    @staticmethod
    def _build_evolutionary_tree(base, evolutions, current_id) -> str:
        tree = []
        stack = [(base, 0)]
        while stack:
            curr, depth = stack.pop()
            if depth == 0:
                prefix = ''
            else:
                prefix = f'`{" " * (depth - 1) * 2}└` '
            name = f'*{curr.name} (#{curr.id:03})*' if curr.id == current_id else f'{curr.name} (#{curr.id:03})'
            method = PokemonEntry._evolution_method(curr.evolutions[0]) if curr.evolutions else ''
            tree.append(f'{prefix}{name}{method}')
            for p in sorted(evolutions.get(curr, []), key=lambda x: x.id, reverse=True):
                stack.append((p, depth + 1))
        return '\n'.join(tree)

    def evolutions_section(self) -> Section:
        chain = self.pokemon.species.evolution_chain.species
        evolutions = {}
        first = None
        for p in chain:
            if not p.parent_species:
                first = p
            if p.child_species:
                evolutions[p] = evolutions.get(p, []) + p.child_species
        content = self._build_evolutionary_tree(first, evolutions, self.pokemon.species_id)
        section = Section(content, parent=SectionReference('', f'pokemon/{self.pokemon.id}/'))
        section.children.extend(
            SectionReference(f'{p.name} (#{p.id:03})', f'pokemon/{p.id}/')
            for p in chain if p.id != self.pokemon.species_id)
        return section

    def locations(self):
        q = session.query(tables.Encounter) \
            .join(tables.LocationArea).join(tables.Location) \
            .filter(tables.Encounter.pokemon_id == self.pokemon.id) \
            .group_by(tables.LocationArea.location_id, tables.Encounter.version_id) \
            .order_by(tables.Encounter.version_id)
        encounters = ((e.version.names_local.name, e.location_area.location.names_local.name) for e in q)
        grouped_by_version = ((version_group, tuple(l[1] for l in locations)) for version_group, locations in
                              groupby(encounters, key=itemgetter(0)))
        grouped_by_locations = ((tuple(vg[0] for vg in version_group), locations) for locations, version_group in
                                groupby(grouped_by_version, key=itemgetter(1)))
        locations = '\n'.join(
            f'*{", ".join(versions)}:* {", ".join(locations)}' for versions, locations in grouped_by_locations)
        return f'*{self._title}*\nLocations\n\n' + (locations or 'Not found in the wild')

    def learnset(self):
        level_up_moves = session.query(tables.PokemonMove) \
            .join(tables.VersionGroup) \
            .filter(tables.PokemonMove.pokemon_id == self.pokemon.id,
                    tables.PokemonMove.pokemon_move_method_id == 1,
                    tables.VersionGroup.generation_id == 5) \
            .group_by(tables.PokemonMove.move_id) \
            .order_by(tables.PokemonMove.level, tables.PokemonMove.order) \
            .all()
        header = ','.join(('Level', 'Move', 'Type', 'Cat.', 'Pwr.', 'Acc.', 'PP'))
        rows = [','.join(
            (str(move.level),
             move.move.name,
             move.move.type.name,
             move.move.damage_class.name.capitalize(),
             f'{move.move.power or "-"}',
             f'{move.move.accuracy or "-"}%',
             str(move.move.pp))) for move in level_up_moves]
        body = '\n'.join(rows)
        return f'''```
{header}
{body}
```'''


class ItemEntry(Entry):
    def __init__(self, item: tables.Item):
        self.item = item
        self.slug = f'item/{self.item.id}'

    def title(self):
        return f'{self.item.name} (item)'

    def description(self):
        return f'{self.item.short_effect}'

    def thumbnail(self):
        pass

    def default_section(self) -> Section:
        return Section(self.summary())

    def summary(self):
        return f'''*{self.item.name}* (item)
{self.item.effect}'''


class AbilityEntry(Entry):
    def __init__(self, ability) -> None:
        self.ability = ability
        self.slug = f'ability/{self.ability.id}'

    def title(self):
        return f'{self.ability.name} (ability)'

    def description(self):
        return f'{self.ability.short_effect}'

    def thumbnail(self):
        pass

    def default_section(self) -> Section:
        return Section(self.summary())

    def summary(self):
        return f'''*{self.ability.name}* (ability)
{self.ability.effect}'''


class MoveEntry(Entry):
    def __init__(self, move):
        self.move = move
        self.slug = f'move/{self.move.id}'

    def title(self):
        return f'{self.move.name} (move)'

    def description(self):
        return f'{self.move.short_effect}'

    def thumbnail(self):
        pass

    def default_section(self) -> Section:
        return Section(self.summary())

    def summary(self):
        return f'''*{self.move.name}* (move)
Type: {self.move.type.name}
Power: {self.move.power}
Accuracy: {self.move.accuracy}
PP: {self.move.pp}
{self.move.effect}'''


def reply_markup_for_section(section) -> Optional[Dict]:
    buttons = []
    if section.parent:
        buttons.append({'text': 'Back', 'callback_data': section.parent[1]})
    if not section.children:
        for name, path in section.siblings:
            buttons.append({'text': name, 'callback_data': path})
    for name, path in section.children:
        buttons.append({'text': name, 'callback_data': path})
    if buttons:
        return {'inline_keyboard': [[b] for b in buttons]}


def inline_result_for_entry(entry: Entry):
    result = {
        'type': 'article',
        'id': entry.slug,
        'title': entry.title(),
        'description': entry.description(),
    }
    default_section = entry.default_section()
    result['input_message_content'] = {'message_text': default_section.content, 'parse_mode': 'Markdown'}
    reply_markup = reply_markup_for_section(default_section)
    if reply_markup:
        result['reply_markup'] = reply_markup
    thumbnail = entry.thumbnail()
    if thumbnail:
        result['thumb_url'] = thumbnail
    return result
