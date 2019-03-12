[![CircleCI](https://circleci.com/gh/yi-jiayu/rotom-pokedex-bot-2.svg?style=svg)](https://circleci.com/gh/yi-jiayu/rotom-pokedex-bot-2)
[![codecov](https://codecov.io/gh/yi-jiayu/rotom-pokedex-bot-2/branch/master/graph/badge.svg)](https://codecov.io/gh/yi-jiayu/rotom-pokedex-bot-2)

# Rotom Pokédex Bot 2
A rewrite of https://github.com/yi-jiayu/rotom-pokedex-bot to use data from
https://github.com/veekun/pokedex.

Find it on Telegram: [@rotom_pokedex_bot](https://t.me/rotom_pokedex_bot)

<img alt="Screenshot of Rotom Pokédex Bot displaying an entry for Turtwig" src="https://user-images.githubusercontent.com/11734309/54208898-c00aac00-4517-11e9-8a4a-6b3101d84123.png" width=400>

## Roadmap

- [x] Pokémon summary
- [x] Abilities
- [x] Moves
- [x] Pokémon forms
- [x] Items
- [ ] Pokémon locations
- [x] Pokémon base stats
- [x] Pokémon evolutions
- [ ] Pokémon learnsets

- [x] Inline mode

## Dependencies

- Python 3.7
- Pipenv

## Setup

```sh
pipenv install
pipenv run pokedex setup -v
```

This sets up a virtual environment, installs dependencies and loads Pokédex data.
