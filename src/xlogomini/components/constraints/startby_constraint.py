from src.xlogomini.components.constraints.base_constraint import *


class StartByConstraints(BaseConstraints):
    def __init__(self, json):
        BaseConstraints.__init__(self, json)

    def __repr__(self):
        """
        E.g., "'right', 'left', 'forward'.
        """
        if len(self.cons) == 0:
            return ""
        middle = ''
        for cmd in self.cons:
            middle += f", '{BLOCK_FULLNAME[cmd]}'"
        return middle[2:]

    def toPytorchTensor(self):
        """
        Features: [[fd, bk, lt, rt],
                   [fd, bk, lt, rt],
                   [fd, bk, lt, rt],
                   [fd, bk, lt, rt],
                   [fd, bk, lt, rt]
                  ]
        """
        fields = ['fd', 'bk', 'lt', 'rt']
        MAX_LEN = 5
        tensor = [0] * len(fields) * MAX_LEN

        for i, blk in enumerate(self.cons):
            if blk == 'fd':
                tensor[i * len(fields) + 0] = 1
            elif blk == 'bk':
                tensor[i * len(fields) + 1] = 1
            elif blk == 'lt':
                tensor[i * len(fields) + 2] = 1
            elif blk == 'rt':
                tensor[i * len(fields) + 3] = 1
            else:
                raise ValueError(f"{blk} not recognized")
        return tensor

    def __len__(self):
        return len(self.cons)

    def __getitem__(self, item):
        return self.cons[item]
