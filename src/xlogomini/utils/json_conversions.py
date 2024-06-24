from src.xlogomini.utils.enums import NAME_VARS, COLOR_VARS
import numpy as np
import json


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return json.JSONEncoder.default(self, obj)


def dict2json(task_dict, filename):
    """
    save task_dict to json file
    """
    with open(filename, 'w') as f:
        json.dump(task_dict, f, cls=NpEncoder)


def cnf2json(cnf):
    spec_json = []
    for c in cnf:
        clause = []
        for l in c:
            if l in NAME_VARS:
                clause.append({"name": l, "neg": 0})
            elif l in COLOR_VARS:
                clause.append({"color": l, "neg": 0})
        # TODO parse the negation
        spec_json.append(clause)
    return spec_json
