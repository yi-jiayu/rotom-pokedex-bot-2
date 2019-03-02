import argparse
import json
import logging
import os
import sys

from pokedex.lookup import PokedexLookup
from pokedex.db import connect, tables

import tornado.httpclient
import tornado.ioloop
import tornado.web

session = connect()
lookup = PokedexLookup(session=session)


def format_pokemon(pokemon: tables.Pokemon):
    return f'''*{pokemon.name} (#{pokemon.id})*
{'/'.join(t.name for t in pokemon.types)}
Abilities: {', '.join(a.name for a in pokemon.abilities)}'''


def format_ability(ability: tables.Ability):
    return f'''*{ability.name}* (Ability)
{ability.effect}'''


def format_item(item: tables.Item):
    return f'''*{item.name}* (Item)
{item.effect}'''


def format_move(move: tables.Move):
    return f'''*{move.name}* (Move)
Type: {move.type.name}
Power: {move.power}
Accuracy: {move.accuracy}
PP: {move.pp}
{move.effect}'''


def format_result(result):
    if isinstance(result, tables.PokemonSpecies):
        return format_pokemon(result.default_pokemon)
    elif isinstance(result, tables.PokemonForm):
        return format_pokemon(result.pokemon)
    elif isinstance(result, tables.Item):
        return format_item(result)
    elif isinstance(result, tables.Ability):
        return format_ability(result)
    elif isinstance(result, tables.Move):
        return format_move(result)


class WebhookHandler(tornado.web.RequestHandler):
    def initialize(self, lookup):
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
                response = format_result(best)
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
        ('/webhook', WebhookHandler, dict(lookup=lookup)),
    ])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--set-webhook', action='store_true', help='Sets the bot webhook before starting.')
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
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()
