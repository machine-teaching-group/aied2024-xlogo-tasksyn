import json
from src.xlogomini.components.code import actions
from src.xlogomini.components.constraints.code_constraints import CodeConstraints


class Code:
    def __init__(self, astJson=None):
        """
        Initializes the `Code` object. If an AST JSON is provided, it attempts to parse it;
        otherwise, it creates an empty structure.

        Parameters:
            astJson (dict, optional): The AST JSON representation of the code. Defaults to None.
        """
        if astJson:
            try:
                cursor, open_bodies, success = self._parse_json(astJson)
                assert success
                self.astJson = astJson
                self.cursor = cursor
                self.open_bodies = open_bodies
            except Exception as e:
                print(e)
                raise e
        else:
            self.astJson = {"run": [{"type": "cursor"}]}
            self.cursor = self.astJson["run"]
            self.open_bodies = []

        self.block_cnt, self.depth = self._get_block_cnt(block_cnt={}, body=astJson['run'], depth=0)
        self.n_blocks = sum(self.block_cnt.values())

    def _get_block_cnt(self, block_cnt, body, depth):
        """
        Recursively counts the blocks in the code and determines the depth of the code structure.

        Parameters:
            block_cnt (dict): A dictionary to store the count of each block type.
            body (list): The list of blocks in the code body.
            depth (int): The current depth of the code structure.

        Returns:
            tuple: Updated block count dictionary and the maximum depth.
        """
        max_depth = depth
        for b in body:
            blockType = b['type']
            if blockType not in block_cnt:
                block_cnt[blockType] = 0
            block_cnt[blockType] += 1

            if blockType == 'repeat':
                block_cnt, repeat_depth = self._get_block_cnt(block_cnt, b['body'], depth + 1)
                max_depth = max(depth, repeat_depth)

        return block_cnt, max_depth

    def get_pen_colors(self, pc, body):
        """
        Recursively extracts and returns a set of pen colors used in the code.

        Parameters:
            pc (set): A set to store the pen colors.
            body (list): The list of blocks in the code body.

        Returns:
            set: The set of pen colors used in the code.
        """
        for b in body:
            blockType = b['type']
            if blockType == 'setpc':
                pc.add(b['value'])

            if blockType == 'repeat':
                pc = self.get_pen_colors(pc, b['body'])

        return pc

    def is_done(self):
        """
        Checks if the cursor is at the end of the code.

        Returns:
            bool: True if the cursor is None, indicating the end of the code; False otherwise.
        """
        return self.cursor is None

    def getJson(self):
        """
        Returns the AST JSON representation of the code.

        Returns:
            dict: The AST JSON representation.
        """
        return self.astJson

    def _parse_json(self, astJson):
        """
        Validates the AST JSON format and extracts cursor and open bodies information.

        Parameters:
            astJson (dict): The AST JSON representation of the code.

        Returns:
            tuple: Cursor position, open bodies list, and success flag.
        """
        cursors_list = []

        def _parse_body(block_body, cursor_valid, cursor_path):
            if cursor_path is not None:
                cursor_path.append(block_body)
            for i in range(len(block_body)):
                child = block_body[i]
                cursor_valid_iter = cursor_valid and (i == len(block_body) - 1)
                if child["type"] == "repeat":
                    assert len(child.keys()) == 3
                    assert isinstance(child["times"], int)
                    assert 0 < child["times"] < 13
                    assert _parse_body(child["body"], cursor_valid_iter,
                                       None if not cursor_valid_iter else cursor_path.copy())
                elif child in actions.SET_VARIABLES:
                    assert len(child.keys()) == 2
                    assert isinstance(child["value"], str) or child['value'] is None
                    assert child["value"] in ["red", "black", "blue", "green", "yellow", "white", None]
                elif child in actions.BASIC_ACTIONS:
                    assert len(child.keys()) == 1
                else:
                    assert child["type"] == "cursor", f"Unknown block, found {child}"
                    assert cursor_valid_iter
                    cursors_list.append(cursor_path)
            return True

        assert len(astJson.keys()) == 1
        assert _parse_body(astJson["run"], True, [])
        assert len(cursors_list) <= 1
        success = True
        cursor = cursors_list[0][-1] if len(cursors_list) == 1 else None
        open_bodies = cursors_list[0][:-1] if len(cursors_list) else []
        return cursor, open_bodies, success

    def check_constraints(self, constraint):
        """
        Validates the code against provided constraints.

        Parameters:
            constraint (dict): Constraints to be checked against the code.

        Returns:
            bool: True if all constraints are satisfied, False otherwise.
        """
        constraint = CodeConstraints(constraint)
        for block_name, cnt in self.block_cnt.items():
            if cnt > constraint.at_most(block_name) or cnt < constraint.at_least(block_name):
                return False

        if self.n_blocks > constraint.at_most('all') or self.n_blocks < constraint.at_least('all'):
            return False

        if len(constraint.start) > self.n_blocks:
            return False
        if len(constraint.start) > 0:
            for i in range(len(constraint.start)):
                if self.astJson['run'][i]['type'] != constraint.start[i]:
                    return False
        return True

    def toString(self):
        """
        Returns the AST JSON representation as a formatted string.

        Returns:
            str: The formatted AST JSON string.
        """
        return json.dumps(self.astJson, sort_keys=True, indent=2)

    def __repr__(self):
        """
        Returns a human-readable string representation of the code structure.

        Returns:
            str: The string representation of the code.
        """

        def print_json(obj, indent=0):
            output = ""
            if "type" in obj:
                if obj["type"] == "repeat":
                    output += "  " * indent + "repeat(" + str(obj["times"]) + "){\n"
                    for element in obj["body"]:
                        output += print_json(element, indent + 1)
                    output += "  " * indent + "}\n"
                elif obj["type"] == "setpc":
                    output += "  " * indent + obj["type"] + '(' + obj["value"] + ')\n'
                else:
                    output += "  " * indent + obj["type"] + "\n"
            else:
                for element in obj:
                    output += print_json(element, indent)
            return output

        code_str = ""
        for b in self.astJson['run']:
            code_str += print_json(b, 0)
        return code_str