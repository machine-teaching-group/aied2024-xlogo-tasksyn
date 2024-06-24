def get_task_goal_type(task_json):
    """
    Return the goal type of the task_json.
    """
    # get the goal type
    if 'goal' not in task_json:
        return 'draw'

    goal = task_json['goal']
    if goal is None or goal == []:
        return 'draw'
    else:
        obj_keys = list(set([o['name'] for o in goal]))
        # if `forbid` in obj_keys, put it in the end
        if 'forbid' in obj_keys:
            obj_keys.remove('forbid')
            obj_keys.append('forbid')
        # convert into string
        obj_keys = '_'.join(obj_keys)
    assert obj_keys in ['find',
                        'findonly',
                        'find_forbid',
                        'collectall',
                        'collectall_forbid',
                        'concat',
                        'draw',
                        'sum',
                        'logic'
                        ], f"Unknown goal type: {obj_keys}"
    return obj_keys
