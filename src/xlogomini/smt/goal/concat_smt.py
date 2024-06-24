from src.xlogomini.smt.goal.base_objective_smt import ObjectiveSMT
from z3 import Not, And, Implies, Sum, If
from src.xlogomini.utils.formulas import cnf_formula


class ConcatSMT(ObjectiveSMT):
    def __init__(self, rows, cols, vars, objective, visited):
        ObjectiveSMT.__init__(self, rows, cols, vars, objective, visited)

    def properties_for_emulator(self):
        return self.feasible_path(self.visited)

    def properties(self):
        # final item at last visited
        ITEM_LAST_VISITED = cnf_formula(self.vars, self.cnfs[-1], self.visited[-1], 'and')

        # only one target item
        ONLY_ONE_TAR_ITEM = And([cnf_formula(self.vars, cnf, list(range(self.ntiles)), 'exactly_one')
                                 for cnf in self.cnfs])

        C = [
            ITEM_LAST_VISITED,
            ONLY_ONE_TAR_ITEM,
            self.feasible_path(self.visited),
        ]
        return And(C)

    def feasible_path(self, path):
        C = []

        for k in range(len(self.cnfs)):
            C.append(cnf_formula(self.vars, self.cnfs[k], path, 'exactly_one'))

            for i, v in enumerate(path):
                if len(path[:i]) < 1: continue
                if k >= len(self.cnfs) - 1: break

                pre_visit = path[:i]
                cur_visit = path[i:i + 1]
                post_visit = path[i + 1:]

                C.append(Implies(cnf_formula(self.vars, self.cnfs[k + 1], cur_visit, 'or'),
                                 cnf_formula(self.vars, self.cnfs[k], pre_visit, 'or')))
                C.append(Implies(cnf_formula(self.vars, self.cnfs[k], cur_visit, 'or'),
                                 Not(cnf_formula(self.vars, self.cnfs[k + 1], pre_visit, 'or'))))
        FEASIBLE = And(C)
        return FEASIBLE
