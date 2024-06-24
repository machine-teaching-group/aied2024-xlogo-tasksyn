from src.xlogomini.utils.helpers import get_neighboring_ids
from src.xlogomini.utils.helpers import yx2i, i2y, i2x, i2yx
from src.xlogomini.components.task import Task
from src.xlogomini.utils.enums import ITEM_CHAR, ITEM_FRUIT, ITEM_SHAPE
from src.xlogomini.utils.load_data import load_task_json
from networkx import Graph, node_connected_component
import numpy as np
import torch as th
import copy


def is_standalone_wall(world, index, position='left'):
    """
    Return True if the wall at index with position is standalone.
    """
    y, x = i2yx(index, world.cols)
    assert position == 'left' or position == 'right' or position == 'top' or position == 'bottom'

    # no wall, then false
    if not getattr(world.tiles[y, x], f'wall_{position}'):
        return False

    # get all neighbors
    neighbors = get_neighboring_ids(index, world.rows, world.cols)

    if position == 'top':
        if neighbors['top'] is not None:
            y_, x_ = i2yx(neighbors['top'], world.cols)
            return world.tiles[y, x].allowed and world.tiles[y_, x_].allowed
    elif position == 'left':
        if neighbors['left']:
            y_, x_ = i2yx(neighbors['left'], world.cols)
            return world.tiles[y, x].allowed and world.tiles[y_, x_].allowed
    elif position == 'right':
        if neighbors['right']:
            y_, x_ = i2yx(neighbors['right'], world.cols)
            return world.tiles[y, x].allowed and world.tiles[y_, x_].allowed
    elif position == 'bottom':
        if neighbors['bottom']:
            y_, x_ = i2yx(neighbors['bottom'], world.cols)
            return world.tiles[y, x].allowed and world.tiles[y_, x_].allowed
    return False


def n_standalone_walls(world):
    """
    Preference for world with less standalone walls
    """
    n_standalone_walls = 0
    for idx in range(world.rows * world.cols):
        for pos in ['left', 'right', 'top', 'bottom']:
            if is_standalone_wall(world, idx, pos):
                n_standalone_walls += 1
    return n_standalone_walls


def compute_task_score(ref_task, syn_task, debug=False):
    vis_distance = compute_world_vis_distance(ref_task.world, syn_task.world)
    concept_distance = compute_world_conceptual_distance(ref_task, syn_task)
    goal_distance = compute_goal_distance(ref_task.goal, syn_task.goal)
    cons_distance = compute_cons_distance(ref_task.constraints, syn_task.constraints)
    n_sl_walls = n_standalone_walls(syn_task.world)

    score = (vis_distance - (concept_distance + goal_distance + cons_distance)) * (100 - n_sl_walls) / 100
    if debug:
        print(f"vis_dis: {round(float(vis_distance), 4)}\n"
              f"concept: {round(float(concept_distance), 4)}\n"
              f"goal: {round(float(goal_distance), 4)}\n"
              f"cons: {round(float(cons_distance), 4)}\n"
              f"sl_walls: {n_sl_walls}\n"
              f"total: {round(float(score), 4)}\n"
              )
    return score


def compute_world_conceptual_distance(ref_task, syn_task):
    ref_concep_vec = ref_task.world.getWorldStats()
    syn_concep_vec = syn_task.world.getWorldStats()
    return th.mean((ref_concep_vec - syn_concep_vec) ** 2)


def compute_world_vis_distance(ref_world, syn_world):
    """
    Compute the visual similarity between the reference task and synthesized task.
    Return the similarity score between 0 and 1.
    """
    max_padding = max(ref_world.rows, ref_world.cols, syn_world.rows, syn_world.cols)

    t_ref = ref_world.toPytorchTensor(max_padding)
    t_syn = syn_world.toPytorchTensor(max_padding)

    # remove feature vec for turtle
    t_ref_no_turtle = t_ref[4:, :, :]
    t_syn_no_turtle = t_syn[4:, :, :]

    # turtle dir
    t_ref_turtle_dir = np.array([
        int(ref_world.turtle.dir == 0),
        int(ref_world.turtle.dir == 1),
        int(ref_world.turtle.dir == 2),
        int(ref_world.turtle.dir == 3),
    ])
    t_syn_turtle_dir = np.array([
        int(syn_world.turtle.dir == 0),
        int(syn_world.turtle.dir == 1),
        int(syn_world.turtle.dir == 2),
        int(syn_world.turtle.dir == 3),
    ])
    # turtle pos
    t_ref_turtle_pos = np.zeros(max_padding ** 2)
    t_syn_turtle_pos = np.zeros(max_padding ** 2)
    t_ref_turtle_pos[yx2i(ref_world.turtle.y, ref_world.turtle.x, ref_world.cols)] = 1
    t_syn_turtle_pos[yx2i(syn_world.turtle.y, syn_world.turtle.x, syn_world.cols)] = 1

    t_ref = th.cat([t_ref_no_turtle.view(-1), th.from_numpy(t_ref_turtle_dir), th.from_numpy(t_ref_turtle_pos)], dim=0)
    t_syn = th.cat([t_syn_no_turtle.view(-1), th.from_numpy(t_syn_turtle_dir), th.from_numpy(t_syn_turtle_pos)], dim=0)

    return th.mean((t_ref - t_syn) ** 2)


def compute_goal_distance(ref_goal, syn_goal):
    ref_vec = {
        "find"      : 0,
        "forbid"    : 0,
        "findonly"  : 0,
        "sum"       : 0,
        "concat"    : 0,
        "collectall": 0,
        "draw"      : 0
    }
    syn_vec = copy.deepcopy(ref_vec)

    for obj_name in ref_goal.objs:
        ref_vec[obj_name] += len(ref_goal.objs[obj_name])

    for obj_name in syn_goal.objs:
        syn_vec[obj_name] += len(syn_goal.objs[obj_name])

    ref_vec = th.FloatTensor([v for k, v in ref_vec.items()])
    syn_vec = th.FloatTensor([v for k, v in syn_vec.items()])

    return th.mean((ref_vec - syn_vec) ** 2)


def compute_cons_distance(ref_cons, syn_cons):
    ref_cons = th.FloatTensor([
        len(ref_cons.exactly.cons),
        len(ref_cons.most.cons),
        len(ref_cons.start.cons),
    ]) / 3  # normalized by max len
    syn_cons = th.FloatTensor([
        len(syn_cons.exactly.cons),
        len(syn_cons.most.cons),
        len(syn_cons.start.cons),
    ]) / 3
    return th.mean((ref_cons - syn_cons) ** 2)


def compute_task_reachability(task):
    """
    Compute the reachability of a task. Return the ratio of bad items over all items.

    Note: an item is reachable if the turtle can pass over the item and collect it.
    Sometimes an item is present in the world, but unfortunately it's not reachable
    due to the walls or forbidden areas. This is undoubtedly a bad design of
    task and should be avoided.
    """

    def build_world_graph(world):
        rows, cols = world.rows, world.cols
        ntiles = rows * cols

        tiles = world.tiles
        nodes_and_edges = {}
        # build the graph
        for i in range(ntiles):
            nodes_and_edges[i] = []
            y_i, x_i = i2y(i, cols), i2x(i, cols)
            # allowed?
            if not tiles[y_i, x_i].allowed:
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
        return nodes_and_edges

    rows = task.rows
    cols = task.cols

    turtle = task.world.turtle
    items = task.world.items
    nodes_and_edges = build_world_graph(task.world)

    G = Graph(nodes_and_edges)
    # subax1 = plt.subplot(121)
    # nx.draw(G, with_labels=True)
    # plt.show()

    reachable_pos = node_connected_component(G, yx2i(turtle.y, turtle.x, cols))
    unreachable_pos = set(range(rows * cols)) - reachable_pos

    bad_items = [i for i in unreachable_pos if items[i2y(i, cols), i2x(i, cols)] is not None]
    all_items = [i for i in range(rows * cols) if items[i2y(i, cols), i2x(i, cols)] is not None]

    bad_items_ratio = len(bad_items) / len(all_items)
    return 1 - bad_items_ratio


def compute_task_conceptual_distance(ref_task, syn_task):
    """
    Compute the conceptual distance between two tasks depends on their included concepts.
    """
    assert ref_task.rows == syn_task.rows
    assert ref_task.cols == syn_task.cols

    def get_world_concepts(world):
        """
        Return a dict containing the concepts in the world.
        The concepts include:
            1) item_types_used;
            2) colors_used
            3) counts_used
            4) has_walls
            5) has_forbidden_areas
        """
        item_types, colors, counts, = set(), set(), set()
        has_walls, has_forbidden_areas = 0, 0
        items = world.items
        tiles = world.tiles
        for y in range(world.rows):
            for x in range(world.cols):
                item = items[y, x]
                tile = tiles[y, x]
                # concepts in items
                if item is not None:
                    if item.name in ITEM_FRUIT:
                        item_types.add('fruit')
                    elif item.name in ITEM_SHAPE:
                        item_types.add('shape')
                    elif item.name in ITEM_CHAR:
                        item_types.add('char')
                    else:
                        raise ValueError(f"{item.name} not recognized")
                    colors.add(item.color)
                    counts.add(item.count)

                # concepts in tiles
                if tile.wall_top or tile.wall_left or tile.wall_right or tile.wall_bottom:
                    has_walls = 1
                if not tile.allowed:
                    has_forbidden_areas = 1
        concepts = {
            "item_types_used"   : item_types,
            "colors_used"       : colors,
            "counts_used"       : counts,
            "has_walls"         : has_walls,
            "has_forbidden_area": has_forbidden_areas
        }
        return concepts

    ref_concepts = get_world_concepts(ref_task.world)
    syn_concepts = get_world_concepts(syn_task.world)

    max_type_dis = 3  # only three type at most: fruit, shape, letter
    max_count_dis = 1
    max_color_dis = 1
    max_wall_dis = 1
    max_forbidden_dis = 1

    # item type distance: (X v Y) - (X ∧ Y)
    type_dis = len(ref_concepts['item_types_used'].union(syn_concepts['item_types_used']) \
                   - ref_concepts['item_types_used'].intersection(syn_concepts['item_types_used']))
    # count distance
    ref_2_more_cnts = sum(ref_concepts['counts_used']) > 1
    syn_2_more_cnts = sum(syn_concepts['counts_used']) > 1
    count_dis = abs(int(ref_2_more_cnts) - int(syn_2_more_cnts))
    # color distance
    ref_2_more_clrs = len(ref_concepts['colors_used']) > 1
    syn_2_more_clrs = len(syn_concepts['colors_used']) > 1
    color_dis = abs(int(ref_2_more_clrs) - int(syn_2_more_clrs))
    # wall
    wall_dis = abs(ref_concepts['has_walls'] - syn_concepts['has_walls'])
    # forbidden areas
    forbidden_dis = abs(ref_concepts['has_forbidden_area'] - syn_concepts['has_forbidden_area'])

    concept_distance = type_dis + count_dis + color_dis + wall_dis + forbidden_dis
    max_concept_distance = max_type_dis + max_count_dis + max_color_dis + max_wall_dis + max_forbidden_dis
    return concept_distance / max_concept_distance