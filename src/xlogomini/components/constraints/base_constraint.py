BLOCK_FULLNAME = {
    "fd"    : "forward",
    "bk"    : "backward",
    "lt"    : "left",
    "rt"    : "right",
    'repeat': "repeat"
}


class BaseConstraints():
    def __init__(self, json):
        self.cons = json

    def to_json(self):
        return self.cons

    def __repr__(self):
        pass

    def __getitem__(self, item):
        return self.cons[item]

    def toPytorchTensor(self):
        """
        Get the tensor for 'most' and 'exactly'.
        Features: [fd, fd_cnt, bk, bk_cnt, lt, lt_cnt, rt, rt_cnt, all, all_cnt]
        """
        tensor = [0] * 10
        for k, v in self.cons.items():
            if k == 'fd':
                tensor[0] = 1
                tensor[1] = int(v)
            elif k == 'bk':
                tensor[2] = 1
                tensor[3] = int(v)
            elif k == 'lt':
                tensor[4] = 1
                tensor[5] = int(v)
            elif k == 'rt':
                tensor[6] = 1
                tensor[7] = int(v)
            elif k == 'all':
                tensor[8] = 1
                tensor[9] = int(v)
        return tensor
