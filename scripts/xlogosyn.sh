#!/bin/bash
export PYTHONPATH="./:$PYTHONPATH"
export PYTHONPATH="./src:$PYTHONPATH"

##### The following task_ids are supported #####
#all_task_ids=(
#  "1" "2" "3" "4" "5" "6" "7" "8" "9a" "9b"
#  "10a" "10b" "11" "12a" "12b" "13" "14" "15" "16" "17a" "17b" "18a" "18b" "19"
#  "20" "21" "22" "23" "24" "25" "26" "27" "28" "29"
#  "30" "31" "32" "33" "34" "35" "36" "37" "38" "39"
#  "50" "51" "52" "53" "54" "55" "56" "57" "58" "59"
#  "60" "61" "62" "63" "64" "65" "66" "67"
#  "70" "71" "72" "73"
#  "80" "81" "82" "83" "84" "85" "86" "87"
#  "90" "91" "92" "93" "94"
#  "100" "101" "102" "103" "104" "105"
#)

task_id="87"
diff="easy" # Options: easy, medium, hard

python src/xlogominidatagen/pipeline.py --task_id ${task_id} \
  --n_codes 10 \
  --n_goals 10 \
  --n_init_pos 16 \
  --save_dir "./results/datagen" \
  --n_worlds_per_init 64 \
  --max_workers 2 \
  --diff "easy" \
  --alg xlogosyn \
  --parallel

python src/xlogominidatagen/xlogosyn.py --task_id ${task_id} \
  --diff ${diff} \
  --show_ref \
  --save_img \
  --quartile 4 \
  --selection 'topk' \
  --n_sample 3
