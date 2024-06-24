from src.xlogomini.smt.code.base_block_smt import *
from z3 import And, Int, Const, Or, If


class ActionSMT(BaseBlockSMT):
    def __init__(self, js, id):
        BaseBlockSMT.__init__(self, js, id)
        self.vars = self._build_vars()

    def _build_vars(self):
        vars = {}
        vars[f'block__{self.id}'] = Const(f"block__{self.id}", Block)
        return vars

    def properties(self):
        if self.js is None:
            return Or(
                self.vars[f'block__{self.id}'] == fd,
                self.vars[f'block__{self.id}'] == bk,
                self.vars[f'block__{self.id}'] == lt,
                self.vars[f'block__{self.id}'] == rt,
                self.vars[f'block__{self.id}'] == noblock,
            )
        else:
            if self.js['type'] == 'fd':
                return self.vars[f'block__{self.id}'] == fd
            elif self.js['type'] == 'bk':
                return self.vars[f'block__{self.id}'] == bk
            # if self.js['type'] in ['fd', 'bk']:
            #     return Or(
            #         self.vars[f'block__{self.id}'] == fd,
            #         self.vars[f'block__{self.id}'] == bk,
            #         # self.vars[f'block__{self.id}'] == noblock,
            #     )
            elif self.js['type'] in ['lt', 'rt']:
                return Or(
                    self.vars[f'block__{self.id}'] == lt,
                    self.vars[f'block__{self.id}'] == rt,
                    # self.vars[f'block__{self.id}'] == noblock,
                )
            else:
                raise ValueError(f"{self.js['type']} not recognized!")

    def target_block_cnt(self, block, mutated):
        """
        Return a smt formula that represents the number of `block`.
        """
        if mutated:
            return If(self.vars[f'block__{self.id}'] == block, 1, 0)
        else:
            return 1 if str(block) == self.js['type'] else 0

    def total_block_cnt(self, mutated):
        if mutated:
            return If(self.vars[f'block__{self.id}'] != noblock, 1, 0)
        else:
            return 1

    def __len__(self):
        return 1

    def to_json(self, model_values):
        block = model_values[f'block__{self.id}']
        if block == noblock:
            return None
            # return {"type": str(model_values[f'block__{self.id}'])}
        else:
            return {"type": str(model_values[f'block__{self.id}'])}
