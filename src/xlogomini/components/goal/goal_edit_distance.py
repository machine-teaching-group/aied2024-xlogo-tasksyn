import zss
from src.xlogomini.components.goal.goal import Goal


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


class ObjectiveNode(Node):
    def __init__(self, name, specs):
        super().__init__(node_type=name, specs=specs)
        for spec in specs:
            self.add_child(SpecNode(spec=spec))

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, specs={self.children})"


class SpecNode(Node):
    def __init__(self, spec):
        super().__init__(node_type='spec', spec=spec)
        spec.sort(key=lambda x: list(x[0].keys())[0])  # always color before name
        for clause in spec:
            self.add_child(ClauseNode(clause=clause))


class ClauseNode(Node):
    def __init__(self, clause):
        super().__init__(node_type='clause', clause=clause)
        for literal in clause:
            self.add_child(LiteralNode(literal=literal))


class LiteralNode(Node):
    def __init__(self, literal):
        name = literal['name'] if 'name' in literal.keys() else 'null'
        color = literal['color'] if 'color' in literal.keys() else 'null'
        count = literal['count'] if 'count' in literal.keys() else 'null'
        super().__init__(node_type=f'{name}_{color}_{count}_{literal["neg"]}',
                         literal=literal)

    def __repr__(self):
        return f"{self.__class__.__name__}()"


def parse_goal(goal_json):
    run_node = Node('run')
    for obj_json in goal_json:
        run_node.add_child(ObjectiveNode(name=obj_json['name'], specs=obj_json['specs']))
    return run_node


def cal_tree_distance_for_goal(goal_json1, goal_json2):
    # handle special case: for sum
    if goal_json1[0]['name'] == 'sum' or goal_json2[0]['name'] == 'sum':
        # abs = 2
        if goal_json1[0]['total_cnt'] - goal_json2[0]['total_cnt'] == 2:
            distance = 3
        # abs = 1
        elif goal_json1[0]['total_cnt'] - goal_json2[0]['total_cnt'] == 1:
            distance = 1
        # abs > 2
        else:
            distance = 2
        return distance

    node1 = parse_goal(goal_json1)
    node2 = parse_goal(goal_json2)

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
    goal1 = [
        {
            "name" : "find",
            "specs": [
                [
                    [
                        {
                            "name": "circle",
                            "neg" : 0
                        }
                    ],
                    [
                        {
                            "color": "pink",
                            "neg"  : 0
                        }
                    ]
                ]
            ]
        },
        {
            "name" : "forbid",
            "specs": [
                [
                    [
                        {
                            "name": "circle",
                            "neg" : 0
                        }
                    ],
                    [
                        {
                            "color": "red",
                            "neg"  : 0
                        }
                    ]
                ]
            ]
        },
        {
            "name" : "forbid",
            "specs": [
                [
                    [
                        {
                            "name": "circle",
                            "neg" : 0
                        }
                    ],
                    [
                        {
                            "color": "green",
                            "neg"  : 0
                        }
                    ]
                ]
            ]
        }
    ]
    goal2 = [
        {
            "name" : "find",
            "specs": [
                [
                    [
                        {
                            "name": "circle",
                            "neg" : 0
                        }
                    ],
                    [
                        {
                            "color": "red",
                            "neg"  : 0
                        }
                    ]
                ]
            ]
        },
        {
            "name" : "forbid",
            "specs": [
                [
                    [
                        {
                            "name": "circle",
                            "neg" : 0
                        }
                    ],
                    [
                        {
                            "color": "green",
                            "neg"  : 0
                        }
                    ]
                ]
            ]
        },
        {
            "name" : "forbid",
            "specs": [
                [
                    [
                        {
                            "name": "cross",
                            "neg" : 0
                        }
                    ],
                    [
                        {
                            "color": "yellow",
                            "neg"  : 0
                        }
                    ]
                ]
            ]
        }
    ]
    goal3 = [
        {
            "name" : "find",
            "specs": [
                [
                    [
                        {
                            "name": "circle",
                            "neg" : 0
                        }
                    ],
                    [
                        {
                            "color": "purple",
                            "neg"  : 0
                        }
                    ]
                ]
            ]
        },
        {
            "name" : "forbid",
            "specs": [
                [
                    [
                        {
                            "name": "circle",
                            "neg" : 0
                        }
                    ],
                    [
                        {
                            "color": "yellow",
                            "neg"  : 0
                        }
                    ]
                ]
            ]
        },
        {
            "name" : "forbid",
            "specs": [
                [
                    [
                        {
                            "name": "circle",
                            "neg" : 0
                        }
                    ],
                    [
                        {
                            "color": "green",
                            "neg"  : 0
                        }
                    ]
                ]
            ]
        }
    ]
    print(Goal.init_from_json(goal1))
    print(Goal.init_from_json(goal2))
    print(Goal.init_from_json(goal3))

    print(cal_tree_distance_for_goal(goal1, goal2))
    print(cal_tree_distance_for_goal(goal1, goal3))
    print(cal_tree_distance_for_goal(goal2, goal3))
