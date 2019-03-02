import argparse
import json
import logging
import os
import sys

from pokedex.lookup import PokedexLookup
from pokedex.db import connect, tables

import sentry_sdk

import tornado.httpclient
import tornado.ioloop
import tornado.web

import type_efficacy

session = connect()
lookup = PokedexLookup(session=session)


def format_type_effectiveness(type_effectiveness):
    weaknesses = ', '.join(f'{t} ({e:.2g}x)' for t, e in type_effectiveness.items() if e > 1)
    resistances = ', '.join(f'{t} ({e:.2g}x)' for t, e in type_effectiveness.items() if 1 > e > 0)
    immunities = ', '.join(f'{t} ({e:.2g}x)' for t, e in type_effectiveness.items() if e == 0)
    return '\n'.join(
        f'{k}: {v}' for k, v in (('Weaknesses', weaknesses),
                                 ('Resistances', resistances),
                                 ('Immunities', immunities)) if v)


def pokemon_image_url(pokemon_id):
    return f'https://assets.pokemon.com/assets/cms2/img/pokedex/full/{pokemon_id}.png'


def format_pokemon(session, pokemon: tables.Pokemon):
    type_effectiveness = type_efficacy.get_type_effectiveness(session, pokemon)
    s = f'''*{pokemon.name} (#{pokemon.id:03})*
Type: {'/'.join(t.name for t in pokemon.types)}
{format_type_effectiveness(type_effectiveness)}
Abilities: {', '.join(a.name for a in pokemon.abilities)}
Hidden ability: {pokemon.hidden_ability and pokemon.hidden_ability.name}
Height: {pokemon.height / 10} m
Weight: {pokemon.weight / 10} kg'''
    if pokemon.id < 10000:
        s += f'\n[Image]({pokemon_image_url(pokemon.id)})'
    return s


def format_ability(ability: tables.Ability):
    return f'''*{ability.name}* (ability)
{ability.effect}'''


def format_item(item: tables.Item):
    return f'''*{item.name}* (item)
{item.effect}'''


def format_move(move: tables.Move):
    return f'''*{move.name}* (move)
Type: {move.type.name}
Power: {move.power}
Accuracy: {move.accuracy}
PP: {move.pp}
{move.effect}'''


def format_result(session, result):
    if isinstance(result, tables.PokemonSpecies):
        return format_pokemon(session, result.default_pokemon)
    elif isinstance(result, tables.PokemonForm):
        return format_pokemon(session, result.pokemon)
    elif isinstance(result, tables.Item):
        return format_item(result)
    elif isinstance(result, tables.Ability):
        return format_ability(result)
    elif isinstance(result, tables.Move):
        return format_move(result)


class WebhookHandler(tornado.web.RequestHandler):
    def initialize(self, session, lookup):
        self.session = session
        self.lookup = lookup

    def post(self):
        update = json.loads(self.request.body)
        if 'message' in update and 'text' in update['message']:
            query = update['message']['text']
            logging.info(f'query: {query}')
            hits = self.lookup.lookup(query)
            logging.info(f'hits: {hits}')
            response = None
            if hits:
                best = hits[0].object
                response = format_result(self.session, best)
            response = response or 'No results!'
            self.write({'method': 'sendMessage', 'chat_id': update['message']['chat']['id'], 'text': response,
                        'parse_mode': 'markdown'})


def set_webhook(bot_token, host):
    client = tornado.httpclient.HTTPClient()
    webhook_url = f'https://{host}/webhook'
    request = tornado.httpclient.HTTPRequest(
        f'https://api.telegram.org/bot{bot_token}/setWebhook?url={webhook_url}')
    logging.info(f'setting webhook to {webhook_url}')
    response = client.fetch(request, raise_error=False)
    result = json.loads(response.body.decode('utf-8'))
    if result['ok']:
        logging.info('webhook set successfully')
    else:
        logging.warning(f'failed to set webhook: {result}')
    client.close()


def make_app():
    return tornado.web.Application([
        ('/webhook', WebhookHandler, dict(session=session, lookup=lookup)),
    ])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sentry_sdk.init()

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--set-webhook', action='store_true', help='Sets the bot webhook before starting.')
    parser.add_argument('-p', '--port', help='Port to listen on')
    args = parser.parse_args()

    if args.set_webhook:
        bot_token = os.getenv('ROTOM_BOT_TOKEN')
        if not bot_token:
            logging.critical('ROTOM_BOT_TOKEN not set')
            sys.exit(1)

        host = os.getenv('ROTOM_HOST')
        if not host:
            logging.critical('ROTOM_HOST not set')
            sys.exit(1)

        set_webhook(bot_token, host)

    app = make_app()

    port = args.port or os.getenv('PORT') or 8080
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()
