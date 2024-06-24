from src.xlogomini.components.goal.spec import Spec
from src.xlogomini.utils.enums import ITEM_COLOR


class Objective(object):
    """
    This module defines the `Objective` class, which represents an objective with
    specific constraints and specifications.
    """
    def __init__(self, obj_name, specs, total_cnt=None):
        """
        Initializes the `Objective` object with a name, specifications, and an optional total count.

        Parameters:
            obj_name (str): The name of the objective.
            specs (list): A list of specifications for the objective.
            total_cnt (int, optional): The total count for 'sum' objectives. Defaults to None.
        """
        self.obj_name = obj_name
        self.specs = specs
        self.total_cnt = total_cnt

        if obj_name == 'sum':
            assert self.total_cnt is not None
        else:
            assert self.total_cnt is None

        if obj_name == 'concat':
            assert len(specs) > 1
        else:
            assert len(specs) == 1

    @classmethod
    def init_from_json(cls, obj_json):
        """
        Class method to initialize an `Objective` object from a JSON representation.

        Parameters:
            obj_json (dict): A dictionary representing the objective.

        Returns:
            Objective: An instance of the `Objective` class.
        """
        obj_name = obj_json['name']
        specs = [Spec.init_from_json(spec) for spec in obj_json['specs']]
        total_cnt = obj_json['total_cnt'] if 'total_cnt' in obj_json.keys() else None

        return cls(obj_name, specs, total_cnt)

    def to_json(self):
        """
        Converts the objective to a JSON representation.

        Returns:
            dict: A dictionary representing the objective.
        """
        specs_json = [spec.to_json() for spec in self.specs]
        obj_json = {
            "name" : self.obj_name,
            "specs": specs_json
        }
        if self.obj_name == 'sum':
            obj_json['total_cnt'] = self.total_cnt
        return obj_json

    def toPytorchTensor(self):
        """
        Converts the objective to a PyTorch tensor.

        Returns:
            torch.Tensor: A tensor representation of the objective.
        """
        import torch as th
        MAX_SPECS = 3
        name = ['find', 'forbid', 'findonly', 'concat', 'sum', 'collectall', 'draw']
        name_tensor = th.zeros(len(name))
        name_tensor[name.index(self.obj_name)] = 1

        specs_tensor = []
        for i, s in enumerate(self.specs):
            if i >= MAX_SPECS:
                break
            specs_tensor.append(s.toPytorchTensor())
        while len(specs_tensor) < MAX_SPECS:
            specs_tensor.append(th.zeros_like(specs_tensor[0]))
        specs_tensor = th.stack(specs_tensor).flatten()

        cnt_tensor = th.Tensor([0 if self.total_cnt is None else self.total_cnt])

        obj_tensor = th.concat([name_tensor, specs_tensor, cnt_tensor])

        assert name_tensor.shape[0] == 7
        assert specs_tensor.shape[0] == 180
        assert cnt_tensor.shape[0] == 1
        assert obj_tensor.shape[0] == 188
        return obj_tensor

    def __str__(self):
        """
        Returns a human-readable string representation of the objective.

        Returns:
            str: The string representation of the objective.
        """
        if self.obj_name == 'collectall':
            if str(self.specs[0]) in ITEM_COLOR:
                prefix = f'Collect all {self.specs[0]} objects'
            else:
                prefix = f'Collect all {self.specs[0]}'
        elif self.obj_name == 'find':
            prefix = f'Find the {self.specs[0]}'
        elif self.obj_name == 'forbid':
            prefix = f'without standing on a {self.specs[0]}'
        elif self.obj_name == 'sum':
            prefix = f'Collect exactly {self.total_cnt} {self.specs[0]}'
            if self.total_cnt > 1:
                prefix = prefix.replace('strawberry', 'strawberries')
                prefix = prefix.replace('lemon', 'lemons')
        elif self.obj_name == 'findonly':
            prefix = f'Find only the {self.specs[0]}'
        elif self.obj_name == 'concat':
            prefix = f'First find the {str(self.specs[0])}, '
            prefix += f'then the {str(self.specs[1])}, '
            for x in self.specs[2:-1]:
                prefix += f'{str(x)},'
            prefix += f'finally the {str(self.specs[-1])}'
        elif self.obj_name == 'draw':
            prefix = 'Draw the picture'
        else:
            raise ValueError(f"{self.obj_name} not recognized")
        return f'{prefix}'

    def __eq__(self, other):
        """
        Checks if two `Objective` objects are equal.

        Parameters:
            other (Objective): Another `Objective` object to compare with.

        Returns:
            bool: True if the objectives are equal, False otherwise.
        """
        if isinstance(other, Objective):
            return self.__str__() == str(other)
        else:
            return False
