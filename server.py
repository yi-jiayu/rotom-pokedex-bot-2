import asyncio
import argparse
import json
import logging
import os
import sys

from typing import Optional

from pokedex.db import tables

import sentry_sdk

import tornado.httpclient
import tornado.ioloop
import tornado.web

import entries
import log
import type_efficacy
from app import lookup, session

# 40 characters should be more than enough to query anything in the Pokédex
MAX_QUERY_LENGTH = 40


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


def pokemon_thumbnail_image_url(pokemon_id):
    return f'https://assets.pokemon.com/assets/cms2/img/pokedex/detail/{pokemon_id:03}.png'


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
        s += f'\n[Image]({pokemon_full_image_url(pokemon.id)})'
    return s


def format_pokemon_inline_result(session, pokemon: tables.Pokemon):
    result = {
        'type': 'article',
        'id': f'pokemon#{pokemon.id}',
        'title': f'{pokemon.name} (#{pokemon.id:03})',
        'input_message_content': {
            'message_text': format_pokemon(session, pokemon),
            'parse_mode': 'Markdown',
        },
        'description': '/'.join(t.name for t in pokemon.types),
    }
    if pokemon.id < 10000:
        result['thumb_url'] = pokemon_thumbnail_image_url(pokemon.id)
    return result


def format_ability(ability: tables.Ability):
    return f'''*{ability.name}* (ability)
{ability.effect}'''


def format_ability_inline_result(ability: tables.Ability):
    return {
        'type': 'article',
        'id': f'ability#{ability.id}',
        'title': f'{ability.name} (ability)',
        'input_message_content': {
            'message_text': format_ability(ability),
            'parse_mode': 'Markdown',
        },
        'description': str(ability.short_effect),
    }


def format_item(item: tables.Item):
    return f'''*{item.name}* (item)
{item.effect}'''


def format_item_inline_result(item: tables.Item):
    return {
        'type': 'article',
        'id': f'item#{item.id}',
        'title': f'{item.name} (item)',
        'input_message_content': {
            'message_text': format_item(item),
            'parse_mode': 'Markdown',
        },
        'description': str(item.short_effect),
    }


def format_move(move: tables.Move):
    return f'''*{move.name}* (move)
Type: {move.type.name}
Power: {move.power}
Accuracy: {move.accuracy}
PP: {move.pp}
{move.effect}'''


def format_move_inline_result(move: tables.Move):
    return {
        'type': 'article',
        'id': f'move#{move.id}',
        'title': f'{move.name} (move)',
        'input_message_content': {
            'message_text': format_move(move),
            'parse_mode': 'Markdown',
        },
        'description': str(move.short_effect),
    }


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


def format_inline_result(session, result):
    if isinstance(result, tables.PokemonSpecies):
        return format_pokemon_inline_result(session, result.default_pokemon)
    elif isinstance(result, tables.PokemonForm):
        return format_pokemon_inline_result(session, result.pokemon)
    elif isinstance(result, tables.Ability):
        return format_ability_inline_result(result)
    elif isinstance(result, tables.Item):
        return format_item_inline_result(result)
    elif isinstance(result, tables.Move):
        return format_move_inline_result(result)


def handle_text_message(message):
    query = message['text'][:MAX_QUERY_LENGTH]
    chat_id = message['chat']['id']
    hits = lookup(query)
    log.info(query=query, hits=hits, type='text_message', chat_id=chat_id, message_id=message['message_id'])
    text = None
    reply_markup = None
    if hits:
        best = hits[0].object
        entry = entries.Entry.from_model(best)
        if entry:
            section = entry.default_section()
            text = section.content
            reply_markup = entries.reply_markup_for_section(section)
    text = text or 'No results!'
    response = {'method': 'sendMessage',
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'markdown'}
    if reply_markup:
        response['reply_markup'] = json.dumps(reply_markup)
    return response


def handle_inline_query(inline_query):
    query = inline_query['query'][:MAX_QUERY_LENGTH]
    inline_query_id = inline_query['id']
    if query:
        hits = lookup(query)
        log.info(query=query, hits=hits, type='inline_query', inline_query_id=inline_query_id)
        entries_ = filter(None, (entries.Entry.from_model(h.object) for h in hits))
        results = list(entries.inline_result_for_entry(e) for e in entries_)
        serialised_results = json.dumps(results) if results else ''
    else:
        serialised_results = ''
    return {
        'method': 'answerInlineQuery',
        'inline_query_id': inline_query_id,
        'results': serialised_results,
    }


def get_entry(table: str, id_: int) -> Optional[entries.Entry]:
    if table == 'pokemon':
        return entries.PokemonEntry.from_pokemon_id(id_)


async def answer_callback_query(http_client, bot_token, callback_query, text=''):
    url = f'https://api.telegram.org/bot{bot_token}/answerCallbackQuery'
    data = {'callback_query_id': callback_query['id']}
    if text:
        data['text'] = text
    body = json.dumps(data)
    headers = {'Content-Type': 'application/json'}
    request = tornado.httpclient.HTTPRequest(url, 'POST', headers, body)
    return await http_client.fetch(request, raise_error=False)


async def update_message(http_client, bot_token, callback_query, text, reply_markup):
    url = f'https://api.telegram.org/bot{bot_token}/editMessageText'
    data = {'text': text, 'parse_mode': 'Markdown'}
    if 'inline_message_id' in callback_query:
        data['inline_message_id'] = callback_query['inline_message_id']
    else:
        data['chat_id'] = callback_query['message']['chat']['id']
        data['message_id'] = callback_query['message']['message_id']
    if text:
        data['text'] = text
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)
    body = json.dumps(data)
    headers = {'Content-Type': 'application/json'}
    request = tornado.httpclient.HTTPRequest(url, 'POST', headers, body)
    return await http_client.fetch(request, raise_error=False)


async def handle_callback_query(http_client, bot_token, callback_query):
    try:
        data = callback_query['data']
        table, id_, path = data.split('/', maxsplit=3)
        entry = get_entry(table, int(id_))
        if entry is None:
            raise ValueError
        section = entry.section(path)
        if section is None:
            raise ValueError
        text = section.content
        reply_markup = entries.reply_markup_for_section(section)
        results = await asyncio.gather(
            answer_callback_query(http_client, bot_token, callback_query),
            update_message(http_client, bot_token, callback_query, text, reply_markup),
        )
        for r in results:
            details = json.loads(r.body)
            if not details.get('ok'):
                logging.warning(details)
    except ValueError:
        return {'method': 'answerCallbackQuery',
                'callback_query_id': callback_query['id'],
                'text': 'Invalid callback data!'}


class WebhookHandler(tornado.web.RequestHandler):
    def initialize(self, bot_token, http_client):
        self.bot_token = bot_token
        self.http_client: tornado.httpclient.AsyncHTTPClient = http_client

    async def post(self):
        update = json.loads(self.request.body)
        if 'message' in update and 'text' in update['message']:
            response = handle_text_message(update['message'])
            self.write(response)
        elif 'inline_query' in update:
            response = handle_inline_query(update['inline_query'])
            self.write(response)
        elif 'callback_query' in update:
            response = await handle_callback_query(self.http_client, self.bot_token, update['callback_query'])
            if response:
                self.write(response)


def set_webhook(bot_token, host):
    client = tornado.httpclient.HTTPClient()
    webhook_url = f'https://{host}/webhook'
    request = tornado.httpclient.HTTPRequest(
        f'https://api.telegram.org/bot{bot_token}/setWebhook?url={webhook_url}')
    log.info(message='setting webhook', url=webhook_url)
    response = client.fetch(request, raise_error=False)
    result = json.loads(response.body.decode('utf-8'))
    if not result['ok']:
        logging.warning(f'failed to set webhook: {result}')
    client.close()


def make_app(bot_token):
    http_client = tornado.httpclient.AsyncHTTPClient()
    return tornado.web.Application([
        ('/webhook', WebhookHandler, {'bot_token': bot_token, 'http_client': http_client}),
    ])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sentry_sdk.init()

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--set-webhook', action='store_true', help='Sets the bot webhook before starting.')
    parser.add_argument('-p', '--port', help='Port to listen on')
    args = parser.parse_args()

    bot_token = os.getenv('ROTOM_BOT_TOKEN')
    if not bot_token:
        logging.critical('ROTOM_BOT_TOKEN not set')
        sys.exit(1)

    if args.set_webhook:

        host = os.getenv('ROTOM_HOST')
        if not host:
            logging.critical('ROTOM_HOST not set')
            sys.exit(1)

        set_webhook(bot_token, host)

    app = make_app(bot_token)

    port = args.port or os.getenv('PORT') or 8080
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()
