from src.xlogomini.smt.goal.base_objective_smt import ObjectiveSMT
import networkx as nx
from z3 import Not, And, Or, Sum, If
from src.xlogomini.utils.graph import build_empty_world_graph
from src.xlogomini.utils.formulas import cnf_formula


class ForbidSMT(ObjectiveSMT):
    def __init__(self, rows, cols, vars, objective, visited):
        ObjectiveSMT.__init__(self, rows, cols, vars, objective, visited)

    def properties_for_emulator(self):
        forb_items_not_in_visited = Not(cnf_formula(self.vars, self.cnfs[0], self.visited, 'or'))
        return And(forb_items_not_in_visited)

    def properties(self):
        C = []
        non_visited = set(range(self.ntiles)) - set(self.visited)

        forb_items_not_in_visited = Not(cnf_formula(self.vars, self.cnfs[0], self.visited, 'or'))
        forb_items_in_non_visited = cnf_formula(self.vars, self.cnfs[0], non_visited, 'or')

        # put forbidden items only at similar position as standalone walls
        # those positions are not covered by shortest path
        graph = build_empty_world_graph(self.rows, self.cols)
        possible_forb_items_pos = set()
        for i in range(len(self.visited)):
            for j in range(i + 1, len(self.visited)):
                sub_visited = self.visited[i: j + 1]
                shortest_paths = list(nx.all_shortest_paths(graph,
                                                            source=sub_visited[0],
                                                            target=sub_visited[-1]))
                for path in shortest_paths:
                    possible_forb_items_pos.update(set(path))

        possible_forb_items_pos -= set(self.visited)  # forbidden items cannot be on the trace

        # When the code is "fd, fd", there would be no possible positions for forbidden items,
        # then we don't add such a constraints. However, when there are possible positions, we require the
        # forbidden items only appear in these positions.
        if len(possible_forb_items_pos) > 0:
            impossible_forb_items_pos = set(range(self.ntiles)) - possible_forb_items_pos
            forb_items_not_in_non_shortest_paths = Not(cnf_formula(self.vars,
                                                                   self.cnfs[0],
                                                                   impossible_forb_items_pos,
                                                                   'or'))
            C.append(forb_items_not_in_non_shortest_paths)

        C = [
            forb_items_not_in_visited,
            forb_items_in_non_visited,
        ]
        return And(C)

    def feasible_path(self, path):
        FORBID_FEASIBLE = Not(cnf_formula(self.vars, self.cnfs[0], path, 'or'))
        return FORBID_FEASIBLE
