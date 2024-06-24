from src.xlogomini.smt.goal.base_objective_smt import ObjectiveSMT
from z3 import And, Sum, If
from src.xlogomini.utils.formulas import cnf_formula


class SumSMT(ObjectiveSMT):
    def __init__(self, rows, cols, vars, objective, visited):
        ObjectiveSMT.__init__(self, rows, cols, vars, objective, visited)
        self.total_cnt = objective.total_cnt
        assert self.total_cnt is not None

    def properties_for_emulator(self):
        return Sum([self.vars['count'][i] * If(cnf_formula(self.vars, self.cnfs[0], i, 'or'), 1, 0)
                    for i in set(self.visited)]) == self.total_cnt

    def properties(self):
        pre_visited_set = set(self.visited) - set(self.visited[-1:])

        # build constraints for target items
        pre_visited_cnt = Sum(
            [self.vars['count'][i] * If(cnf_formula(self.vars, self.cnfs[0], i, 'or'), 1, 0) for i in pre_visited_set])
        last_visited_cnt = self.vars['count'][self.visited[-1]] * If(
            cnf_formula(self.vars, self.cnfs[0], self.visited[-1]),
            1, 0)
        pre_visited_cnt_less_than_total_cnt = pre_visited_cnt < self.total_cnt
        pre_plus_last_visited_equals_total_cnt = (pre_visited_cnt + last_visited_cnt) == self.total_cnt

        # only strawberry allowed to be distractors
        only_straw_allowed = cnf_formula(self.vars, [['noname', 'strawberry']], list(range(self.ntiles)), 'and')

        # put more target items
        more_than_collected = Sum(
            [self.vars['count'][i] * If(cnf_formula(self.vars, self.cnfs[0], i, 'or'), 1, 0) for i in
             range(self.ntiles)]) > self.total_cnt

        # constrains
        C = [
            pre_visited_cnt_less_than_total_cnt,
            pre_plus_last_visited_equals_total_cnt,
            only_straw_allowed,
            more_than_collected
        ]
        return And(C)

    def feasible_path(self, path):
        FEASIBLE = Sum([self.vars['count'][i] * If(cnf_formula(self.vars, self.cnfs[0], i, 'or'), 1, 0)
                        for i in set(path)]) == self.total_cnt
        return FEASIBLE
