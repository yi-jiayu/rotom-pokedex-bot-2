#!/bin/sh -

set -e

PIPENV_PATH=$(which pipenv)
export PIPENV_PATH

ROTOM_BOT_TOKEN=
ROTOM_HOST=

export ROTOM_BOT_TOKEN
export ROTOM_HOST

SENTRY_AUTH_TOKEN=
SENTRY_DSN=
SENTRY_ENVIRONMENT=
SENTRY_ORG=

export SENTRY_AUTH_TOKEN
export SENTRY_DSN
export SENTRY_ENVIRONMENT
export SENTRY_ORG

SENTRY_RELEASE=$(sentry-cli releases propose-version)

export SENTRY_RELEASE

# Create a release
sentry-cli releases new -p rotom-pokedex-bot-2 $SENTRY_RELEASE

# Associate commits with the release
sentry-cli releases set-commits --auto $SENTRY_RELEASE

envsubst < rotom-pokedex-bot.service > rotom-pokedex-bot.service~
sudo mv rotom-pokedex-bot.service~ /etc/systemd/system/rotom-pokedex-bot.service

sudo systemctl daemon-reload
sudo systemctl restart rotom-pokedex-bot

sentry-cli releases deploys $SENTRY_RELEASE new -e $SENTRY_ENVIRONMENT
