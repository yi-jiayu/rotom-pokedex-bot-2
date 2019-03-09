import json

with open('data/kalos.json') as f:
    pokemon = json.load(f)


class A:
    def m(self):
        pass

    @classmethod
    def cm(cls, self):
        cls.m(self)
