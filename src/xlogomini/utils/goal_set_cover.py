from src.xlogomini.components.goal.goal_edit_distance import cal_tree_distance_for_goal
import numpy as np
from src.xlogomini.components.goal.goal import Goal
from tqdm import tqdm


def get_goal_set_cover(goals):
    # >300: 2, >50: 1, <50: 0.5
    if len(goals) > 300:
        distance_threshold = 2
    elif len(goals) > 50 and len(goals) <= 300:
        distance_threshold = 1
    else:
        distance_threshold = 0.5

    # Step 1: Calculate Distance Matrix
    distance_matrix = np.zeros((len(goals), len(goals)))
    # use tqdm
    for i in tqdm(range(len(goals)), desc="Calculating distance matrix"):
        for j in range(len(goals)):
            if i != j:
                distance_matrix[i][j] = cal_tree_distance_for_goal(goals[i], goals[j])

    # Step 2: Define Set Cover Problem
    # Here, each goal can "cover" goals that are within the distance threshold
    can_cover = [{j for j in range(len(goals)) if distance_matrix[i][j] <= distance_threshold} for i in
                 range(len(goals))]

    # Step 3: Implement Greedy Set Cover Algorithm
    uncovered = set(range(len(goals)))
    selected_goals = []
    selected_goals_str = set()

    while uncovered:
        # Select the goal that covers the most uncovered goals
        goal = max(can_cover, key=lambda s: len(s & uncovered))
        uncovered -= goal
        selected_goals.append(goals[can_cover.index(goal)])
        selected_goals_str.add(Goal.init_from_json(goals[can_cover.index(goal)]))

    return selected_goals