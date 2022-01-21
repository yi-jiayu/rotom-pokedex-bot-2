from python:3.10

copy . /app

run pip install -r /app/requirements.txt

run pokedex setup -v

workdir /app
entrypoint ["/usr/local/bin/python", "/app/server.py"]
