import json
import random
import numpy as np
from tqdm import tqdm
import argparse
import os
from src.xlogomini.components.task import Task
from src.xlogomini.components.code.xlogo_ast import Code
from src.xlogomini.utils.load_data import load_task_json, load_code_json
from src.xlogomini.components.code.xlogo_ast import cal_tree_distance
from src.xlogomini.utils.image_conversions import create_task_code_img_sidebyside
from xlogominidatagen.scoring import compute_task_score


def generate(task_id, diff, quartile=4, show=False, show_ref=False,
             selection='topk', n_sample=3, save=False):
    # load ref task & code
    ref_task_json = load_task_json(task_id)
    ref_code_json = load_code_json(task_id)
    ref_task = Task.init_from_json(ref_task_json)
    ref_code = Code(ref_code_json)

    # load syn task & code
    syn_task_file = f"./results/datagen/task/task_{task_id}_{diff}_xlogosyn.json"
    os.makedirs(os.path.dirname(syn_task_file), exist_ok=True)
    syn_json_list = json.load(open(syn_task_file, 'r'))

    scored_jsons = []

    # sample 10k from syn_json_list in case too many
    syn_json_list = random.sample(syn_json_list, min(10000, len(syn_json_list)))

    # score tasks
    for syn_json in tqdm(syn_json_list, desc=f"Imaging task_{task_id}_{diff}_xlogosyn"):
        # get json
        syn_task_json = syn_json['task_json']
        syn_task_json['constraints'] = syn_json['constraints']
        syn_code_json = syn_json['code_json']

        # get task & code
        syn_task = Task.init_from_json(syn_task_json)
        syn_code = Code(syn_code_json)

        # get score
        task_score = compute_task_score(ref_task=ref_task, syn_task=syn_task, debug=False).item()
        code_score = cal_tree_distance(ref_code.astJson, syn_code.astJson).item()
        final_score = float(task_score + 0.1 * code_score / max(ref_code.n_blocks, syn_code.n_blocks))

        scored_jsons.append(((final_score, task_score, code_score), syn_json))

    # sort
    scored_jsons.sort(key=lambda x: x[0][0], reverse=True)

    # Calculate quartile boundaries
    final_scores = [scores[0] for scores, _ in scored_jsons]
    quartiles = np.percentile(final_scores, [25, 50, 75])

    if quartile == 1:
        quartile_range = (0, quartiles[0])
    elif quartile == 2:
        quartile_range = (quartiles[0], quartiles[1])
    elif quartile == 3:
        quartile_range = (quartiles[1], quartiles[2])
    else:  # quartile == 4
        quartile_range = (quartiles[2], 99999)

    # Filter images in the specified quartile
    quartile_jsons = [(scores, syn_json) for scores, syn_json in scored_jsons if
                      quartile_range[0] <= scores[0] <= quartile_range[1]]

    if selection == 'topk':
        sampled_jsons = quartile_jsons[:min(n_sample, len(quartile_jsons))]
    elif selection == 'sample':
        # Randomly sample n jsons from the quartile
        sampled_jsons = random.sample(quartile_jsons, min(n_sample, len(quartile_jsons)))
    else:
        raise ValueError(f"Invalid selection: {selection}")

    # Show or save sampled images
    for i, (scores, syn_json) in enumerate(sampled_jsons):
        syn_task_json = syn_json['task_json']
        syn_task_json['constraints'] = syn_json['constraints']
        syn_code_json = syn_json['code_json']

        create_task_code_img_sidebyside(syn_task_json=syn_task_json, syn_code_json=syn_code_json,
                                        ref_task_json=ref_task_json, ref_code_json=ref_code_json, show=show,
                                        show_ref=show_ref, diff=diff, save=save,
                                        filename=f"./results/datagen/image/{task_id}_{diff}_xlogosyn_q{quartile}_{selection}{i}.png")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--task_id', type=str, help='', default="1")
    parser.add_argument('--diff', type=str, help='', default='medium')
    parser.add_argument('--show_img', action='store_true', help='show images')
    parser.add_argument('--show_ref', action='store_true', help='add reference task into the image')
    parser.add_argument('--save_img', action='store_true', help='save images')
    parser.add_argument('--quartile', type=int, help='quartile', default=4)
    parser.add_argument('--selection', type=str, help='topk or sample', default='topk')
    parser.add_argument('--n_sample', type=int, help='number of samples', default=5)
    args = parser.parse_args()

    generate(args.task_id, args.diff,
             quartile=args.quartile,
             show=args.show_img,
             show_ref=args.show_ref,
             save=args.save_img,
             selection=args.selection,
             n_sample=args.n_sample)
