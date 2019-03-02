[![CircleCI](https://circleci.com/gh/yi-jiayu/rotom-pokedex-bot-2.svg?style=svg)](https://circleci.com/gh/yi-jiayu/rotom-pokedex-bot-2)
[![codecov](https://codecov.io/gh/yi-jiayu/rotom-pokedex-bot-2/branch/master/graph/badge.svg)](https://codecov.io/gh/yi-jiayu/rotom-pokedex-bot-2)

# Rotom Pokédex Bot 2
A rewrite of https://github.com/yi-jiayu/rotom-pokedex-bot to use data from
https://github.com/veekun/pokedex. 

## Roadmap

- [x] Pokémon summary
- [x] Abilities
- [x] Moves
- [x] Pokémon forms
- [x] Items
- [ ] Pokémon locations
- [ ] Pokémon base stats

- [ ] Inline mode

## Dependencies

- Python 3.7
- Pipenv

## Setup

```sh
pipenv install
pipenv run pokedex setup -v
```

This sets up a virtual environment, installs dependencies and loads Pokédex data.
