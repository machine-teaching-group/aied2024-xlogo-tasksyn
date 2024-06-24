from src.xlogomini.components.code.xlogo_code import Code
from src.xlogomini.components.world.world import World
from src.xlogomini.components.constraints.code_constraints import CodeConstraints
from src.xlogomini.components.goal.goal import Goal
from src.xlogomini.utils.checkers import check_goal, check_code_constraints
from src.xlogomini.emulator.fast_emulator import FastEmulator


def execute(task_json, code_json):
    world_json = {}
    world_json['turtle'] = task_json['turtle']
    world_json['items'] = task_json['items']
    world_json['tiles'] = task_json['tiles']
    world_json['lines'] = task_json['lines']

    goal_json = task_json['goal']
    cons_json = task_json['constraints']

    world = World.init_from_json(world_json)
    goal = Goal.init_from_json(goal_json)
    constraints = CodeConstraints(cons_json)
    code = Code(code_json)

    emulator = FastEmulator()
    emu_result = emulator.emulate(code, world)

    goal_ok, cons_ok = None, None
    if not emu_result.crashed:
        # check goal
        goal_ok = check_goal(goal, emu_result.inpgrid, emu_result.outgrid)

        # check code constraints
        cons_ok = check_code_constraints(code, constraints)

    return {
        'crashed': emu_result.crashed,
        'crashed_msg': emu_result.outgrid.crashed_msg,
        'goal_ok': goal_ok,
        'cons_ok': cons_ok,
        'err_msg': emu_result.status
    }