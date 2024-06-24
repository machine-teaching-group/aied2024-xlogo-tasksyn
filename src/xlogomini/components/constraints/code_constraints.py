import numpy as np
from src.xlogomini.components.constraints.atmost_constraint import *
from src.xlogomini.components.constraints.startby_constraint import *


class CodeConstraints(object):
    """
    This module defines the `CodeConstraints` class, which handles various constraints
    related to code blocks, including exactly, at most, and start by constraints. It
    also includes methods for converting these constraints to different formats and
    validating them.
    """
    def __init__(self, json):
        """
        Initializes the `CodeConstraints` object with the given JSON constraints.

        Example of json:
        -----------------
        {
            "exactly": {"all": 2},
            "start_by": ["fd", "lt"],
            "at_most": {"all": 5, "fd": 3, "lt": 2}
        }

        Parameters:
            json (dict or list of dict): The constraints in JSON format.
        """
        if type(json) == dict:
            self.json = json
        elif type(json) == list:
            if len(json) == 1:
                json = json[0]
            else:
                json = {}
            self.json = json

        self.exactly = ExactlyConstraints(json['exactly']) if 'exactly' in json.keys() else ExactlyConstraints({})
        self.most = AtMostConstraints(json['at_most']) if 'at_most' in json.keys() else AtMostConstraints({})
        self.start = StartByConstraints(json['start_by']) if 'start_by' in json.keys() else StartByConstraints([])

    def at_least(self, block_name):
        """
        Returns the minimal number of blocks allowed for the given block name.

        Parameters:
            block_name (str): The name of the block, could be {'fd', 'bk', 'lt', 'rt', 'repeat', 'all'}.

        Returns:
            int: The minimal number of blocks allowed for the block name.
        """
        if block_name in self.exactly.cons.keys():
            return self.exactly[block_name]
        else:
            return 0

    def at_most(self, block_name):
        """
        Returns the maximal number of blocks allowed for the given block name.

        Parameters:
            block_name (str): The name of the block, could be {'fd', 'bk', 'lt', 'rt', 'repeat', 'all'}.

        Returns:
            int: The maximal number of blocks allowed for the block name.
        """
        assert not ((block_name in self.exactly.cons.keys()) and (block_name in self.most.cons.keys()))
        if block_name in self.exactly.cons.keys():
            return self.exactly[block_name]
        if block_name in self.most.cons.keys():
            return self.most[block_name]
        else:
            return float('inf')

    def to_json(self):
        """
        Returns the constraints as a JSON object.

        Returns:
            dict: The constraints in JSON format.
        """
        return self.json

    def to_xlogo_json(self):
        """
        Converts the constraints into a format compatible with xlogo.

        Returns:
            dict: The constraints in xlogo compatible format.
        """
        xlogo_json = {}

        for k, v in self.exactly.cons.items():
            if 'constraints' not in xlogo_json.keys():
                xlogo_json["constraints"] = []

            if k == 'all':
                xlogo_json['constraints'].append({'total': {"type": 'eq', "amount": v}})
            else:
                xlogo_json['constraints'].append({k: {"type": 'eq', "amount": v}})

        for k, v in self.most.cons.items():
            if 'constraints' not in xlogo_json.keys():
                xlogo_json["constraints"] = []

            if k == 'all':
                xlogo_json['constraints'].append({'total': {'type': 'lte', 'amount': v}})
            else:
                xlogo_json['constraints'].append({k: {"type": 'lte', "amount": v}})

        for i, k in enumerate(self.start.cons):
            if 'solutionPrefix' not in xlogo_json.keys():
                xlogo_json['solutionPrefix'] = ''

            if k in ['fd', 'bk']:
                xlogo_json['solutionPrefix'] += f'{k} 100'
            elif k in ['lt', 'rt']:
                xlogo_json['solutionPrefix'] += f'{k} 90'
            else:
                raise ValueError(f"{k} not recognized")

            if i != len(self.start.cons) - 1:
                xlogo_json['solutionPrefix'] += ' '

        return xlogo_json

    def toPytorchTensor(self):
        """
        Converts the constraints into a PyTorch tensor.

        Returns:
            torch.Tensor: The constraints as a PyTorch tensor.
        """
        import torch
        cons_tensor = torch.Tensor(np.concatenate([
            self.exactly.toPytorchTensor(),
            self.most.toPytorchTensor(),
            self.start.toPytorchTensor()
        ]))
        return cons_tensor

    def is_empty(self):
        """
        Checks if the constraints are empty.

        Returns:
            bool: True if the constraints are empty, False otherwise.
        """
        n_cons = len(self.exactly.cons) + len(self.most.cons) + len(self.start.cons)
        return n_cons == 0

    def __getitem__(self, block_name):
        """
        Returns the minimal and maximal allowed blocks for the given block name.

        Parameters:
            block_name (str): The name of the block, could be {'fd', 'bk', 'lt', 'rt', 'repeat', 'all'}.

        Returns:
            tuple: The minimal and maximal allowed blocks for the block name.
        """
        return (self.at_least(block_name), self.at_most(block_name))

    def __repr__(self):
        """
        Returns a human-readable string representation of the constraints.

        Returns:
            str: The string representation of the constraints.
        """
        string_list = []

        exactly_without_0 = {k: v for k, v in self.exactly.cons.items() if v != 0}
        most_without_0 = {k: v for k, v in self.most.cons.items() if v != 0}
        without_using = {}
        without_using.update({k: v for k, v in self.exactly.cons.items() if v == 0})
        without_using.update({k: v for k, v in self.most.cons.items() if v == 0})

        def generate_output_string(d):
            mapping = {
                "fd"    : "forward",
                "bk"    : "backward",
                "lt"    : "left",
                "rt"    : "right",
                'setpc' : "set pen color",
                'repeat': "repeat",
                'all'   : "commands"
            }

            items = []

            for key, value in d.items():
                if key in mapping:
                    if value == 0:
                        items.append(f"'{mapping[key]}'")
                    else:
                        if mapping[key] == 'commands':
                            items.append(f"{value} {mapping[key]}")
                        else:
                            items.append(f"{value} '{mapping[key]}'")

            items = sorted(items, key=lambda x: 'command' in x)

            if len(items) == 1:
                return items[0]
            elif len(items) == 2:
                return " and ".join(items)
            elif len(items) > 2:
                return ", ".join(items[:-1]) + " and " + items[-1]
            else:
                return ""

        str_exactly = generate_output_string(exactly_without_0)
        str_most = generate_output_string(most_without_0)
        str_without_list = [generate_output_string({k: v}) for k, v in without_using.items()]

        if str(self.start) != '':
            string_list.append('start by using' + str(self.start))
        if str_exactly != '':
            string_list.append("use exactly " + str_exactly)
        if str_most != '':
            string_list.append("use at most " + generate_output_string(most_without_0))

        for str_without in str_without_list:
            if str_without != '':
                string_list.append("don't use " + str_without)

        number2letter = {
            1: "a",
            2: "b",
            3: "c",
            4: "d",
            5: "e",
            6

             : "f",
            7: "g"
        }

        if len(string_list) == 0:
            return ''
        elif len(string_list) == 1:
            return string_list[0].lower().capitalize()
        else:
            all_str = "Follow these rules: "
            for index, string in enumerate(string_list):
                all_str += f"({number2letter[index + 1]}) {string.capitalize()}. "
            return all_str.strip()

    def __hash__(self):
        """
        Returns the hash of the constraints representation.

        Returns:
            int: The hash value of the constraints representation.
        """
        return hash(self.__repr__())