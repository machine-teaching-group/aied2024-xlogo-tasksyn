from z3 import And, Or, Not
from src.xlogomini.smt.goal import REGISTRY as OBJ_REGISTRY
from src.xlogomini.utils.formulas import cnf_formula, wall_vars_along_the_path
from src.xlogomini.utils.boolean_logic import not_cnf
from src.xlogomini.components.goal.objective import Objective
from src.xlogomini.components.goal.spec import Spec


class GoalSMT():
    def __init__(self, rows, cols, vars, goal, visited, edge_colors=None):
        self.goal = goal
        self.visited = visited
        self.edge_colors = edge_colors

        self.rows = rows
        self.cols = cols
        self.ntiles = rows * cols

        self.vars = vars
        self.tar_smt, self.forb_smts = self._build_smts()

    def _build_smts(self):
        tar_smt = None
        forb_smts = []

        objs = self.goal.objs
        for obj_name in objs.keys():
            for obj in objs[obj_name]:
                kwargs = {
                    "rows"     : self.rows,
                    "cols"     : self.cols,
                    "vars"     : self.vars,
                    "objective": obj,
                    "visited"  : self.visited
                }
                if obj_name == 'findonly':
                    tar_smt = OBJ_REGISTRY['find'](**kwargs)
                    kwargs.update({"objective": Objective(obj_name='forbid', specs=[Spec(not_cnf(tar_smt.cnfs[0]))])})
                    forb_smts = [OBJ_REGISTRY['forbid'](**kwargs)]
                elif obj_name == 'forbid':
                    forb_smts.append(OBJ_REGISTRY[obj_name](**kwargs))
                elif obj_name == 'draw':
                    kwargs.update({"edge_colors": self.edge_colors})
                    tar_smt = OBJ_REGISTRY[obj_name](**kwargs)
                else:
                    tar_smt = OBJ_REGISTRY[obj_name](**kwargs)

        return tar_smt, forb_smts

    def properties_for_emulator(self):
        C = []
        if self.tar_smt is not None:
            C.append(self.tar_smt.properties_for_emulator())
        for forb_smt in self.forb_smts:
            C.append(forb_smt.properties_for_emulator())
        return And(C)

    def properties(self):
        C = []
        if self.tar_smt is not None:
            C.append(self.tar_smt.properties())
        for forb_smt in self.forb_smts:
            C.append(forb_smt.properties())
        return And(C)

    # def properties_for_good_placement(self):
    #     """
    #     Given the trace, infer the items' positions
    #     """
    #     C = []
    #     graph = build_empty_world_graph(self.rows, self.cols)
    #
    #     cnfs = self.tar_smt.cnfs
    #
    #     for i in range(len(self.visited)):
    #         for j in range(i + 1, len(self.visited)):
    #             sub_visited = self.visited[i: j + 1]
    #             C_path = []
    #             shortest_paths = list(nx.all_shortest_paths(graph, source=sub_visited[0], target=sub_visited[-1]))
    #             for path in shortest_paths:
    #                 # current sub_visited is already one of the shortest paths, the turtle may select it without any reasons
    #                 if len(path) == len(sub_visited):
    #                     break
    #                 # build the graph for visited grids
    #                 g_extra_visited = build_visit_graph(sub_visited)
    #                 # remove the nodes contained in the shortest path from the visited trace
    #                 g_extra_visited.remove_nodes_from(path)
    #                 # target items at extra visited grids
    #                 tar_items_at_extra_visited = Or(
    #                     [cnf_formula(self.vars, cnf, list(g_extra_visited), 'or') for cnf in cnfs])
    #                 # constraints for path forbidden
    #                 path_forbidden = self.properties_for_impossible_trace(path)
    #                 # grid visited either because there are target items or the other shortest paths are forbidden
    #                 C_path.append(exactly_one([tar_items_at_extra_visited, path_forbidden]))
    #             # There all non-selected shortest paths
    #             C.append(And(C_path))
    #     return And(C)

    def properties_for_impossible_trace(self, trace):
        """
        Get the constraints that makes the `trace` impossible
        either because of the forbidden areas, walls or forbidden items.
        """
        # allowed
        GRIDS_NOT_ALLOWED = Not(And(list(map(self.vars['allowed'].__getitem__, trace))))

        # forbidden items
        if len(self.forb_smts) > 0:
            ITEMS_FORBIDDEN = Or([cnf_formula(self.vars, smt.cnfs[0], trace, 'or') for smt in self.forb_smts])
        else:
            ITEMS_FORBIDDEN = False

        # walls
        WALLS_IN_THE_PATH = Or(wall_vars_along_the_path(self.vars, self.rows, self.cols, trace))

        return Or(WALLS_IN_THE_PATH, GRIDS_NOT_ALLOWED, ITEMS_FORBIDDEN)

    def feasible_path(self, path):
        """
        Return the formula showing if the given `path` is feasible.
        """
        TAR_FEASIBLE = self.tar_smt.feasible_path(path)
        FORB_FEASIBLE = And([forb_smt.feasible_path(path) for forb_smt in self.forb_smts])
        return And(TAR_FEASIBLE, FORB_FEASIBLE)
