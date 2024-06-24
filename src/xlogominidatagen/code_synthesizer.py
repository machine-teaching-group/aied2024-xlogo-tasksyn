from src.xlogomini.smt.code.code_smt import CodeSMT
from src.xlogomini.utils.model_conversions import model2values
import json
import argparse
from src.xlogomini.smt.constraints.code_constraints_smt import CodeConstraintsSMT
from z3 import And, Solver, sat, Not, Implies, Or, Sum
from src.xlogomini.utils.formulas import exactly_the_same
from src.xlogomini.smt.code.base_block_smt import *


class CodeSyn():
    def __init__(self, code_js, cons_js):
        self.code_js = code_js
        self.cons_js = cons_js

        self.mutated = True

        self.code_smt = CodeSMT(code_js)
        self.cons_smt = CodeConstraintsSMT(cons_js)

        self.vars = self._build_vars()

    def _build_vars(self):
        vars = {}
        vars.update(self.code_smt.vars)
        vars.update(self.cons_smt.vars)
        return vars

    def properties(self,
                   rows, cols,
                   max_code_inc, max_code_dec,
                   exact_code_inc,
                   max_rep_body_inc, max_rep_body_dec,
                   max_rep_times_inc, max_rep_times_dec,
                   max_cons_dec, max_cons_inc):
        C = [
            self.code_smt.properties(rows, cols,
                                     max_code_inc, max_code_dec,
                                     exact_code_inc,
                                     max_rep_body_inc, max_rep_body_dec,
                                     max_rep_times_inc, max_rep_times_dec),
            self.cons_smt.properties(max_dec=max_cons_dec, max_inc=max_cons_inc),
            self.properties_for_exactly_on_code(),
            self.properties_for_most_on_code(),
            self.properties_for_startby_on_code()
        ]
        return And(C)

    def properties_for_exactly_on_code(self):
        C = []
        vars = self.cons_smt.body['exactly'].vars
        # constraints for exactly
        for i in range(len(vars['exactly_name'])):
            C.append(Implies(And(vars['exactly_name'][i] != noblock, vars['exactly_name'][i] != allblocks),
                             self.code_smt.target_block_cnt(vars['exactly_name'][i], mutated=True) ==
                             vars['exactly_cnt'][i]))
            C.append(Implies(vars['exactly_name'][i] == allblocks,
                             self.code_smt.total_block_cnt(mutated=True) == vars['exactly_cnt'][i]))
        return And(C)

    def properties_for_most_on_code(self):
        C = []
        vars = self.cons_smt.body['at_most'].vars
        for i in range(len(vars['most_name'])):
            # should be `==` instead of <=, because `most` is usually the minimal number of blocks to be used.
            C.append(Implies(And(vars['most_name'][i] != noblock, vars['most_name'][i] != allblocks),
                             self.code_smt.target_block_cnt(vars['most_name'][i], mutated=True) == vars['most_cnt'][i]))
            C.append(Implies(vars['most_name'][i] == allblocks,
                             self.code_smt.total_block_cnt(mutated=True) == vars['most_cnt'][i]))
        return And(C)

    def properties_for_startby_on_code(self):
        C = []

        start = self.cons_smt.body['start_by'].vars['start_name']
        body = self.code_smt.body

        # 1. size of the start_by constrain should be less than the size of the outer code
        size_start = Sum([var != noblock for var in start])
        size_outer_code = Sum([body[k].vars[f"block__{body[k].id}"] != noblock for k in range(len(body))])
        C.append(size_start < size_outer_code)

        # 2. pattern matching
        for i in range(len(start)):
            or_list = []
            # n non-empty block before index i for start constraint
            n_block_before_i_start = Sum([start[k] != noblock for k in range(len(start[:i]))])
            for j in range(len(self.code_smt.body)):
                # n non-empty block before index j for code
                n_block_before_j_body = Sum(
                    [body[k].vars[f'block__{body[k].id}'] != noblock for k in range(len(body[:j]))])

                # same number of non-empty blocks before respective index and their current blocks are the same
                or_list.append(
                    And(n_block_before_j_body == n_block_before_i_start,
                        body[j].vars[f'block__{body[j].id}'] == start[i]))

            C.append(Implies(start[i] != noblock, Or(or_list)))
        return And(C)

    def mutate(self,
               n_blks_insert_hetero,
               n_blks_insert_homog,
               prob_insert_rep=0):
        self.mutated = True
        # count existing `repeat`s
        n_repeat = self.code_smt.target_block_cnt(repeat, mutated=False)

        # if there are already repeats, don't mutate to `repeat`,
        # otherwise mutate to `repeat` with prob `prob_insert_rep`
        if n_repeat > 0:
            self.code_smt.mutate(n_blks_insert_hetero=n_blks_insert_hetero,
                                 n_blks_insert_homog=n_blks_insert_homog,
                                 prob_insert_rep=0)
        else:
            self.code_smt.mutate(n_blks_insert_hetero=n_blks_insert_hetero,
                                 n_blks_insert_homog=n_blks_insert_homog,
                                 prob_insert_rep=prob_insert_rep)

        self.cons_smt.mutate()
        self.vars = self._build_vars()

    def to_json(self, model_values):
        return {
            "code_json"  : self.code_smt.to_json(model_values, with_run=True),
            "constraints": self.cons_smt.to_json(model_values)
        }

    def generate(self, n_max=10, save_dir=None, save=False,
                 rows=3, cols=3,
                 n_blks_insert_homog=1, n_blks_insert_hetero=2,
                 prob_insert_rep=0,
                 max_code_inc=4, max_code_dec=1,
                 exact_code_inc=None,
                 max_rep_body_inc=2, max_rep_body_dec=2,
                 max_rep_times_inc=2, max_rep_times_dec=2,
                 max_cons_dec=0, max_cons_inc=1):

        mutations = []

        self.mutate(n_blks_insert_homog=n_blks_insert_homog,
                    n_blks_insert_hetero=n_blks_insert_hetero,
                    prob_insert_rep=prob_insert_rep)

        model_values = {}

        s = Solver()
        s.add(self.properties(rows=rows, cols=cols,
                              max_code_inc=max_code_inc, max_code_dec=max_code_dec,
                              exact_code_inc=exact_code_inc,
                              max_rep_body_inc=max_rep_body_inc, max_rep_body_dec=max_rep_body_dec,
                              max_rep_times_inc=max_rep_times_inc, max_rep_times_dec=max_rep_times_dec,
                              max_cons_dec=max_cons_dec, max_cons_inc=max_cons_inc))

        n = 0
        while s.check() == sat and n < n_max:
            n += 1
            model_values = model2values(self.vars, s.model())

            instance = self.to_json(model_values)
            mutations.append(instance)
            # print(instance)
            # print(Code(instance['code_json']))
            # print((CodeConstraints(instance['constraints'])))
            # print('===========================')

            s.add(Not(exactly_the_same(self.vars, model_values)))

        # remove the duplicated codes (only consider the code equivalence, don't consider cons)
        string_list = [json.dumps(item, sort_keys=True) for item in mutations]
        unique_set = set(string_list)
        unique_mutations = [json.loads(item) for item in unique_set]

        return unique_mutations