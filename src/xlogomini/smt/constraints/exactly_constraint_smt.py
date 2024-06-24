from z3 import Distinct, Int, And, Or, Implies, Sum, Not, IntVector, sat, Solver, Const, If
from src.xlogomini.smt.constraints.base_constraint_smt import *
from src.xlogomini.smt.code.base_block_smt import Block, fd, bk, lt, rt, setpc, repeat, noblock, allblocks


class ExactlyConstraintSMT(BaseConstraintSMT):
    def __init__(self, js):
        BaseConstraintSMT.__init__(self, js)
        self.mutated = False
        self.id = 'exactly'
        self.vars = self._build_vars()

    def _build_vars(self):
        vars = {}
        vars[f"{self.id}_name"] = [Const(f"{self.id}_name__{i}", Block) for i in range(len(self.js))]
        vars[f"{self.id}_cnt"] = IntVector(f"{self.id}_cnt", len(self.js))
        return vars

    def properties(self):
        C = [
            self.properties_for_noblock(),
            # self.properties_for_similar_cons(),

            # size of the constraint (e.g., {'fd':2, 'bk': 3} is of size 2)
            # self.properties_for_size(max_dec=max(len(self.js), 1), max_size=max(len(self.js) + 1, 2)),
            self.properties_for_size(min_size=0, max_size=min(len(self.js) + 1, 2)),
            # distinct names
            self.properties_for_distinct_names(),
            # disable blocks
            self.properties_for_disabling_block(repeat),
            self.properties_for_disabling_block(setpc),
            # range for different blocks
            self.properties_for_cnt_range(),
            self.properties_for_existence_of_allblocks(),
            self.properties_for_using_just()
        ]
        return And(C)

    def properties_for_using_just(self):
        """
        If the constraints in ref constraints satisfy this property,  this function would constrain
        the cnt for 'all' to be equivalent to the sum of cnts for other blocks.

        This constraint is especially designed for task 11:
        "Find the strawberry using just these 3 commands: 'forward', 'forward', 'right'"
        The constraints for this are: "exactly": {"fd": 2, "rt": 1, "all": 3}.
        """
        C = []
        if 'all' in self.js.keys():
            if self.js['all'] == sum([cnt for blk, cnt in self.js.items() if blk != 'all']):
                pass
                n = len(self.vars[f'{self.id}_name'])
                for i in range(n):
                    I_IS_ALLBLOCK = self.vars[f'{self.id}_name'][i] == allblocks
                    SUM_OF_CNT_EXCEPT_ALL = Sum([self.vars[f'{self.id}_cnt'][j] for j in range(n) if j != i])
                    CNT_FOR_ALL = self.vars[f'{self.id}_cnt'][i]
                    C.append(Implies(I_IS_ALLBLOCK, SUM_OF_CNT_EXCEPT_ALL == CNT_FOR_ALL))
        return And(C)

    def properties_for_noblock(self):
        C = []
        for i in range(len(self.vars[f'{self.id}_name'])):
            C.append(Implies(self.vars[f'{self.id}_name'][i] == noblock, self.vars[f'{self.id}_cnt'][i] == 0))
        return And(C)

    def properties_for_existence_of_allblocks(self):
        C = []
        n = len(self.vars[f'{self.id}_name'])

        # if `all` exists in ref constraint, then it should also be in the mutated constraint
        if 'all' in self.js.keys():
            C.append(Or(
                [self.vars[f'{self.id}_name'][i] == allblocks for i in range(n)]))
        # if `all` doesn't exist in ref constraint, then it shouldn't be in the mutated constraint
        else:
            C.append(Not(Or(
                [self.vars[f'{self.id}_name'][i] == allblocks for i in range(n)])))
        return And(C)

    def properties_for_distinct_names(self):
        # C = [
        #     # but allow multiple blocks to be 'noblock'
        #     Distinct([self.vars[f"{self.id}_name"][i] for i in range(len(self.vars[f"{self.id}_name"])) if
        #               self.vars[f"{self.id}_name"][i] != noblock]),
        #     # Distinct(self.vars[f"{self.id}_name"])
        # ]
        # at most 1 'all' block, at most 1 'fd' block, at most 1 'bk' block, at most 1 'lt' block, at most 1 'rt' block
        n = len(self.vars[f"{self.id}_name"])
        n_fd = Sum([If(self.vars[f"{self.id}_name"][i] == fd, 1, 0) for i in range(n)])
        n_bk = Sum([If(self.vars[f"{self.id}_name"][i] == bk, 1, 0) for i in range(n)])
        n_lt = Sum([If(self.vars[f"{self.id}_name"][i] == lt, 1, 0) for i in range(n)])
        n_rt = Sum([If(self.vars[f"{self.id}_name"][i] == rt, 1, 0) for i in range(n)])
        n_all = Sum([If(self.vars[f"{self.id}_name"][i] == allblocks, 1, 0) for i in range(n)])
        n_setpc = Sum([If(self.vars[f"{self.id}_name"][i] == setpc, 1, 0) for i in range(n)])
        n_repeat = Sum([If(self.vars[f"{self.id}_name"][i] == repeat, 1, 0) for i in range(n)])

        return And(
            n_fd <= 1,
            n_bk <= 1,
            n_lt <= 1,
            n_rt <= 1,
            n_all <= 2,
            n_setpc <= 0,
            n_repeat <= 0
        )

    def properties_for_cnt_range(self):
        C = []
        n = len(self.vars[f'{self.id}_name'])

        for i in range(n):
            C.extend([
                # range for cnt
                And(self.vars[f"{self.id}_cnt"][i] <= CNT_MAX, self.vars[f"{self.id}_cnt"][i] >= 0),
                # range for 'all'
                Implies(self.vars[f"{self.id}_name"][i] == allblocks,
                        And(self.vars[f"{self.id}_cnt"][i] <= CNT_MAX, self.vars[f"{self.id}_cnt"][i] >= 2)),
                # cnt range for 'fd', 'bk', 'lt', 'rt'
                Implies(Or(self.vars[f"{self.id}_name"][i] == fd,
                           self.vars[f"{self.id}_name"][i] == bk,
                           self.vars[f"{self.id}_name"][i] == lt,
                           self.vars[f"{self.id}_name"][i] == rt),
                        self.vars[f"{self.id}_cnt"][i] <= 4, self.vars[f"{self.id}_cnt"][i] >= 0),
                # range for 'noblock'
                Implies(self.vars[f"{self.id}_name"][i] == noblock,
                        self.vars[f"{self.id}_cnt"][i] == 0)
            ])
            if 'most' in self.id:
                # don't allow "at most 0 commands"
                C.append(Implies(self.vars[f"{self.id}_name"][i] != noblock,
                                 self.vars[f"{self.id}_cnt"][i] > 0))
        return And(C)

    def mutate(self):
        self.mutated = True
        i = len(self.vars[f'{self.id}_name'])
        self.vars[f"{self.id}_name"].append(Const(f"{self.id}_name__{i}", Block))
        self.vars[f"{self.id}_cnt"].append(Int(f"{self.id}_cnt__{i}"))

    def to_json(self, model_values):
        js = {}
        for i in range(len(self.vars[f'{self.id}_name'])):
            if model_values[f"{self.id}_name"][i] == noblock:
                pass
            elif model_values[f"{self.id}_name"][i] == allblocks:
                js["all"] = model_values[f"{self.id}_cnt"][i].as_long()
            else:
                js[str(model_values[f"{self.id}_name"][i])] = model_values[f"{self.id}_cnt"][i].as_long()
        return js
