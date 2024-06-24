from src.xlogomini.smt.goal.base_objective_smt import ObjectiveSMT
from z3 import Not, And, Or
from src.xlogomini.utils.helpers import get_neighboring_ids
from src.xlogomini.utils.helpers import i2y, i2x


class DrawSMT(ObjectiveSMT):
    def __init__(self, rows, cols, vars, objective, visited, edge_colors):
        ObjectiveSMT.__init__(self, rows, cols, vars, objective, visited)
        self.edge_colors = edge_colors

    def properties_for_emulator(self):
        C = []
        non_visited = set(range(self.ntiles)) - set(self.visited)

        # markers on visited grids
        for i in range(len(self.visited) - 1):
            neighbors = get_neighboring_ids(self.visited[i], self.rows, self.cols)
            if self.visited[i + 1] == neighbors['top']:
                C.extend([
                    self.vars['topM'][self.visited[i]],
                    self.vars['bottomM'][self.visited[i + 1]],
                ])
            elif self.visited[i + 1] == neighbors['bottom']:
                C.extend([
                    self.vars['bottomM'][self.visited[i]],
                    self.vars['topM'][self.visited[i + 1]],
                ])
            elif self.visited[i + 1] == neighbors['left']:
                C.extend([
                    self.vars['leftM'][self.visited[i]],
                    self.vars['rightM'][self.visited[i + 1]],
                ])
            elif self.visited[i + 1] == neighbors['right']:
                C.extend([
                    self.vars['rightM'][self.visited[i]],
                    self.vars['leftM'][self.visited[i + 1]],
                ])
            else:
                raise ValueError(f"No neighbors found for idx {i}")

        # non-exist on non-visited grids
        C.extend([Not(self.vars['exist'][nv]) for nv in non_visited])
        return And(C)

    def properties(self):
        C = []
        non_visited = set(range(self.ntiles)) - set(self.visited)

        has_y_eq_0 = any([i2y(v, self.cols) == 0 for v in self.visited])
        has_x_eq_0 = any([i2x(v, self.cols) == 0 for v in self.visited])

        C.append(And(has_x_eq_0, has_y_eq_0))

        # markers on visited grids
        for i in range(len(self.visited) - 1):
            neighbors = get_neighboring_ids(self.visited[i], self.rows, self.cols)
            if self.visited[i + 1] == neighbors['top']:
                C.extend([
                    self.vars['topM'][self.visited[i]],
                    self.vars['bottomM'][self.visited[i + 1]],
                ])
            elif self.visited[i + 1] == neighbors['bottom']:
                C.extend([
                    self.vars['bottomM'][self.visited[i]],
                    self.vars['topM'][self.visited[i + 1]],
                ])
            elif self.visited[i + 1] == neighbors['left']:
                C.extend([
                    self.vars['leftM'][self.visited[i]],
                    self.vars['rightM'][self.visited[i + 1]],
                ])
            elif self.visited[i + 1] == neighbors['right']:
                C.extend([
                    self.vars['rightM'][self.visited[i]],
                    self.vars['leftM'][self.visited[i + 1]],
                ])
            else:
                raise ValueError(f"No neighbors found for idx {i}")

        # non-exist on non-visited grids
        C.extend([Not(self.vars['exist'][nv]) for nv in non_visited])
        return And(C)
