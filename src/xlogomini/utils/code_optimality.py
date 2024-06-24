from src.xlogomini.utils.graph import build_world_graph, build_empty_world_graph
from src.xlogomini.utils.helpers import get_neighboring_ids
import networkx as nx


def min_actions_for_dst(world, src, dst):
    """
    Calculate the minimal basic actions (e.g., fd/bk/lt/rt)
    required to get to `target` starting from `source` in a `world`.
    """
    rows, cols = world.rows, world.cols

    # compare the trace with the shortest paths
    G = build_world_graph(world)  # build the graph for this world
    basic_actions_each_sp = [n_actions_for_path(rows, cols, sp, world.turtle.dir)[0]
                             for sp in nx.all_shortest_paths(G, source=src, target=dst)]
    return min(basic_actions_each_sp)


def n_actions_for_path(rows, cols, path, init_dir):
    # init state for this round
    cur_dir = init_dir
    action_list = []
    for i in range(len(path) - 1):
        i_neighbors = get_neighboring_ids(path[i], rows, cols)

        # for both cases, don't need extra turns or direction changes
        # Case 1. using fd, don't need extra turns
        dir_N_and_next_on_top = (cur_dir == 0) and (path[i + 1] == i_neighbors['top'])
        dir_E_and_next_on_right = (cur_dir == 1) and (path[i + 1] == i_neighbors['right'])
        dir_S_and_next_on_bottom = (cur_dir == 2) and (path[i + 1] == i_neighbors['bottom'])
        dir_W_and_next_on_left = (cur_dir == 3) and (path[i + 1] == i_neighbors['left'])
        if dir_N_and_next_on_top or dir_E_and_next_on_right or dir_S_and_next_on_bottom or dir_W_and_next_on_left:
            action_list.append({"type": "fd"})

        # Case 2. using bk, don't need extra turns
        dir_N_and_next_on_bottom = (cur_dir == 0) and (path[i + 1] == i_neighbors['bottom'])
        dir_E_and_next_on_left = (cur_dir == 1) and (path[i + 1] == i_neighbors['left'])
        dir_S_and_next_on_top = (cur_dir == 2) and (path[i + 1] == i_neighbors['top'])
        dir_W_and_next_on_right = (cur_dir == 3) and (path[i + 1] == i_neighbors['right'])
        if dir_N_and_next_on_bottom or dir_E_and_next_on_left or dir_S_and_next_on_top or dir_W_and_next_on_right:
            action_list.append({"type": "bk"})

        # Case 3. using left, need to turn left first
        dir_N_and_next_on_left = (cur_dir == 0) and (path[i + 1] == i_neighbors['left'])
        dir_E_and_next_on_top = (cur_dir == 1) and (path[i + 1] == i_neighbors['top'])
        dir_S_and_next_on_right = (cur_dir == 2) and (path[i + 1] == i_neighbors['right'])
        dir_W_and_next_on_bottom = (cur_dir == 3) and (path[i + 1] == i_neighbors['bottom'])
        if dir_N_and_next_on_left or dir_E_and_next_on_top or dir_S_and_next_on_right or dir_W_and_next_on_bottom:
            action_list.append({"type": "lt"})
            action_list.append({"type": "fd"})

        # Case 4. using right, need to turn right first
        dir_N_and_next_on_right = (cur_dir == 0) and (path[i + 1] == i_neighbors['right'])
        dir_E_and_next_on_bottom = (cur_dir == 1) and (path[i + 1] == i_neighbors['bottom'])
        dir_S_and_next_on_left = (cur_dir == 2) and (path[i + 1] == i_neighbors['left'])
        dir_W_and_next_on_top = (cur_dir == 3) and (path[i + 1] == i_neighbors['top'])
        if dir_N_and_next_on_right or dir_E_and_next_on_bottom or dir_S_and_next_on_left or dir_W_and_next_on_top:
            action_list.append({"type": "rt"})
            action_list.append({"type": "fd"})

        if not (dir_N_and_next_on_top or
                dir_E_and_next_on_right or
                dir_S_and_next_on_bottom or
                dir_W_and_next_on_left or
                dir_N_and_next_on_bottom or
                dir_E_and_next_on_left or
                dir_S_and_next_on_top or
                dir_W_and_next_on_right):
            # update the current direction
            if path[i + 1] == i_neighbors['top']:  # next node is on the top
                cur_dir = 0
            elif path[i + 1] == i_neighbors['right']:
                cur_dir = 1
            elif path[i + 1] == i_neighbors['bottom']:
                cur_dir = 2
            elif path[i + 1] == i_neighbors['left']:
                cur_dir = 3

    # a trace with n nodes has n-1 edges. Each edge implies a fd/bk required.
    # fd/bk + #turns is the total basic actions required
    code_json = {"run": action_list}
    return len(action_list), cur_dir, code_json
