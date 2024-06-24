from z3 import And, Sum, If, Or
from src.xlogomini.smt.code.base_block_smt import Block, fd, bk, lt, rt, setpc, repeat, noblock, allblocks

CNT_MAX = 15
CNT_MIN = 0


class BaseConstraintSMT():
    def __init__(self, js):
        self.js = js
        self.id = None
        self.vars = {}

    def _build_vars(self):
        pass

    def properties(self):
        pass

    def properties_for_disabling_block(self, block):
        n = len(self.vars[f'{self.id}_name'])
        return And([self.vars[f'{self.id}_name'][i] != block for i in range(n)])

    def properties_for_size(self, min_size=0, max_size=2):
        non_empty = []
        for i in range(len(self.vars[f'{self.id}_name'])):
            non_empty.append(If(self.vars[f"{self.id}_name"][i] != noblock, 1, 0))
        size = Sum(non_empty)
        return And(size <= max_size, size >= min_size)

    def size_inc(self):
        non_empty = []
        for i in range(len(self.vars[f'{self.id}_name'])):
            non_empty.append(If(self.vars[f"{self.id}_name"][i] != noblock, 1, 0))
        size = Sum(non_empty) - len(self.js)
        return size

    def size_dec(self):
        non_empty = []
        for i in range(len(self.vars[f'{self.id}_name'])):
            non_empty.append(If(self.vars[f"{self.id}_name"][i] != noblock, 1, 0))
        size = len(self.js) - Sum(non_empty)
        return size

    def size(self):
        return self.size_inc() + len(self.js)


    def properties_for_similar_cons(self):
        """
        'lt/rt' can only be replaced with 'lt/rt'.
        'fd/bk' can only be replaced with 'bk/fd'
        'all' can only be replaced with 'allblocks'
        """
        if isinstance(self.js, dict):
            ref_blocks = self.js.keys()
        elif isinstance(self.js, list):
            ref_blocks = self.js
        else:
            raise ValueError(f"{self.js} not recognized")

        avail_blocks = [noblock]
        for key in ref_blocks:
            # lt/rt only mutate to lt/rt
            if key in ['lt', 'rt']:
                avail_blocks.extend([lt, rt])
            # fd/bk only mutate to fd/bk
            elif key in ['fd', 'bk']:
                avail_blocks.extend([fd, bk])
            elif key in ['all']:
                avail_blocks.extend([allblocks])

        n = len(self.vars[f'{self.id}_name'])
        return And([Or(list(map(lambda b: self.vars[f'{self.id}_name'][i] == b, avail_blocks)))
                    for i in range(n)])
