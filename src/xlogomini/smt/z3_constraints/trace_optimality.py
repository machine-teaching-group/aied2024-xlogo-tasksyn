from z3 import And, Or, Not, simplify, Implies
from src.xlogomini.components.code.xlogo_code import Code
from src.xlogomini.utils.code_optimality import n_actions_for_path
from src.xlogomini.utils.formulas import wall_vars_along_the_path, is_standalone_wall
from src.xlogomini.utils.helpers import get_neighboring_ids


def redundant_sub_edges(edges, sub_edges):
    edges_info = info_of_edges(edges)

    # skit the first edge (k=0), because it will never be redundant due to the initial position
    k = 1
    n = len(sub_edges)

    while k <= len(edges) - n:
        if edges[k:k + n] == sub_edges:
            edges_without_sub_edges = edges[:k] + edges[k + n:]
            # if the new edges are legal (edges still continous) and the info doesn't change by removing a sub_edges from the edges
            # then the sub edges must be redundant
            if legal_edges(edges_without_sub_edges) and (
                    len(edges_info - info_of_edges(edges_without_sub_edges)) == 0):
                return True
        k += 1
    return False


def legal_edges(edges):
    """
    Return True if the given edges are legal
    """
    for i in range(len(edges) - 1):
        if edges[i][1] != edges[i + 1][0]:
            return False
    return True


def info_of_edges(edges):
    """
    The information contained in the edges. The `info` is represented by a set.
    """
    return set(map(lambda t: (t[0], t[1], t[2]) if t[0] < t[1] else (t[1], t[0], t[2]), edges))


def redundant_setpc_in_code(code, pworld):
    """
    Check if there exist colors used in code but not shown in the drawn markers.
    If exists, then the code has redundant colors.
    """
    colors_in_code = code.get_pen_colors(set(), code.astJson['run'])
    colors_in_markers = pworld.drawn_markers.get_colors()
    has_redundant_colors = len(colors_in_code - colors_in_markers) > 0
    return has_redundant_colors


def redundant_grids_in_trace(trace, edge_colors=None):
    edges = trace2edges(trace, edge_colors=edge_colors)

    for i in range(len(edges) - 1, -1, -1):
        for j in range(i + 1, len(edges) + 1):
            if redundant_sub_edges(edges, sub_edges=edges[i:j]):
                return True
    return False


def trace2edges(trace, edge_colors=None):
    """
    Convert the `trace`, which is a list of visited grids, to the `edges`.
    Example:
        trace = [1, 0, 1, 2, 3, 4]
        edges = [(1, 0, None), (0, 1, None), (1, 2, None), (2, 3, None), (3, 4, None)]
    """
    if edge_colors is not None:
        assert len(trace) == len(edge_colors) + 1

    edges = []
    for i in range(len(trace) - 1):
        edge = (trace[i], trace[i + 1], edge_colors[i] if edge_colors is not None else None)
        edges.append(edge)
    return edges


def properties_for_optimal_trace(vars, rows, cols, visited, init_dir, feasible_path_func, trace_max_actions=8,
                                 code_constraints=None):
    """
    Constraints that can make the trace optimal for solving the task.
    Without this, you may generate tasks that have better code (i.e., shorter code) than the given one.
    """
    if redundant_grids_in_trace(visited):
        return False

    C = []
    shorter_paths_walls = []
    n_actions_visited, _, _ = n_actions_for_path(rows, cols, visited, init_dir=init_dir)

    # shorter_paths = []

    def generate_shorter_paths(start, max_actions, prev_path, cur_dir, code_constraints):
        """
        This recursive function is used to generate all possible paths from the
        starting position of the turtle to any other target positions.

        `start` : The starting position of the turtle as a node in the graph.
        `max_actions` : The maximum distance the turtle can travel from the starting position to the target positions.
        `prev_path` : The previous path taken by the turtle to reach the current position.
        """
        if max_actions <= 0:
            return

        neighbors = get_neighboring_ids(start, rows, cols)
        next_nodes = [v for k, v in neighbors.items() if v != None]

        for end in next_nodes:
            # each grid can be visited at most 3 times
            if prev_path.count(end) >= 3:
                continue

            # check required actions for this path
            req_actions, end_dir, _ = n_actions_for_path(rows, cols, [prev_path[-1], end], init_dir=cur_dir)
            # no enough actions
            if req_actions > max_actions:
                continue

            merged_path = prev_path + [end]
            # save the path
            if visited != merged_path:
                _, _, code_js = n_actions_for_path(rows, cols, merged_path, init_dir=init_dir)
                cons_satisfied = Code(code_js).check_constraints(code_constraints)
                if (not redundant_grids_in_trace(merged_path)) and cons_satisfied:
                    path_walls = wall_vars_along_the_path(vars, rows, cols, merged_path)
                    if merged_path[-1] == visited[-1]:  # same destination
                        shorter_paths_walls.extend(path_walls)
                    # shorter_paths.append(merged_path)
                    # for a shorter path, don't allow the path to solve the task by
                    # 1) path cannot solve the task (forbidden items included)
                    # 2) walls in the path
                    PATH_IS_FEASIBLE = feasible_path_func(merged_path)
                    SL_WALLS_IN_PATH = Or([is_standalone_wall(vars, rows, cols, str(wall)) for wall in path_walls])
                    C.append(And([
                        # Implies(Not(PATH_IS_FEASIBLE), Not(SL_WALLS_IN_PATH)),
                        Implies(PATH_IS_FEASIBLE, SL_WALLS_IN_PATH)]
                    ))

            generate_shorter_paths(end,
                                   max_actions=max_actions - req_actions,
                                   prev_path=merged_path,
                                   cur_dir=end_dir,
                                   code_constraints=code_constraints)

    generate_shorter_paths(start=visited[0],
                           max_actions=min(n_actions_visited - 1, trace_max_actions),
                           prev_path=[visited[0]],
                           cur_dir=init_dir,
                           code_constraints=code_constraints)

    # don't allow non-shortest paths to have standalone walls
    all_walls = vars['leftW'] + vars['rightW'] + vars['topW'] + vars['bottomW']
    allowed_walls = shorter_paths_walls + wall_vars_along_the_path(vars, rows, cols, visited)
    disallowed_walls = [x for x in all_walls if x not in allowed_walls]

    NO_SA_WALLS_IN_NON_SHORTEST_PATHS = And(
        [Not(is_standalone_wall(vars, rows, cols, str(wall))) for wall in disallowed_walls])
    C.append(NO_SA_WALLS_IN_NON_SHORTEST_PATHS)

    return And(C)


if __name__ == '__main__':
    # trace = Trace([1, 0, 1, 0, 1, 2, 3, 4, 3])
    # trace = Trace([1, 0, 1, 2, 1, 2, 3, 4, 3])
    trace = [1, 0, 1, 2, 3, 4, 3]
    print(redundant_grids_in_trace(trace))

    _, _, code = n_actions_for_path(3, 3, [7, 4, 1, 2], 0)
    Code(code).check_constraints({"exactly" : {"fd": 1},
                                  "at_most" : {},
                                  "start_by": []})
