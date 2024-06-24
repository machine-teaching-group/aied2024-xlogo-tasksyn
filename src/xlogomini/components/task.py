from src.xlogomini.components.world.world import World
from src.xlogomini.components.goal.goal import Goal
from src.xlogomini.components.constraints.code_constraints import CodeConstraints
from src.xlogomini.utils.enums import *


class Task(object):
    """
    This module defines the `Task` class, which represents a task consisting of a world, a goal,
    and constraints.
    """
    def __init__(self, world, goal, constraints):
        """
        Initializes the `Task` object with a world, a goal, and constraints.

        Parameters:
            world (World): The world object.
            goal (Goal): The goal object.
            constraints (CodeConstraints): The constraints object.
        """
        self.rows = world.rows
        self.cols = world.cols

        self.world = world
        self.goal = goal
        self.constraints = constraints

    @classmethod
    def init_from_json(cls, task_json):
        """
        Class method to initialize a `Task` object from a JSON representation.

        Parameters:
            task_json (dict): A dictionary representing the task.

        Returns:
            Task: An instance of the `Task` class.
        """
        rows = max([tile['y'] for tile in task_json['tiles']]) + 1
        cols = max([tile['x'] for tile in task_json['tiles']]) + 1

        if task_json['goal'] is None or task_json['goal'] == []:
            goal = Goal.init_from_json([{"name" : "draw",
                                         "specs": [[[line] for line in task_json['lines']]]
                                         }])
        else:
            goal = Goal.init_from_json(task_json['goal'])

        return cls(World(rows, cols,
                         task_json['turtle'],
                         task_json['tiles'],
                         task_json['items'],
                         task_json['lines']),
                   goal,
                   CodeConstraints(task_json['constraints']))

    def to_json(self, task_id):
        """
        Converts the task to a JSON representation.

        Parameters:
            task_id (str): The unique identifier for the task.

        Returns:
            dict: A dictionary representing the task in JSON format.
        """
        w = self.world
        turtle_json = {
            "x"        : w.turtle.x,
            "y"        : w.turtle.y,
            "direction": w.turtle.dir
        }
        tiles_json = []
        items_json = []
        for y in range(self.rows):
            for x in range(self.cols):
                tiles_json.append({
                    "x"      : x,
                    "y"      : y,
                    "exist"  : w.tiles[y, x].exist,
                    "allowed": w.tiles[y, x].allowed,
                    "walls"  : {
                        "top"   : w.tiles[y, x].wall_top,
                        "left"  : w.tiles[y, x].wall_left,
                        "right" : w.tiles[y, x].wall_right,
                        "bottom": w.tiles[y, x].wall_bottom
                    }
                })

                if w.items[y, x] is not None:
                    items_json.append({
                        "name" : w.items[y, x].name,
                        "x"    : x,
                        "y"    : y,
                        "count": w.items[y, x].count,
                        "color": w.items[y, x].color,
                    })

        task_json = {
            "id"         : task_id,
            "description": self.task_description(),
            "rows"       : self.rows,
            "cols"       : self.cols,
            "turtle"     : turtle_json,
            "tiles"      : tiles_json,
            "lines"      : w.markers.to_json(),
            "items"      : items_json,
            "goal"       : self.goal.to_json(),
        }
        return task_json

    def task_description(self):
        """
        Generates a natural language description of the task.

        Returns:
            str: A string description of the task.
        """

        def colors_to_natural_language(color_set):
            color_list = sorted([color for color in color_set if color not in {'white'}])

            if len(color_list) == 0:
                return ""
            elif len(color_list) == 1 and 'black' not in color_list:
                return "in " + color_list[0]
            elif len(color_list) == 1 and 'black' in color_list:
                return ""
            elif len(color_list) == 2:
                return "using the colors " + " and ".join(color_list)
            else:
                return "using the colors " + ", ".join(color_list[:-1]) + " and " + color_list[-1]

        draw_colors = colors_to_natural_language(self.world.pen_colors_used)

        if str(self.constraints) == '':
            return_str = f"{self.goal}" + (f' {draw_colors}' if draw_colors != '' else '')
        else:
            return_str = str(self.goal) + (f' {draw_colors}' if draw_colors != '' else '') + '.' + ' ' + str(
                self.constraints)

        return_str = return_str.strip()

        if return_str[-1] != '.':
            return_str += '.'
        return return_str

    def __repr__(self):
        """
        Returns a human-readable string representation of the task.

        Returns:
            str: The string representation of the task.
        """
        goal_info = f"{TCOLORS['green']}-------- goal ------- {TCOLORS['end']}\n" \
                    f"{self.goal}\n"
        cons_info = f"{TCOLORS['green']}---- constraints ---- {TCOLORS['end']}\n" \
                    f"{self.constraints}\n"
        world_info = f"{TCOLORS['green']}--- input world [{self.rows}x{self.cols}] --- {TCOLORS['end']}\n" \
                     f"{self.world}\n"
        return goal_info + cons_info + world_info

    def __eq__(self, other):
        """
        Checks if two `Task` objects are equal.

        Parameters:
            other (Task): Another `Task` object to compare with.

        Returns:
            bool: True if the tasks are equal, False otherwise.
        """
        if isinstance(other, Task):
            return self.__repr__() == other.__repr__()
        else:
            return False

    def __hash__(self):
        """
        Returns the hash of the task representation.

        Returns:
            int: The hash value of the task representation.
        """
        return hash(self.__repr__())