import random
import time
from src.xlogomini.components.constraints.code_constraints import CodeConstraints
from src.xlogomini.components.task import Task
from src.xlogomini.components.world.world import World
from src.xlogominidatagen.symexecution.symbolic_executor import SymExecutor
from src.xlogomini.smt.goal.goal_smt import GoalSMT
from src.xlogomini.smt.goal.draw_smt import DrawSMT
from src.xlogomini.smt.world.world_smt import WorldSMT
from src.xlogomini.components.goal.goal import Goal
from src.xlogomini.utils.load_data import load_code_json, load_goal_json, load_world_json
from src.xlogomini.components.code.xlogo_code import Code
from src.xlogomini.utils.model_conversions import model2values, values2world
from src.xlogomini.utils.formulas import exactly_the_same
from src.xlogomini.utils.load_data import load_code_json, load_cons_json
from src.xlogomini.utils.enums import DEG_MAP
from src.xlogomini.utils.image_conversions import task2image
from src.xlogomini.smt.z3_constraints.trace_optimality import redundant_setpc_in_code
from src.xlogomini.smt.z3_constraints.trace_optimality import properties_for_optimal_trace
from z3 import Solver, sat, Not
import argparse


class Code2Tasks():
    def __init__(self, rows, cols, ref_world_js, symmetric):
        self.rows = rows
        self.cols = cols

        ref_world = World.init_from_json(ref_world_js)
        self.world_smt = WorldSMT(rows=rows, cols=cols)

        # build world type constraints
        if ref_world.markers_used:
            self.world_type_cons = self.world_smt.properties_for_marker_world()
        else:
            self.world_type_cons = self.world_smt.properties_for_item_world(ref_world=ref_world,
                                                                            req_reachable=True,
                                                                            req_sim_items=True,
                                                                            wall_ratio_variation=0.5,
                                                                            forb_ratio_variation=0.5)

        self.pworld_indep_prop = self.world_smt.pworld_indep_properties(
            colors_straw=['red'],
            colors_lemon=['yellow'],
            colors_char=['black'],
            colors_triangle=['red', 'green', 'blue'],
            colors_rectangle=['red', 'green', 'blue'],
            colors_cross=['red', 'green', 'blue'],
            colors_circle=['red', 'green', 'blue', 'yellow',
                           'orange', 'pink', 'purple', 'black'],
            count_straw=[1, 2, 3, 4],
            count_lemon=[1],
            count_shapes=[1],
            count_chars=[1],
            symmetric=symmetric
        )

    def symbolic_execution(self, code_json, n_inti_pos=1):
        code = Code(code_json)
        sym_executor = SymExecutor()
        pworlds = []

        # Create a list of all possible (y, x, dir) tuples
        all_positions = [(y, x, dir) for y in range(self.rows) for x in range(self.cols) for dir in DEG_MAP.keys()]

        # Shuffle the list to ensure random sampling
        random.shuffle(all_positions)

        MAX_TRIES = n_inti_pos * 10
        tries = 0
        # Iterate over the shuffled positions and directions
        for y, x, dir in all_positions:
            tries += 1
            pworld = sym_executor.execute_code(rows=self.rows, cols=self.cols,
                                               code=code,
                                               turtle_y=y, turtle_x=x, turtle_dir=dir)
            if pworld is not None and not redundant_setpc_in_code(code, pworld):
                pworlds.append(pworld)

            if len(pworlds) >= n_inti_pos or tries > MAX_TRIES:
                return pworlds

        return pworlds

    def pworld_to_worlds(self, solver, pworld, n_max):
        syn_worlds = []

        while solver.check() == sat and len(syn_worlds) < n_max:
            model_values = model2values(self.world_smt.vars, solver.model())

            # generated task
            syn_world = values2world(pworld.rows, pworld.cols, model_values=model_values)
            syn_worlds.append(syn_world)

            # next model cannot be exactly the same as the current one
            solver.add(Not(exactly_the_same(self.world_smt.vars, model_values)))

        return syn_worlds

    def synthesize(self, code_json, cons_json, goal, ref_world_json,
                   n_init=1, n_worlds_per_init=1000, n_max=10000,
                   log=False, debug=False):
        """
        Given the code_json, do the following steps:
        1. Generate pworlds:
            First run the code by symbolic execution with `n_init` different initial positions of the turtle.
            After this step, we will get `n_init` pworlds.
        2. Generate worlds:
            First shuffle the pworlds. For each pworld (e.g., different init turtle), generate at most `n_worlds_per_init` worlds.
            However, once we get `n_max` worlds, then stop generating.
        3. Task = world + goal + constraints
            Combine world, goal and constraints to get the tasks.
        """
        cons = CodeConstraints(cons_json)
        ref_world = World.init_from_json(ref_world_json)

        # ----- 1. symbolic execution -----
        pworlds = self.symbolic_execution(code_json=code_json, n_inti_pos=n_init)
        random.shuffle(pworlds)

        # ------ 2. generate worlds ------
        start_time = time.time()
        all_tasks = []
        for pworld in pworlds:
            # only synthesize `n_max` tasks
            if len(all_tasks) >= n_max:
                break
            # pworld-specific goal_smt
            goal_smt = GoalSMT(rows=self.rows,
                               cols=self.cols,
                               vars=self.world_smt.vars,
                               goal=goal,
                               visited=pworld.trace,
                               edge_colors=pworld.edge_colors)
            s = Solver()
            s.add(self.pworld_indep_prop)
            s.add(self.world_type_cons)  # item-based or marker-based constraints
            s.add(goal_smt.properties())
            s.add(self.world_smt.properties_for_pworld(pworld, ref_world.markers_used))

            # add trace optimality for non-draw task
            if not isinstance(goal_smt.tar_smt, DrawSMT):
                s.add(properties_for_optimal_trace(vars=goal_smt.vars, rows=pworld.rows, cols=pworld.cols,
                                                   visited=pworld.trace, init_dir=pworld.init_turtle.dir,
                                                   feasible_path_func=goal_smt.feasible_path,
                                                   trace_max_actions=8, code_constraints=cons_json))

            # generate at most `n_worlds_per_init` worlds for a given pworld
            worlds = self.pworld_to_worlds(solver=s, pworld=pworld, n_max=n_worlds_per_init)
            if len(worlds) > 0:
                for world in worlds:
                    task = Task(world, goal, cons)
                    all_tasks.append(task)
                    if debug:
                        # show the tasks for debugging
                        task2image(task.to_json("debug"), show=True, save=False)
                        print("debugging")

        if log:
            print(f"Total Synthesized Tasks: {len(all_tasks)}")
            print(f"Time spent: {round(time.time() - start_time, 2)}")
        return all_tasks


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--task_id', type=str, help='', default="11")
    parser.add_argument('--grid_size_inc', type=int, help='', default=0)
    parser.add_argument('--log_interval', type=int, help='', default=10000)
    parser.add_argument('--save', action='store_true', help='')
    parser.add_argument('--n_max', type=int, help='', default=20000)
    # params for task synthesis
    parser.add_argument('--symmetric', action='store_true', help='Require the forbidden areas to be symmetric')
    args = parser.parse_args()

    # load json
    code_json = load_code_json(args.task_id)
    cons_json = load_cons_json(args.task_id)
    goal_json = load_goal_json(args.task_id)
    world_json = load_world_json(args.task_id)
    ref_world = World.init_from_json(world_json)

    goal = Goal.init_from_json(goal_json)

    c2t = Code2Tasks(rows=ref_world.rows + args.grid_size_inc,
                     cols=ref_world.cols + args.grid_size_inc,
                     ref_world_js=world_json,
                     symmetric=args.symmetric)
    tasks = c2t.synthesize(code_json=code_json,
                           cons_json=cons_json,
                           goal=goal,
                           ref_world_json=world_json,
                           n_init=30,
                           n_worlds_per_init=3,
                           n_max=50,
                           debug=True)
