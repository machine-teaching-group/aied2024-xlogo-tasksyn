from src.xlogomini.components.goal.objective import Objective


class Goal(object):
    """
    This module defines the `Goal` class, which represents a collection of objectives.
    It provides methods for initializing goals from JSON, retrieving objective names and
    constraints, converting goals to different formats, and various utility functions.

    """
    def __init__(self, objs):
        """
        Initializes the `Goal` object with a dictionary of objectives.

        Parameters:
            objs (dict): A dictionary of objectives.
        """
        assert isinstance(objs, dict)
        self.objs = objs
        self.n_objs = len(self.objs)

    @classmethod
    def init_from_json(cls, goal_json):
        """
        Class method to initialize a `Goal` object from a JSON representation.

        Parameters:
            goal_json (list): A list of dictionaries representing the objectives.

        Returns:
            Goal: An instance of the `Goal` class.
        """
        objs = {}

        for obj_js in goal_json:
            obj = Objective.init_from_json(obj_js)
            if obj.obj_name not in objs.keys():
                objs[obj.obj_name] = [obj]
            else:
                objs[obj.obj_name].append(obj)
        return cls(objs)

    def _get_list_of_obj_names(self):
        """
        Returns a list of objective names.

        Returns:
            list: A list of objective names.
        """
        return self.objs.keys()

    def get_cnfs(self):
        """
        Returns a dictionary with lists of target CNFs and forbidden CNFs for each objective.

        Returns:
            dict: A dictionary with lists of CNFs for each objective.
        """
        cnfs = {}
        for name in self.objs.keys():
            if isinstance(self.objs[name], list):
                cnfs[name] = [s.cnf for o in self.objs[name] for s in o.specs]
            else:
                cnfs[name] = [s.cnf for s in self.objs[name].specs]
        return cnfs

    def to_json(self):
        """
        Converts the goal to a JSON representation.

        Returns:
            list or None: A list of JSON representations of the objectives, or None if 'draw' is in the objective names.
        """
        if 'draw' in self._get_list_of_obj_names():
            return None
        else:
            return [obj.to_json() for k in self.objs.keys() for obj in self.objs[k]]

    def toPytorchTensor(self):
        """
        Converts the goal to a PyTorch tensor.

        Returns:
            torch.Tensor: A tensor representation of the goal.
        """
        import torch as th
        goal_tensor = []
        for objs in self.objs.values():
            for obj in objs:
                goal_tensor.append(obj.toPytorchTensor())
        while True:
            if len(goal_tensor) < 3:
                goal_tensor.append(th.zeros_like(goal_tensor[0]))
            else:
                break
        goal_tensor = th.concat(goal_tensor)
        assert goal_tensor.shape[0] == 564
        return goal_tensor

    def __getitem__(self, obj_name):
        """
        Returns the objectives associated with the given objective name.

        Parameters:
            obj_name (str): The name of the objective.

        Returns:
            list: A list of objectives associated with the given name.

        Raises:
            ValueError: If the objective name does not exist.
        """
        if obj_name not in self.objs.keys():
            raise ValueError(f"{obj_name} not exists")
        return self.objs[obj_name]

    def __len__(self):
        """
        Returns the number of objectives in the goal.

        Returns:
            int: The number of objectives.
        """
        return len(self.objs)

    def __repr__(self):
        """
        Returns a human-readable string representation of the goal.

        Returns:
            str: The string representation of the goal.
        """
        goal_str = ''
        for obj in self.objs:
            if isinstance(self.objs[obj], list):
                for obj in self.objs[obj]:
                    if obj.obj_name == 'forbid' and 'without' in goal_str:
                        obj_str = str(obj)
                        obj_str = obj_str.replace('without standing on a', 'and')
                        goal_str += f"{obj_str} "
                    else:
                        goal_str += f"{obj} "
            else:
                goal_str += f"{self.objs[obj]}"
        return goal_str.strip()

    def __hash__(self):
        """
        Returns the hash of the goal representation.

        Returns:
            int: The hash value of the goal representation.
        """
        return hash(self.__repr__())

    def __eq__(self, other):
        """
        Checks if two `Goal` objects are equal.

        Parameters:
            other (Goal): Another `Goal` object to compare with.

        Returns:
            bool: True if the goals are equal, False otherwise.
        """
        if isinstance(other, Goal):
            if self.n_objs != other.n_objs:
                return False
            for obj_name in self.objs.keys():
                for i in range(len(self.objs[obj_name])):
                    if self.objs[obj_name][i] != other.objs[obj_name][i]:
                        return False
            return True
        else:
            return False
