import json


def json_read(filename):
    with open(filename, 'r') as inf:
        res = json.load(inf)
    return res


def json_dump(obj, filename, ea=False, indent=4):
    with open(filename, 'w') as ouf:
        json.dump(obj, ouf, ensure_ascii=ea, indent=indent)
