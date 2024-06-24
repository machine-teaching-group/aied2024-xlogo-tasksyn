import copy
from src.xlogomini.utils.load_data import load_task_json, load_code_json
from src.xlogomini.utils.image_conversions import create_task_code_img_sidebyside
import argparse


def rotate(task_json):
    max_x = max(tile['x'] for tile in task_json['tiles'])

    # Rotate the coordinates of the items
    for item in task_json['items']:
        item['x'], item['y'] = item['y'], max_x - item['x']

    # Rotate the turtle
    turtle = task_json['turtle']
    turtle['x'], turtle['y'] = turtle['y'], max_x - turtle['x']
    # Update the turtle's direction (assuming 0 is up, 1 is right, 2 is down, and 3 is left)
    turtle['direction'] = (turtle['direction'] - 1) % 4

    # Rotate the tiles and walls
    for tile in task_json['tiles']:
        tile['x'], tile['y'] = tile['y'], max_x - tile['x']
        walls = tile.get('walls', {})
        new_walls = {}
        # Rotate the walls
        if 'top' in walls:
            new_walls['left'] = walls['top']
        if 'right' in walls:
            new_walls['top'] = walls['right']
        if 'bottom' in walls:
            new_walls['right'] = walls['bottom']
        if 'left' in walls:
            new_walls['bottom'] = walls['left']
        tile['walls'] = new_walls

    # Rotate the lines
    for line in task_json['lines']:
        line['x1'], line['y1'] = line['y1'], max_x - line['x1']
        line['x2'], line['y2'] = line['y2'], max_x - line['x2']

    # Rotate the goals if they have line definitions
    for goal in task_json['goal']:
        for spec in goal['specs']:
            for condition in spec:
                if all(key in condition for key in ('x1', 'y1', 'x2', 'y2')):
                    condition['x1'], condition['y1'] = condition['y1'], max_x - condition['x1']
                    condition['x2'], condition['y2'] = condition['y2'], max_x - condition['x2']

    return task_json


def replace(task_json):
    # Replacement rules
    item_replacements = {
        'strawberry': 'lemon',
        # Add more item replacements as needed
    }

    color_replacements = {
        'red': 'green',
        # Add more color replacements as needed
    }

    shape_replacements = {
        'triangle': 'square',
        # Add more shape replacements as needed
    }

    # Replace items and their properties
    for item in task_json['items']:
        if item['name'] in item_replacements:
            item['name'] = item_replacements[item['name']]

        if 'color' in item and item['color'] in color_replacements:
            item['color'] = color_replacements[item['color']]

        # Assuming that the shape is a property of the item
        if 'shape' in item and item['shape'] in shape_replacements:
            item['shape'] = shape_replacements[item['shape']]

    return task_json


def flip_code(code_json):
    # Recursive function to flip 'lt' and 'rt' within commands
    def flip_commands(commands):
        for command in commands:
            if command['type'] == 'lt':
                command['type'] = 'rt'
            elif command['type'] == 'rt':
                command['type'] = 'lt'
            elif command['type'] == 'repeat':
                # Recursively flip commands within the 'repeat' block
                flip_commands(command['body'])

    # Start flipping commands at the top level 'run'
    flip_commands(code_json['run'])
    return code_json


def flip(task_json):
    max_y = max(tile['y'] for tile in task_json['tiles'])

    # Flip the coordinates of the items
    for item in task_json['items']:
        item['y'] = max_y - item['y']

    # Flip the coordinates of the turtle
    turtle = task_json['turtle']
    turtle['y'] = max_y - turtle['y']
    # When flipping vertically, the direction of the turtle should also be flipped if it's up or down.
    if turtle['direction'] == 0:  # Assuming 0 is up and 2 is down
        turtle['direction'] = 2
    elif turtle['direction'] == 2:
        turtle['direction'] = 0

    # Flip the tiles and walls
    for tile in task_json['tiles']:
        tile['y'] = max_y - tile['y']

        # We also need to flip the walls vertically if they exist
        walls = tile.get('walls', {})
        if 'top' in walls or 'bottom' in walls:
            walls['top'], walls['bottom'] = walls.get('bottom', False), walls.get('top', False)

    # Flip the lines
    for line in task_json['lines']:
        line['y1'] = max_y - line['y1']
        line['y2'] = max_y - line['y2']

    # Flip the goals if they have line definitions
    for goal in task_json['goal']:
        for spec in goal['specs']:
            for condition in spec:
                if all(key in condition for key in ('x1', 'y1', 'x2', 'y2')):
                    condition['y1'] = max_y - condition['y1']
                    condition['y2'] = max_y - condition['y2']

    return task_json


def generate(ref_task_json, ref_code_json, diff):
    syn_task_json = copy.deepcopy(ref_task_json)

    if diff == 'easy':
        # rotate
        syn_task_json = rotate(syn_task_json)
        syn_code_json = copy.deepcopy(ref_code_json)
    elif diff == 'medium':
        # flip
        syn_task_json = flip(syn_task_json)
        syn_code_json = flip_code(copy.deepcopy(ref_code_json))

    elif diff == 'hard':
        # rotate
        syn_task_json = rotate(syn_task_json)
        # flip
        syn_task_json = flip(syn_task_json)
        syn_code_json = flip_code(copy.deepcopy(ref_code_json))
    else:
        raise ValueError(f'Unknown diff: {diff}')

    return syn_task_json, syn_code_json


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--task_id', type=str, help='', default="87")
    parser.add_argument('--diff', type=str, help='', default='easy')
    parser.add_argument('--alg', type=str, help='', default='RotateFlip')
    parser.add_argument('--debug', action='store_true', help='')
    parser.add_argument('--show_img', action='store_true', help='show images')
    parser.add_argument('--save_img', action='store_true', help='save images')
    parser.add_argument('--show_ref', action='store_true', help='add ref task to the image')

    args = parser.parse_args()

    # save to json
    ref_task_json = load_task_json(args.task_id)
    ref_code_json = load_code_json(args.task_id)
    syn_task_json, syn_code_json = generate(ref_task_json, ref_code_json, args.diff)

    create_task_code_img_sidebyside(syn_task_json=syn_task_json, syn_code_json=syn_code_json,
                                    ref_task_json=ref_task_json, ref_code_json=ref_code_json, show=False,
                                    diff=args.diff, save=True, show_ref=args.show_ref,
                                    filename=f'./results/datagen/image/{args.task_id}_{args.diff}_rotateflip.png')
