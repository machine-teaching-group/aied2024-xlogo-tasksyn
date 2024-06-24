from z3 import *
from tqdm import tqdm
from itertools import islice
import numpy as np
from src.xlogomini.utils.graph import build_empty_world_graph
from src.xlogomini.utils.formulas import wall_vars_along_the_path, exactly_one
import networkx as nx
import os


def properties_for_reachability(vars, rows, cols, k_shortest_paths=100):
    # load the constraints from file
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             f'./reachability_{rows}x{cols}_{k_shortest_paths}.smt2')
    if os.path.exists(file_path):
        # Load the constraints from the file
        with open(file_path, 'r') as f:
            z3_cons = parse_smt2_string(f.read())
            return And(z3_cons)

    def k_shortest_simple_paths(G, source, target, k, weight=None):
        return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))

    # if constraints not pre-calculated, then calculate
    ntiles = rows * cols
    M = np.empty([ntiles, ntiles], dtype=object)  # connectivity matrix
    G = build_empty_world_graph(rows, cols)

    for i in tqdm(range(ntiles)):
        M[i, i] = True
        for j in range(i + 1, ntiles):
            paths = k_shortest_simple_paths(G, i, j, k=k_shortest_paths)
            all_paths_blocked_by_walls = And([Or(wall_vars_along_the_path(vars, rows, cols, path))
                                              for path in paths])
            M[i, j] = Not(all_paths_blocked_by_walls)
            M[j, i] = M[i, j]

    C = []
    for i in range(ntiles):
        for j in range(i, ntiles):
            C.extend([
                # allowed + allowed => M[i,j]
                Implies(And(vars['allowed'][i], vars['allowed'][j]),
                        M[i, j]),

                # allowed + not allowed => not M[i,j]
                Implies(exactly_one([vars['allowed'][i],
                                     vars['allowed'][j]]),
                        Not(M[i, j])),

                # (skip) not allowed + not allowed => M[i,j] or not M[i,j]

                # M[i,j] => (allowed + allowed) or (not allowed + not allowed)
                Implies(M[i, j], Or(
                    And(vars['allowed'][i], vars['allowed'][j]),
                    And(Not(vars['allowed'][i]), Not(vars['allowed'][j]))
                )),

                # not M[i,j] => (allowed + not allowed) or (not allowed + not allowed)
                Implies(Not(M[i, j]), Or(
                    And(vars['allowed'][i], Not(vars['allowed'][j])),
                    And(vars['allowed'][j], Not(vars['allowed'][i])),
                    And(Not(vars['allowed'][i]), Not(vars['allowed'][j]))
                )),

                # allowed_i + M[i,j] => allowed_j
                Implies(And(vars['allowed'][i], M[i, j]),
                        vars['allowed'][j]),
                Implies(And(vars['allowed'][j], M[i, j]),
                        vars['allowed'][i]),

                # allowed_i + not M[i,j] => not allowed_j
                Implies(And(vars['allowed'][i], Not(M[i, j])),
                        Not(vars['allowed'][j])),
                Implies(And(vars['allowed'][j], Not(M[i, j])),
                        Not(vars['allowed'][i])),

                # not allowed_i + M[i,j] => not allowed_j
                Implies(And(Not(vars['allowed'][i]), M[i, j]),
                        Not(vars['allowed'][j])),
                Implies(And(Not(vars['allowed'][j]), M[i, j]),
                        Not(vars['allowed'][i])),

                # (skip) not allowed_i + not M[i,j] => any of allowed_j
            ])

    C = simplify(And(C))
    s = Solver()
    s.add(C)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           f'./reachability_{rows}x{cols}_{k_shortest_paths}.smt2'), 'w') as f:
        f.write(s.to_smt2())
    return C


if __name__ == "__main__":
    # world_json = load_world_json('83')
    from xlogomini.xlogo_smt.world.world_smt import WorldSMT
    import time

    start_time = time.time()
    world_smt = WorldSMT(rows=5, cols=4)
    s = Solver()
    s.add(properties_for_reachability(world_smt.vars, world_smt.rows, world_smt.cols))
    print(time.time() - start_time)
    print(s.check())
