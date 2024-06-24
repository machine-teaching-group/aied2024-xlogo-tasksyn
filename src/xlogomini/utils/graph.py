import networkx as nx
from src.xlogomini.utils.helpers import i2yx, i2y, i2x


def build_empty_world_graph(rows, cols):
    nodes_and_edges = {}
    ntiles = rows * cols

    for i in range(ntiles):
        i_y, i_x = i2yx(i, cols)
        nodes_and_edges[i] = []
        i_neighbors = [i + 1, i - cols, i - 1, i + cols]
        for j in i_neighbors:
            j_y, j_x = i2yx(j, cols)
            i_j_dis = abs(j_y - i_y) + abs(j_x - i_x)
            if j >= 0 and j < ntiles and i_j_dis == 1:
                nodes_and_edges[i].append(j)
    return nx.Graph(nodes_and_edges)


def build_world_graph(world):
    tiles = world.tiles
    rows, cols = world.rows, world.cols
    ntiles = rows * cols

    nodes_and_edges = {}
    # build the graph
    for i in range(ntiles):
        nodes_and_edges[i] = []
        y_i, x_i = i2y(i, cols), i2x(i, cols)
        # allowed?
        if not tiles[y_i, x_i].allowed or not tiles[y_i, x_i].exist:
            continue
        # top wall
        if not tiles[y_i, x_i].wall_top:
            j = i - cols
            y_j, x_j = i2y(j, cols), i2x(j, cols)
            if (j >= 0) and (j < ntiles) and (abs(y_i - y_j) + abs(x_i - x_j) <= 1) and \
                    (tiles[y_j, x_j].allowed) and (not tiles[y_j, x_j].wall_bottom):
                nodes_and_edges[i].append(j)
        # right wall
        if not tiles[y_i, x_i].wall_right:
            j = i + 1
            y_j, x_j = i2y(j, cols), i2x(j, cols)
            if (j >= 0) and (j < ntiles) and (abs(y_i - y_j) + abs(x_i - x_j) <= 1) and \
                    (tiles[y_j, x_j].allowed) and (not tiles[y_j, x_j].wall_left):
                nodes_and_edges[i].append(j)
        # bottom wall
        if not tiles[y_i, x_i].wall_bottom:
            j = i + cols
            y_j, x_j = i2y(j, cols), i2x(j, cols)
            if (j >= 0) and (j < ntiles) and (abs(y_i - y_j) + abs(x_i - x_j) <= 1) and \
                    (tiles[y_j, x_j].allowed) and (not tiles[y_j, x_j].wall_top):
                nodes_and_edges[i].append(j)
        # left wall
        if not tiles[y_i, x_i].wall_left:
            j = i - 1
            y_j, x_j = i2y(j, cols), i2x(j, cols)
            if (j >= 0) and (j < ntiles) and (abs(y_i - y_j) + abs(x_i - x_j) <= 1) and \
                    (tiles[y_j, x_j].allowed) and (not tiles[y_j, x_j].wall_right):
                nodes_and_edges[i].append(j)

    return nx.Graph(nodes_and_edges)


def build_visit_graph(visited):
    G = nx.Graph()
    for i in range(len(visited) - 1):
        G.add_edge(visited[i], visited[i + 1])
    return G


def get_the_closest_shortest_path(rows, cols, visited):
    """
    Return the shortest path that is the closest with the trace and other shortest paths.
    """
    graph = build_empty_world_graph(rows, cols)
    # a list of all shortest paths
    shortest_paths = list(nx.all_shortest_paths(graph, source=visited[0], target=visited[-1]))
    visited_set = set(visited)

    # init
    closest_path = shortest_paths[0]
    min_len = len(visited_set - set(shortest_paths[0]))
    closest_path_idx = 0

    for i in range(len(shortest_paths)):
        cur_len = len(visited_set - set(shortest_paths[i]))  # overlap
        if cur_len < min_len:
            min_len = cur_len
            closest_path = shortest_paths[i]
            closest_path_idx = i
    # remove the closest path
    shortest_paths.pop(closest_path_idx)
    return closest_path, shortest_paths
