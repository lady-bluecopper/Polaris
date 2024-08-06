import numpy as np
from collections import defaultdict
from tqdm.contrib.concurrent import process_map
import time
import random
import sys
sys.path.insert(1,'../')
import src.utils as ut # type: ignore


def get_graph_parallel_chains(sampler,
                              count: int=1,
                              swaps: int=-1,
                              max_workers: int=4,
                              actual_swaps: bool=False,
                              seed: int=0):
        '''
        INPUT
        ======
        sampler: which algorithm use to move in the Markov graph.
        count (int): number of graphs to sample from the Configuration model.
        swaps (int): number of swaps before returning the current state.
        max_workers (int): number of concurrent threads.
        actual_swaps (bool): if True, an iteration is counted only if the
                             transition to the next state was accepted.
        seed (int): for reproducibility.
        
        OUTPUT
        ======
        List of graphs sampled from the state space.
        '''
        if swaps < 0:
            swaps = sampler.m * np.log(sampler.m)
        inputs = []
        for i in range(count):
            inputs.append([sampler, seed + i, swaps])
        if actual_swaps:
            return process_map(sample_graph_exact_swaps, inputs, max_workers=max_workers)
        return process_map(sample_graph, inputs, max_workers=max_workers)


def sample_graph_exact_swaps(inp):
    '''
    An iteration is counted only if the
    transition to the next state was accepted.
    
    INPUT
    ======
    sampler (object): sampler to use to sample the graph.
    seed (int): for reproducibility.
    swaps (int): number of swaps before returning the current state.
    '''
    sampler = inp[0]
    seed = inp[1]
    swaps = inp[2]
    
    random.seed(seed)
    swapped = [-1, -1, -1, -1]
    actual_swaps = 0

    A = ut.copy_weight_dict(sampler.A)
    edges = ut.copy_edge_list(sampler.edge_list)
    start = time.time()
    while actual_swaps < swaps:
        sampler.MCMC_step(A, edges, swapped)
        if swapped[0] != -1:
            actual_swaps += 1
            swapped[0] = -1
    end = time.time() - start
    return edges, end


def sample_graph(inp):
    '''
    INPUT
    ======
    sampler (object): sampler to use to sample the graph.
    seed (int): for reproducibility.
    swaps (int): number of swaps before returning the current state.
    '''
    sampler = inp[0]
    seed = inp[1]
    swaps = inp[2]
    
    random.seed(seed)
    swapped = [-1, -1, -1, -1]
    
    A = ut.copy_weight_dict(sampler.A)
    edges = ut.copy_edge_list(sampler.edge_list)
    start = time.time()
    it = 0
    while it < swaps:
        P = sampler.MCMC_step(A, edges, swapped)
        if P != -2:
            it += 1
    end = time.time() - start

    # SANITY CHECK        
    # deg_seq_g = ut.compute_degree_sequence_from_A(sampler.A)
    # jlm_g1 = ut.compute_JLM_from_A(sampler.A, sampler.node_labels)
    # same_degs = ut.check_degree_sequences(sampler.degrees, deg_seq_g)
    # print(f'SAME DEGREE SEQUENCE={same_degs}')
    
    # deg_seq_g = ut.compute_degree_sequence_from_list(edges)
    # jlm_g2 = ut.compute_JLM_from_list(edges, sampler.node_labels)
    # same_degs = ut.check_degree_sequences(sampler.degrees, deg_seq_g)
    # same_jlm = ut.check_JLM(jlm_g1, jlm_g2)
    # print(f'SAME DEGREE SEQUENCE 2={same_degs}')
    # print(f'SAME JLM 2={same_jlm}')
    return edges, end


def progress_chain(inp):
    '''
    Procedure used in the convergence experiment.
    
    INPUT
    ======
    num_swaps_needed (int): number of moves in the Markov graph to perform.
    last_r: (float): degree assortativity of the current state.  
    denominator (int): denominator of Eq (2) paper Dutta et al. 2023.
    increment (int): running time will be saved every increment steps in the Markov graph.
    seed (int): for reproducibility.
    idx (int): id of the chain.
    sampler (object): sampler to use to move in the state space.
    sampler_name (str): name of the sampler.
    '''
    num_swaps_needed = inp[0]
    last_r = inp[1]
    denominator = inp[2]
    increment = inp[3]
    seed = inp[4]
    idx = inp[5]
    sampler = inp[6]
    sampler_name = inp[7]
    
    random.seed(idx+seed)
    counter = 0
    # degree assortativity values
    assortativities = []
    # Manhattan distance values
    perturbations = []
    probs = dict()
    probs['Accepted'] = defaultdict(int)
    probs['Rejected'] = defaultdict(int)
    step_times = defaultdict(int)
    times = dict()
    actual_moves = 0
    swaps = 0
    swapped = [-1, -1, -1, -1]
    
    last_A = ut.copy_weight_dict(sampler.A)
    last_edge_list = ut.copy_edge_list(sampler.edge_list)
    
    elapsed = 0
    while swaps < num_swaps_needed:
        step_start = time.time_ns()
        P = sampler.MCMC_step(last_A, last_edge_list, swapped)
        step_end = time.time_ns() - step_start
        elapsed += step_end
        delta_r = 0
        # A swap was performed
        if swapped[0] != -1:
            actual_moves += 1
            num = sampler.degrees[swapped[0]] * sampler.degrees[swapped[2]]
            num += sampler.degrees[swapped[1]] * sampler.degrees[swapped[3]]
            num -= sampler.degrees[swapped[0]] * sampler.degrees[swapped[1]]
            num -= sampler.degrees[swapped[2]] * sampler.degrees[swapped[3]]
            delta_r = 2 * num * 2 * sampler.m / denominator
            swapped[0] = -1
            step_times['Accepted (ns)'] += step_end
            probs['Accepted'][str(P)] += 1
        else:
            step_times['Rejected (ns)'] += step_end
            probs['Rejected'][str(P)] += 1
        last_r += delta_r
        swaps += 1

        if counter % increment == 0:
            times[str(swaps)] = elapsed
            assortativities.append(last_r)
            p_score = ut.compute_perturbation_score(sampler.A, last_A)
            perturbations.append(p_score)
        
        counter += 1
                    
    all_stats = dict()
    all_stats['Time (ns)'] = elapsed
    all_stats['Acceptance Ratio'] = actual_moves / num_swaps_needed
    all_stats['Number of Swaps'] = num_swaps_needed
    all_stats['Num Edges'] = sampler.m
    all_stats['Chain'] = idx
    all_stats['Time at Iter (ns)'] = times
    all_stats['Total Time Accepted (ns)'] = step_times['Accepted (ns)']
    all_stats['Total Time Rejected (ns)'] = step_times['Rejected (ns)']
    all_stats['Method'] = sampler_name

    return assortativities, perturbations, probs, all_stats
