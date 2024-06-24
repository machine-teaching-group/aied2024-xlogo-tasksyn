from src.xlogomini.components.world.marker import MarkerArray, Marker
from src.xlogomini.components.world.world import World
from z3 import *
from src.xlogomini.utils.helpers import i2yx, i2x, i2y
from src.xlogomini.utils.enums import NAME_VARS, COLOR_VARS


def model2values(vars, model):
    model_values = {}
    for k in vars.keys():
        if isinstance(vars[k], list):
            model_values[k] = [model.eval(var, model_completion=True) for var in vars[k]]
        else:
            model_values[k] = model.eval(vars[k], model_completion=True)
    return model_values


def values2world(rows, cols, model_values):
    """
    Convert the xlogo_smt model to the world representation (smt_model is an interpretation that makes each asserted constraint true).
    """
    tiles = []
    items = []
    markers = MarkerArray(rows, cols)

    for i in range(rows * cols):
        y, x = i2yx(i, cols)
        tiles.append({
            'x'      : x,
            'y'      : y,
            'allowed': is_true(model_values['allowed'][i]),
            'exist'  : is_true(model_values['exist'][i]),
            'walls'  : {
                'top'   : is_true(model_values['topW'][i]),
                'right' : is_true(model_values['rightW'][i]),
                'bottom': is_true(model_values['bottomW'][i]),
                'left'  : is_true(model_values['leftW'][i])
            }
        })

        if not is_true(model_values['noname'][i]):
            for v in NAME_VARS:
                if is_true(model_values[v][i]):
                    name = v
                    break

            for v in COLOR_VARS:
                if is_true(model_values[v][i]):
                    color = v
                    break

            items.append({
                "name" : name,
                "x"    : i2x(i, cols),
                "y"    : i2y(i, cols),
                "count": model_values['count'][i].as_long(),
                "color": color
            })

        markers[y, x] = Marker(x=x, y=y,
                               top=is_true(model_values['topM'][i]),
                               left=is_true(model_values['leftM'][i]),
                               right=is_true(model_values['rightM'][i]),
                               bottom=is_true(model_values['bottomM'][i]),
                               top_color=str(model_values['topM_color'][i]),
                               left_color=str(model_values['leftM_color'][i]),
                               right_color=str(model_values['rightM_color'][i]),
                               bottom_color=str(model_values['bottomM_color'][i]))

    # restore the turtle
    turtle_json = {"x"        : i2x(model_values['turtle'].index(True), cols),
                   "y"        : i2y(model_values['turtle'].index(True), cols),
                   "direction": model_values['dir'].index(True)}

    # line json
    lines_json = markers.to_json()

    world = World(rows, cols, turtle_json, tiles, items, lines_json)
    return world
