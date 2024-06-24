import json
import random
import os
import time
import argparse
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from src.xlogomini.components.goal.goal import Goal
from src.xlogomini.components.task import Task
from src.xlogomini.components.world.world import World
from src.xlogomini.components.code.xlogo_code import Code
from src.xlogomini.utils.goal_set_cover import get_goal_set_cover
from src.xlogomini.utils.load_data import load_task_json
from src.xlogomini.utils.load_data import load_code_json, load_cons_json, load_world_json, load_goal_json
from src.xlogominidatagen.code_synthesizer import CodeSyn
from src.xlogominidatagen.symexecution.symbolic_executor import SymExecutor
from src.xlogominidatagen.code2task import Code2Tasks
from src.xlogominidatagen.goal_synthesizer import GoalSyn


def parse_difficulty(difficulty):
    if difficulty == 'easy':
        return {
            # for code
            'max_code_inc'  : 0,
            'max_code_dec'  : 0,
            'exact_code_inc': 0,
            'max_cons_inc'  : 0,
            'max_cons_dec'  : 0,
            # for goal
            'same_goal'     : True,
            'max_count_inc' : 0,
            'max_count_dec' : 0,
        }
    elif difficulty == 'medium':
        return {
            # for code
            'max_code_inc'  : 2,
            'max_code_dec'  : -1,
            'exact_code_inc': None,
            'max_cons_inc'  : 0,
            'max_cons_dec'  : 0,
            # for goal
            'same_goal'     : True,
            'max_count_inc' : 0,
            'max_count_dec' : 0,
        }
    elif difficulty == 'hard':
        return {
            # for code
            'max_code_inc'  : 2,
            'max_code_dec'  : 0,
            'exact_code_inc': 2,
            'max_cons_inc'  : 1,
            'max_cons_dec'  : -1,
            # for goal
            'same_goal'     : False,
            'max_count_inc' : 5,
            'max_count_dec' : -1,
        }
    else:
        raise ValueError(f"Unknown difficulty {difficulty}")


def synthesize_tasks_for_code_goal(code_cons, out_goal, ref_world_json, pre_cal_properties,
                                   n_init_pos, n_worlds_per_init, n_tasks, debug, task_id, alg):
    executor = SymExecutor()  # used to calculate min rows and cols

    out_code = Code(code_cons['code_json'])
    ref_world = World.init_from_json(ref_world_json)
    min_rows, min_cols = executor.get_min_world_size(out_code, square=(ref_world.cols == ref_world.cols))
    grid_size = f'{min_rows}x{min_cols}'

    if grid_size not in pre_cal_properties.keys():
        # if ref task is not symmetric (for 91, 92, 94)
        if task_id in ['91', '92', '94']:
            pre_cal_properties[grid_size] = Code2Tasks(rows=min_rows, cols=min_cols,
                                                       ref_world_js=ref_world_json,
                                                       symmetric=False)
        else:
            pre_cal_properties[grid_size] = Code2Tasks(rows=min_rows, cols=min_cols,
                                                       ref_world_js=ref_world_json,
                                                       symmetric=True)

    if alg == 'xlogosyn':
        tasks = pre_cal_properties[grid_size].synthesize(code_json=code_cons['code_json'],
                                                         cons_json=code_cons['constraints'],
                                                         goal=out_goal,
                                                         ref_world_json=ref_world_json,
                                                         n_init=n_init_pos,
                                                         n_worlds_per_init=n_worlds_per_init,
                                                         n_max=n_tasks,
                                                         debug=debug)
    else:
        raise ValueError(f"Unknown algorithm {alg}")

    return [{'task_json'  : task.to_json(task_id),
             'code_json'  : code_cons['code_json'],
             'constraints': code_cons['constraints']} for task in tasks]


def synthesize_code_cons(ref_code_json, ref_cons_json,
                         task_id, difficulty, diff_params, n_codes):
    if os.path.exists(f'{args.save_dir}/code/code_{task_id}_{difficulty}.json'):
        print(f"Loading from the file...")
        out_codes_cons = json.load(open(f'{args.save_dir}/code/code_{task_id}_{difficulty}.json', 'r'))
    else:
        # code mutations
        code_syn = CodeSyn(ref_code_json, ref_cons_json)
        out_codes_cons = code_syn.generate(n_max=n_codes,
                                           save=False,
                                           max_code_inc=diff_params['max_code_inc'],
                                           max_code_dec=diff_params['max_code_dec'],
                                           exact_code_inc=diff_params['exact_code_inc'],
                                           max_cons_inc=diff_params['max_cons_inc'],
                                           max_cons_dec=diff_params['max_cons_dec'])
        os.makedirs(f'{args.save_dir}/code', exist_ok=True)
        json.dump(out_codes_cons, open(f'{args.save_dir}/code/code_{task_id}_{difficulty}.json', 'w'))

    print(f"Total {len(out_codes_cons)} codes synthesized for task {task_id}")
    return out_codes_cons


def synthesize_goals(ref_goal_json, task_id, difficulty, diff_params, n_goals, setcover=False):
    # if ref goal is 'draw', then return itself
    if ref_goal_json[0]['name'] == 'draw':
        print("Ref goal is 'draw', return")
        return [Goal.init_from_json(ref_goal_json)], [Goal.init_from_json(ref_goal_json)]

    if os.path.exists(f'{args.save_dir}/goal/goal_{task_id}_{difficulty}.json'):
        print(f"Loading goals from the file...")
        out_goals = json.load(open(f'{args.save_dir}/goal/goal_{task_id}_{difficulty}.json', 'r'))
        out_goals = [Goal.init_from_json(x) for x in out_goals]
    else:
        # goal mutations
        goal_syn = GoalSyn(ref_goal_json)
        out_goals = goal_syn.generate(n_max=n_goals,
                                      save=False,
                                      max_count_inc=diff_params['max_count_inc'],
                                      max_count_dec=diff_params['max_count_dec'],
                                      same_goal=diff_params['same_goal'])

        os.makedirs(f'{args.save_dir}/goal', exist_ok=True)
        json.dump([x.to_json() for x in out_goals], open(f'{args.save_dir}/goal/goal_{task_id}_{difficulty}.json', 'w'))

    print(f"Total {len(out_goals)} goals synthesized for task {task_id}")

    if setcover:
        # filter the goals, get the set cover
        if os.path.exists(f'{args.save_dir}/datagen/goalsetcover_{task_id}_{difficulty}.json'):
            print(f"Loading goalsetcover from the file...")
            out_goalsetcover = json.load(open(f'{args.save_dir}/datagen/goalsetcover_{task_id}_{difficulty}.json', 'r'))
            out_goalsetcover = [Goal.init_from_json(x) for x in out_goalsetcover]
        else:
            out_goalsetcover = get_goal_set_cover([x.to_json() for x in out_goals])
            json.dump([x for x in out_goalsetcover], open(f'{args.save_dir}/datagen/goalsetcover_{task_id}_{difficulty}.json', 'w'))
            out_goalsetcover = [Goal.init_from_json(x) for x in out_goalsetcover]

        print(f"Total {len(out_goalsetcover)} goals set cover for task {task_id}")
        return out_goals, out_goalsetcover

    return out_goals, out_goals


def synthesize_tasks_wrapper(args_tuple):
    all_tasks = []
    tasks = synthesize_tasks_for_code_goal(*args_tuple)
    if len(tasks) > 0:
        all_tasks.extend(tasks)
    return all_tasks


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--task_id', type=str, help='', default="9a")
    parser.add_argument('--rows', type=int, help='', default=3)
    parser.add_argument('--cols', type=int, help='', default=3)
    parser.add_argument('--diff', type=str, help='', default='easy')
    parser.add_argument('--alg', type=str, help='', default='xlogosyn')

    parser.add_argument('--n_codes', type=int, help='', default=100000)
    parser.add_argument('--n_goals', type=int, help='', default=1000)
    parser.add_argument('--n_init_pos', type=int, help='', default=3)
    parser.add_argument('--n_worlds_per_init', type=int,
                        help='Maximum {} worlds per initial position', default=1000)
    parser.add_argument('--n_tasks_per_triple', type=int,
                        help='Maximum {} tasks per (code, cons, goal) triple', default=3000)

    parser.add_argument('--debug', action='store_true', help='')
    parser.add_argument('--parallel', action='store_true', help='')
    parser.add_argument('--max_workers', type=int, help='', default=24)

    parser.add_argument('--save_dir', type=str, help='', default='./results/datagen')

    args = parser.parse_args()

    # create dir if not exist
    diff_params = parse_difficulty(args.diff)

    # ref code, ref cons, ref goal
    ref_code_json = load_code_json(args.task_id)
    ref_cons_json = load_cons_json(args.task_id)
    ref_goal_json = load_goal_json(args.task_id)
    ref_world_json = load_world_json(args.task_id)
    ref_task_json = load_task_json(args.task_id)

    ref_world = World.init_from_json(ref_world_json)
    ref_code = Code(ref_code_json)
    ref_task = Task.init_from_json(ref_task_json)

    print(f"===== Stage 1: Code Mutation ====")
    out_codes_cons = synthesize_code_cons(ref_code_json=ref_code_json,
                                          ref_cons_json=ref_cons_json,
                                          task_id=args.task_id,
                                          difficulty=args.diff,
                                          diff_params=diff_params,
                                          n_codes=args.n_codes)

    print(f"\n==== Stage 2: Goal Mutation ====")
    out_goals, out_goalsetcovers = synthesize_goals(ref_goal_json=ref_goal_json,
                                                    task_id=args.task_id,
                                                    difficulty=args.diff,
                                                    diff_params=diff_params,
                                                    n_goals=args.n_goals)

    print(f"\n==== Stage 3: Symbolic Execution ====")
    # ------------ gen tasks -------------
    # cal the grid size
    pre_cal_properties = {}

    start_time = time.time()
    # get the local time
    start_local_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    assert len(out_codes_cons) > 0
    assert len(out_goals) > 0

    # shuffle the order of the codes and goals
    random.seed(42)

    # randomly combine code and goal, to generate (code, cons, goal)
    code_cons_goals = []
    for code_cons in out_codes_cons:
        for goal in out_goals:
            code_cons_goals.append({"code_cons": code_cons, "goal": goal})

    # randomly sample 1k (code, cons, goal) triples
    random.shuffle(code_cons_goals)
    code_cons_goals = code_cons_goals[:1000]

    ################ for debugging ###############
    n_code_cons_goal_used = 0
    all_out_tasks = []

    # Create tuples of arguments for parallel processing
    if args.parallel:
        task_args = []
        for out_code_cons_goal in code_cons_goals:
            task_args.append((
                out_code_cons_goal['code_cons'],
                out_code_cons_goal['goal'],
                ref_world_json,
                pre_cal_properties,
                args.n_init_pos,
                args.n_worlds_per_init,
                args.n_tasks_per_triple,  # n_tasks per code-goal pair
                args.debug,
                args.task_id,
                args.alg))

        # Parallel processing
        with ProcessPoolExecutor(max_workers=args.max_workers) as executor:
            future_to_task = {executor.submit(synthesize_tasks_wrapper, arg): arg for arg in task_args}

            # Initialize tqdm progress bar
            with tqdm(total=len(future_to_task), desc=f"Synthesizing {args.task_id}-{args.diff}-{args.alg}",
                      unit="code-cons-goal") as progress_bar:
                for future in as_completed(future_to_task):
                    out_tasks_each_code = future.result()
                    if len(out_tasks_each_code) > 0:
                        n_code_cons_goal_used += 1
                        all_out_tasks.extend(out_tasks_each_code)

                    # Update the progress bar
                    progress_bar.update(1)
    else:
        for out_code_cons_goal in tqdm(code_cons_goals,
                                       desc=f"Synthesizing {args.task_id}-{args.diff}-{args.alg}",
                                       unit="code-cons-goal"):
            # Sequential processing
            out_tasks_each_code = synthesize_tasks_for_code_goal(code_cons=out_code_cons_goal['code_cons'],
                                                                 out_goal=out_code_cons_goal['goal'],
                                                                 ref_world_json=ref_world_json,
                                                                 pre_cal_properties=pre_cal_properties,
                                                                 n_init_pos=args.n_init_pos,
                                                                 n_worlds_per_init=args.n_worlds_per_init,
                                                                 n_tasks=args.n_tasks_per_triple,
                                                                 debug=args.debug,
                                                                 task_id=args.task_id,
                                                                 alg=args.alg)
            if len(out_tasks_each_code) > 0:
                n_code_cons_goal_used += 1
                all_out_tasks.extend(out_tasks_each_code)

    # save args into json, including the time
    params = {
        'args'       : vars(args),
        "start_time" : start_local_time,
        "end_time"   : time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        'diff_params': diff_params,
        'stats'      : {
            "task_id"        : args.task_id,
            "level"          : args.diff,
            "alg"            : args.alg,
            "#code-cons"     : len(out_codes_cons),
            "#goals"         : len(out_goals),
            "#code-cons-goal": n_code_cons_goal_used,
            "#tasks"         : len(all_out_tasks),
            "run_time"       : time.time() - start_time
        },
        # machine details

    }

    # save the number in a file
    os.makedirs(f'{args.save_dir}/params', exist_ok=True)
    json.dump(params, open(f'{args.save_dir}/params/params_{args.task_id}_{args.diff}_{args.alg}.json', 'w'))

    # save the tasks
    os.makedirs(f'{args.save_dir}/task', exist_ok=True)
    json.dump(all_out_tasks, open(f'{args.save_dir}/task/task_{args.task_id}_{args.diff}_{args.alg}.json', 'w'))

    # print params dict with indentation
    print(json.dumps(params, indent=2))

    print('Done')

    end_time = time.time()
    time_spent = (end_time - start_time) / 60
    print(f"Time spent: {time_spent} minutes")
