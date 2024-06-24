from src.xlogomini.components.code.xlogo_code import Code
import zss


class Node:
    def __init__(self, node_type: str, **kwargs):
        self.node_type = node_type
        self.label = node_type
        self.__dict__.update(kwargs)
        self.children = []

    def __str__(self):
        return self.node_type

    def add_child(self, node):
        self.children.append(node)

    def __repr__(self):
        return f"{self.__class__.__name__}(node_type='{self.node_type}', {self.__dict__})"


class RepeatNode(Node):
    def __init__(self, times, body):
        super().__init__('repeat', times=times, body=body)
        for node_json in body:
            self.add_child(parse_node(node_json))

    def __repr__(self):
        return f"{self.__class__.__name__}(times={self.times}, body={self.children})"


class SetpcNode(Node):
    def __init__(self, value):
        super().__init__('setpc', value=value)

    def __repr__(self):
        return f"{self.__class__.__name__}(value='{self.value}')"


class FdNode(Node):
    def __init__(self):
        super().__init__('fd')

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class BkNode(Node):
    def __init__(self):
        super().__init__('bk')

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class LtNode(Node):
    def __init__(self):
        super().__init__('lt')

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class RtNode(Node):
    def __init__(self):
        super().__init__('rt')

    def __repr__(self):
        return f"{self.__class__.__name__}()"


def parse_code(code_json):
    run_node = Node('run')
    for node_json in code_json['run']:
        run_node.add_child(parse_node(node_json))
    return run_node


def parse_node(node_json):
    node_type = node_json['type']
    # kwargs = node_json.get('kwargs', {})
    if node_type == 'fd':
        node = FdNode()
    elif node_type == 'bk':
        node = BkNode()
    elif node_type == 'lt':
        node = LtNode()
    elif node_type == 'rt':
        node = RtNode()
    elif node_type == 'repeat':
        node = RepeatNode(times=node_json['times'], body=node_json['body'])
    elif node_type == 'setpc':
        node = SetpcNode(value=node_json['value'])
    else:
        raise ValueError(f"Unknown node type: {node_type}")
    for child in node_json.get('children', []):
        node.add_child(parse_node(child))
    return node


def cal_tree_distance(code_json1, code_json2):
    node1 = parse_code(code_json1)
    node2 = parse_code(code_json2)

    def insert_cost(node):
        # return the cost of inserting the given node
        return 1

    def remove_cost(node):
        # return the cost of removing the given node
        return 1

    def update_cost(node1, node2):
        # return the cost of updating node1 to node2
        if node1.node_type != node2.node_type:
            return 1
        # check the attributes of the nodes and return the cost of updating them
        # for example, if you have a "value" attribute:
        # if node1.value != node2.value:
        #     return 1
        return 0

    return zss.distance(node1, node2,
                        get_children=lambda node: node.children,
                        insert_cost=insert_cost,
                        remove_cost=remove_cost,
                        update_cost=update_cost)


if __name__ == '__main__':
    code_json1 = {
        "run": [
            {
                "type" : "repeat",
                "times": 4,
                "body" : [
                    {"type": "fd"},
                    {"type": "fd"},
                    {"type": "rt"}
                ]
            }
        ]
    }
    code_json2 = {
        "run": [
            {
                "type" : "repeat",
                "times": 8,
                "body" : [
                    {"type": "fd"},
                    {"type": "fd"},
                    {"type": "lt"}
                ]
            }
        ]
    }
    code_json3 = {
        "run": [
            {
                "type" : "repeat",
                "times": 4,
                "body" : [
                    {"type": "fd"},
                    {"type": "fd"},
                ]
            },
            {"type": "rt"},
        ]
    }
    code_json4 = {
        "run": [
            {
                "type" : "repeat",
                "times": 4,
                "body" : [
                    {"type": "fd"},
                    {"type": "fd"},
                    {"type": "lt"},
                ]
            }
        ]
    }
    code_json5 = {
        "run": [
            {
                "type" : "repeat",
                "times": 4,
                "body" : [
                    {"type": "fd"},
                    {"type": "bk"},
                    {"type": "lt"},
                ],
            },
            {"type": "rt"}
        ]
    }

    code1 = parse_code(code_json1)
    code2 = parse_code(code_json2)
    code3 = parse_code(code_json3)
    code4 = parse_code(code_json4)
    code5 = parse_code(code_json5)

    print(Code(code_json1))
    print(Code(code_json2))
    print(Code(code_json3))
    print(Code(code_json4))
    print(Code(code_json5))

    # create a list of codes
    code_jsons = [code_json1, code_json2, code_json3, code_json4, code_json5]

    # calculate the distance matrix
    dist_matrix = []
    for i in range(len(code_jsons)):
        row = []
        for j in range(len(code_jsons)):
            distance = cal_tree_distance(code_jsons[i], code_jsons[j])
            row.append(distance)
        dist_matrix.append(row)

    # print the distance matrix
    for row in dist_matrix:
        print(row)
