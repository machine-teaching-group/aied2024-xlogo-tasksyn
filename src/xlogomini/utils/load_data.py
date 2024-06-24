import json
import os


def load_code_json(task_id):
    base_path = os.path.dirname(os.path.abspath(__file__))
    code_file = open(os.path.join(base_path, '../assets/xlogomini_codes.json'), 'r')
    code_json = json.load(code_file)[task_id]['code_json']
    return code_json


def load_cons_json(task_id):
    base_path = os.path.dirname(os.path.abspath(__file__))
    cons_file = open(os.path.join(base_path, '../assets/xlogomini_constraints.json'), 'r')
    cons_json = json.load(cons_file)[task_id]['constraints']
    return cons_json


def load_goal_json(task_id):
    base_path = os.path.dirname(os.path.abspath(__file__))
    goal_file = open(os.path.join(base_path, '../assets/xlogomini_goals.json'), 'r')
    goal_json = json.load(goal_file)[task_id]['goal']
    return goal_json


def load_world_json(task_id):
    base_path = os.path.dirname(os.path.abspath(__file__))
    world_file = open(os.path.join(base_path, '../assets/xlogomini_worlds.json'), 'r')
    world_json = json.load(world_file)[task_id]['world_json']
    return world_json


def load_task_json(task_id):
    world_json = load_world_json(task_id)
    goal_json = load_goal_json(task_id)
    cons_json = load_cons_json(task_id)
    task_json = {}
    task_json.update(world_json)
    task_json.update({"goal": goal_json, "constraints": cons_json})
    return task_json
