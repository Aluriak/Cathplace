"""Definition of general-purpose functions"""

import clyngor


def load_humans() -> (str, str):
    "Yield pairs of (name, team)"
    for model in clyngor.solve('data/humans.lp').by_predicate.careful_parsing.int_not_parsed:
        for args in model['human']:
            if len(args) == 1:
                yield args[0], None
            elif len(args) == 2:
                yield args
            elif len(args) >= 3 or not args:
                print(f'ERROR: unhandled human "{args}"')

def load_desks() -> [(int, int), (str, str)]:
    "Yield (room name, desk name, position x, position y) found in export-offices.lp"
    for model in clyngor.solve('data/offices.lp').by_predicate.careful_parsing.int_not_parsed:
        for args in model.get('desk_px', ()):
            if len(args) == 4:
                room, name, x, y = args
                yield (int(x), int(y)), (room.strip('"'), name.strip('"'))
            else:
                print(f'ERROR: unhandled desk "{args}"')

def call_placement_engine():
    models = clyngor.solve(('data/humans.lp', 'data/offices.lp', 'engine.lp'), options='--opt-mode=optN')
    for model in models.by_predicate.careful_parsing.int_not_parsed:
        yield model['place']


def name_to_color(name:str) -> str:
    return 'red'  # sorry

def string_to_asp(string:str) -> str:
    string = string.strip()
    if not string:
        return '""'
    first = string[0]
    if first.isupper() or (first.isdigit() and not all(c.isdigit() for c in string)) or first == '_':
        return '"' + string + '"'
    else:
        return string

