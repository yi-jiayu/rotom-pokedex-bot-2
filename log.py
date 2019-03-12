import logging


def _build_message(**kwargs):
    fields = []
    for key, value in kwargs.items():
        v = value if isinstance(value, str) else repr(value)
        v = f'"{v}"' if ' ' in v else v
        fields.append((key, v))
    return ' '.join(f'{k}={v}' for k, v in fields)


def info(**kwargs):
    logging.info(_build_message(**kwargs))


def debug(**kwargs):
    logging.debug(_build_message(**kwargs))
