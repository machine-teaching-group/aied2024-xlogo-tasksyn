from src.xlogomini.smt.code.base_block_smt import *
from z3 import And, Int, Const, Or, If


class SetPCSMT(BaseBlockSMT):
    def __init__(self, js, id):
        BaseBlockSMT.__init__(self, js, id)
        self.vars = self._build_vars()

    def _build_vars(self):
        vars = {}
        vars[f'block__{self.id}'] = Const(f'block__{self.id}', Block)
        vars[f'value__{self.id}'] = Const(f'value__{self.id}', PColor)  # pen color
        return vars

    def properties(self):
        """
        The synthesized color should be the same as the reference color if the color is `white`.
        """
        BLK_IS_SETPC = self.vars[f'block__{self.id}'] == setpc
        BLK_WHITE = self.vars[f'value__{self.id}'] == white
        BLK_NOT_WHITE = self.vars[f'value__{self.id}'] != white
        CLR = Or(self.vars[f'value__{self.id}'] == red,
                 self.vars[f'value__{self.id}'] == green,
                 self.vars[f'value__{self.id}'] == blue,
                 self.vars[f'value__{self.id}'] == yellow,
                 self.vars[f'value__{self.id}'] == black,
                 self.vars[f'value__{self.id}'] == white)

        C = [
            BLK_IS_SETPC,
            CLR,
            BLK_WHITE if self.js['value'] == 'white' else BLK_NOT_WHITE
        ]
        return And(C)

    def target_block_cnt(self, block, mutated):
        if mutated:
            return If(setpc == block, 1, 0)
        else:
            return 1 if self.js['type'] == str(block) else 0

    def total_block_cnt(self, mutated):
        if mutated:
            return If(self.vars[f'block__{self.id}'] != noblock, 1, 0)
        else:
            return 1

    def __len__(self):
        return 1

    def to_json(self, model_values):
        return {
            "type" : 'setpc',
            "value": str(model_values[str(self.vars[f'value__{self.id}'])])
        }
