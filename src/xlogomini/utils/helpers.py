def yx2i(y, x, cols):
    """
    Convert (y,x) to the index of the world (starting from 0).

    :param y: vertical axis coordinate
    :param x: horizontal axis coordinate
    :param cols: number of the columns of the world
    """
    return y * cols + x


def i2x(i, cols):
    return i % cols


def i2y(i, cols):
    return i // cols


def i2yx(i, cols):
    return i // cols, i % cols


def top_tile_id(i, rows, cols):
    assert i >= 0 and i < rows * cols
    j = i - cols
    y_j, x_j = i2yx(j, cols)
    y_i, x_i = i2yx(i, cols)
    if (j >= 0) and (y_i == y_j + 1) and (x_i == x_j):
        return j
    else:
        return None


def left_tile_id(i, rows, cols):
    assert i >= 0 and i < rows * cols
    j = i - 1
    y_j, x_j = i2yx(j, cols)
    y_i, x_i = i2yx(i, cols)
    if j >= 0 and (y_i == y_j) and (x_i - 1 == x_j):
        return j
    else:
        return None


def right_tile_id(i, rows, cols):
    assert i >= 0 and i < rows * cols
    j = i + 1
    y_j, x_j = i2yx(j, cols)
    y_i, x_i = i2yx(i, cols)
    if (j < rows * cols) and (y_i == y_j) and (x_i + 1 == x_j):
        return j
    else:
        return None


def bottom_tile_id(i, rows, cols):
    assert i >= 0 and i < rows * cols
    j = i + cols
    y_j, x_j = i2yx(j, cols)
    y_i, x_i = i2yx(i, cols)
    if (j < rows * cols) and (y_i + 1 == y_j) and (x_i == x_j):
        return j
    else:
        return None


def get_neighboring_ids(i, rows, cols):
    """
    Return the ids for neighboring tiles of tile `i` in the order: top, left, right, bottom.
    """
    neighbors_ids = {
        "top"   : top_tile_id(i, rows, cols),
        "left"  : left_tile_id(i, rows, cols),
        "right" : right_tile_id(i, rows, cols),
        "bottom": bottom_tile_id(i, rows, cols)
    }
    return neighbors_ids


def get_edges(rows, cols):
    """
    Return a list of edges for the world.
    The start and end points for each edge are sorted in ascending order.

    Examples:
    for a 3*3 world, the function returns:
    [(0, 1), (0, 3), (1, 2), (1, 4), (2, 5), (3, 4), (3, 6), (4, 5), (4, 7), (5, 8), (6, 7), (7, 8)]
    """
    edges = set()
    tiles = rows * cols
    for i in range(tiles):
        ids = get_neighboring_ids(i, rows, cols)
        if ids['top'] is not None:
            edges.add((ids['top'], i))
        if ids['left'] is not None:
            edges.add((ids['left'], i))
        if ids['right'] is not None:
            edges.add((i, ids['right']))
        if ids['bottom'] is not None:
            edges.add((i, ids['bottom']))
    return list(edges)


def lines2goal(lines_json):
    line_spec = [[line] for line in lines_json]
    return [{"name": "draw", "specs": [line_spec]}]
