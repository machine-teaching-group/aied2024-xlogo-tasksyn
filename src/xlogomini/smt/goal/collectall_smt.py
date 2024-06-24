from src.xlogomini.smt.goal.base_objective_smt import ObjectiveSMT
from z3 import And, Sum, If, Not
from src.xlogomini.utils.formulas import cnf_formula


class CollectAllSMT(ObjectiveSMT):
    def __init__(self, rows, cols, vars, objective, visited):
        ObjectiveSMT.__init__(self, rows, cols, vars, objective, visited)

    def properties_for_emulator(self):
        cnf = self.cnfs[0]
        not_visited = set(range(self.ntiles)) - set(self.visited)

        # build constraints
        found_visited = cnf_formula(self.vars, cnf, self.visited, 'or')
        not_found_not_visited = Not(cnf_formula(self.vars, cnf, not_visited, 'or'))

        return And([
            found_visited,
            not_found_not_visited
        ])

    def properties(self):
        cnf = self.cnfs[0]
        not_visited = set(range(self.ntiles)) - set(self.visited)

        # build constraints
        found_visited = cnf_formula(self.vars, cnf, self.visited, 'or')
        not_found_not_visited = Not(cnf_formula(self.vars, cnf, not_visited, 'or'))
        at_least_2_target_items = cnf_formula(self.vars, cnf, self.visited, 'at_least', 2)
        item_last_visited = cnf_formula(self.vars, cnf, self.visited[-1], 'and')

        C = [
            found_visited,
            not_found_not_visited,
            at_least_2_target_items,
            item_last_visited,
        ]
        return And(C)

    def feasible_path(self, path):
        # number of target items in the world (e.g., for "Collect all blue shapes")
        N_TAR_ITEMS = Sum([If(cnf_formula(self.vars, self.cnfs[0], i, 'or'), 1, 0)
                           for i in range(self.ntiles)])
        FEASIBLE = Sum([If(cnf_formula(self.vars, self.cnfs[0], i, 'or'), 1, 0)
                         for i in set(path)]) == N_TAR_ITEMS
        return FEASIBLE