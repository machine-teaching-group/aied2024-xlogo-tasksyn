from z3 import And, Implies, Not, Const, If, Sum
from src.xlogomini.smt.constraints.base_constraint_smt import *


class StartByConstraintSMT(BaseConstraintSMT):
    def __init__(self, js):
        BaseConstraintSMT.__init__(self, js)
        self.id = 'start'

        self.mutated = False
        self.vars = self._build_vars()

    def _build_vars(self):
        vars = {}
        vars[f"start_name"] = [Const(f"start_name__{i}", Block) for i in range(len(self.js))]
        return vars

    def properties(self):
        C = [
            self.properties_for_similar_cons(),
            self.properties_for_size(min_size=max(len(self.js) - 1, 0),
                                     max_size=min(len(self.js) + 2, 4)),
            self.properties_for_disabling_block(repeat),
            self.properties_for_disabling_block(setpc),
            self.properties_for_disabling_block(allblocks)
        ]

        return And(C)

    def mutate(self):
        self.mutated = True
        i = len(self.vars['start_name'])
        self.vars["start_name"].append(Const(f"start_name__{i}", Block))

    def to_json(self, model_values):
        js = []
        for i in range(len(self.vars['start_name'])):
            if model_values[f"start_name"][i] == noblock:
                pass
            else:
                js.append(str(model_values[f"start_name"][i]))
        return js
