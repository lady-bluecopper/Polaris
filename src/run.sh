#!/usr/bin/env bash

# Array of datasets of interest (without the extension)
datasets=("citeseer" "brexit" "twitter_pol" "phy_citations" "abortion" "uselections" "trivago-clicks" "obamacare" "walmart-trips" "combined" "guncontrol" "patents_decade" "youtube")
# CM = Configuration Model, LA = Polaris-B, LW = Polaris-M
algos=("CM" "LA" "LW")

# number of iterations will be mul_fact * num_edges (convergence experiment)
mul_fact=5
# number of parallel Markov chain (convergence experiment)
D=10
seed=0
# number of graphs to sample
S=100
# path to directory with the datasets
base_path='../..'
# directory with the datasets
data_dir='data'
# statistics will be saved every perc * num_edges iterations (convergence experiment)
perc=0.05
# if the number of steps to perform indicates the number of actual moves in the Markov chain
actual='False'

# 0 = run sampling, 1 = run convergence, 2 = run label experiment
exper=0

if [ "$exper" -eq 0 ]; then
    for db in "${datasets[@]}"; do
        for al in "${algos[@]}"; do
            echo "Running SAMPLING for $db and $al"
            echo "---- `date`"
            python run_sampling.py --seed $seed --num_samples $S --base_path ${base_path} --data_dir ${data_dir} --graph_name $db --algorithm $al --perc $perc --actual_swaps $actual
        done
    done
fi

if [ "$exper" -eq 1 ]; then
    for db in "${datasets[@]}"; do
        for al in "${algos[@]}"; do
            echo "Running CONVERGENCE for $db and $al"
            echo "---- `date`"
            python run.py --seed $seed --base_path ${base_path} --data_dir ${data_dir} --graph_name $db --algorithm $al --perc $perc --D $D --mul_fact ${mul_fact}
        done
    done
fi

if [ "$exper" -eq 2 ]; then
    for al in "${algos[@]}"; do
        echo "Running LABEL EXPERIMENT for $al"
        echo "---- `date`"
        python run_label_scalability.py --seed $seed --num_samples $S --label_list 2,4,8,11 --base_path ${base_path} --data_dir ${data_dir} --graph_name walmart-trips --algorithm $al --perc $perc
    done
fi
