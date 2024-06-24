from src.xlogomini.smt.goal.base_objective_smt import ObjectiveSMT
from z3 import And, Sum, If
from src.xlogomini.utils.formulas import cnf_formula


class FindSMT(ObjectiveSMT):
    def __init__(self, rows, cols, vars, objective, visited):
        ObjectiveSMT.__init__(self, rows, cols, vars, objective, visited)

    def properties_for_emulator(self):
        tar_item_in_visited = cnf_formula(self.vars, self.cnfs[0], self.visited, 'or')
        return And(tar_item_in_visited)

    def properties(self):
        # constraints for target items
        tar_item_exactly_one = cnf_formula(self.vars, self.cnfs[0], list(range(self.ntiles)), 'exactly_one')
        tar_items_in_last_visited = cnf_formula(self.vars, self.cnfs[0], self.visited[-1], 'and')

        C = [
            tar_item_exactly_one,
            tar_items_in_last_visited,
        ]
        return And(C)

    def feasible_path(self, path):
        FEASIBLE = Sum([If(cnf_formula(self.vars, self.cnfs[0], i, 'or'), 1, 0)
                        for i in set(path)]) >= 1
        return FEASIBLE
