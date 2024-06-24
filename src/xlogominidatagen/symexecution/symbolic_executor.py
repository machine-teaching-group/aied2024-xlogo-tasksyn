from src.xlogominidatagen.symexecution.symworld import SymWorld
from src.xlogominidatagen.symexecution.decision_maker import RandomDecisionMaker
from src.xlogomini.emulator.fast_emulator import *
from src.xlogomini.utils.enums import DEG_MAP
from src.xlogomini.utils.helpers import i2yx
import json


class SymExecutor(object):
    def __init__(self, decision_maker=None):
        self.emulator = FastEmulator()
        if decision_maker is None:
            self.decision_maker = RandomDecisionMaker.auto_init()

    def _execute(self, code, sym_world):
        """
        Run the `code` in the symbolic world initialized by the given `base_turtle`, `base_tiles`, `base_items`.
        """
        sym_world = SymWorld.init_from_world(world=sym_world,
                                             decision_maker=self.decision_maker)
        emu_result = self.emulator.emulate(code, sym_world)
        return emu_result

    def execute_with_world_from_file(self, code, path):
        init_world = json.load(open(path, 'r'))
        emu_result = self._execute(code=code, sym_world=init_world)
        if emu_result.crashed:
            raise ValueError("The code fails to run in the given world file!")
        return emu_result

    def execute_code(self, rows, cols, code, turtle_y, turtle_x, turtle_dir):
        """
        Run your code with specified (turtle_y, turtle_x, turtle_dir)
        return the pworld if not crashed.
        """
        init_world = {
            "rows"  : rows,
            "cols"  : cols,
            "turtle": {"y"  : turtle_y,
                       "x"  : turtle_x,
                       "dir": turtle_dir
                       },
            "tiles" : [],
            "items" : [],
            "lines" : []
        }
        emu_result = self._execute(sym_world=init_world, code=code)
        # find a non-crash result
        if not emu_result.crashed:
            return emu_result.outgrid
        else:
            return None

    def execute_with_random_world(self, rows, cols, code):
        i, TRIES = 0, 100
        while i < TRIES:
            init_world = {
                "rows"  : rows,
                "cols"  : cols,
                "turtle": {"y"  : self.decision_maker.pick_int(0, rows),
                           "x"  : self.decision_maker.pick_int(0, cols),
                           "dir": self.decision_maker.pick_int(0, len(DEG_MAP))
                           },
                "tiles" : [],
                "items" : [],
                "lines" : []
            }
            emu_result = self._execute(sym_world=init_world, code=code)
            # find a non-crash result
            if not emu_result.crashed:
                return emu_result.outgrid
            i += 1

    def get_min_world_size(self, code, square):
        """
        Run the `code` in a large enough world to calculate the minimal rows and cols
        """
        TEST_SIZE = 8
        sym_world = self.execute_with_random_world(rows=TEST_SIZE, cols=TEST_SIZE, code=code)
        if sym_world is None:
            return 3, 3
        max_x, min_x = -float('inf'), float('inf')
        max_y, min_y = -float('inf'), float('inf')
        for i in sym_world.trace:
            y, x = i2yx(i, TEST_SIZE)
            if y >= max_y:
                max_y = y
            if y <= min_y:
                min_y = y
            if x >= max_x:
                max_x = x
            if x <= min_x:
                min_x = x

        min_rows = int(max_y - min_y + 1)
        min_cols = int(max_x - min_x + 1)

        # minimal rows and cols are 3
        min_rows = max(min_rows, 3)
        min_cols = max(min_cols, 3)

        if square:
            return max(min_rows, min_cols), max(min_rows, min_cols)
        else:
            return min_rows, min_cols
