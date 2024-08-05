import networkx as nx
import sys
import orjson
import os
from tqdm.contrib.concurrent import process_map
sys.path.insert(1,'../')
import src.loaders as ld # type: ignore
import src.ConfigModel_MCMC as mcmc # type: ignore
import src.MCMC_LA as la # type: ignore
import src.MCMC_LW as lw # type: ignore
import src.CM as cm # type: ignore


def save_data(ass, pert, prob, stats, out_dir, out_base):
    # array of arrays
    print('Saving Assortativity')
    with open(f'{out_dir}/assortativities__{out_base}', 'wb') as out_f:
        # Chain Assortativity List
        for idx, data in enumerate(ass):
            out_f.write(orjson.dumps({str(idx): data}) + b'\n')
    del ass
    # array of arrays
    print('Saving Perturbations')
    with open(f'{out_dir}/perturbations__{out_base}', 'wb') as out_f:
        # Chain Perturbation List
        for idx, data in enumerate(pert):
            out_f.write(orjson.dumps({str(idx): data}) + b'\n')
    del pert
    # array of dicts
    print('Saving Acceptance Probs')
    with open(f'{out_dir}/acceptance__{out_base}', 'wb') as out_f:
        # 'Chain Probability Count'
        for idx, ps_dict in enumerate(prob):
            out_f.write(orjson.dumps({str(idx): ps_dict}) + b'\n')
    del prob
    # array of dicts
    print('Saving STATS')
    with open(f'{out_dir}/stats__{out_base}', 'wb') as out_f:
        for stats_dict in stats:
            out_f.write(orjson.dumps(stats_dict) + b'\n')
    del stats


def run_convergence(edges: list[tuple[int,int]], 
                    degrees: dict[int, int], 
                    node_labels: dict[int, int],
                    perc: float=.05, 
                    D: int=10,
                    max_workers: int=4,
                    mul_fact: float=2.,
                    algo: str='LA',
                    seed: int=0):
        '''
        INPUT
        ======
        edges (list): list of edges in the original graph.
        degrees (dict): degree of each node.
        node_labels (dict): label of each node.
        perc (float): running time will be saved after perc * num_edges iterations.
        D (int): number of parallel MCMC to run.
        max_workers (int): max number of concurrent threads.
        mul_fact (float): percentage of number of edges to use as number of swaps.
        algo (str): name of the sampler to use to move in the state space.
        seed (int): for reproducibility.
        '''
        if algo == 'LA':
            sampler = la.MCMC_LA(edges, degrees, node_labels)
        elif algo == 'LW':
            sampler = lw.MCMC_LW(edges, degrees, node_labels)
        elif algo == 'CM':
            sampler = cm.CM(edges, degrees, node_labels)
        else:
            sys.exit(f'{algo} not supported.')
        denominator = sampler.r_denominator
        num_swaps = int(mul_fact * sampler.m)
        SL = 0
        for e in edges:
            SL += 2 * degrees[e[0]] * degrees[e[1]]
        S1 = 2 * sampler.m
        S2 = sampler.S2
        numerator = S1 * SL - (S2**2)
        r_burn_in = float(numerator) / denominator
        inputs = []
        for idx in range(D):
            row = [num_swaps,
                   r_burn_in, # current degree assortativity
                   denominator,
                   int(sampler.m * perc),
                   seed,
                   idx,
                   sampler,
                   algo]
            inputs.append(row)
        
        outputs = process_map(mcmc.progress_chain, inputs, max_workers=max_workers)
        
        ass_list = [[r_burn_in] + outputs[i][0] for i in range(D)]
        pert_list = [outputs[i][1] for i in range(D)]
        prob_list = [outputs[i][2] for i in range(D)]
        stats_dict = [outputs[i][3] for i in range(D)]
        return ass_list, pert_list, prob_list, stats_dict
    

if __name__ == '__main__':
    
    args = ld.read_arguments()
    
    base_path = args['base_path']
    data_dir = args['data_dir']
    graph_name = args['graph_name']
    sampl_name = args['algorithm']
    base_seed = args['seed']
    mul_fact = args['mul_fact']
    perc = args['perc']
    D = args['D']

    data_dir = f'{base_path}/{data_dir}'
    out_dir = f'{base_path}/out'
    os.makedirs(out_dir, exist_ok=True)
    
    file_path = f'{data_dir}/{graph_name}.tsv'
    edges = ld.read_tsv_graph(file_path)
    G = nx.MultiGraph()
    G.add_edges_from(edges)
    degrees = dict(G.degree()) # type: ignore
    
    lab_path = f'{data_dir}/{graph_name}_labels.tsv'
    node_labels, inner_outer_labels = ld.read_node_labels(lab_path, G.nodes())

    ass_lists, pert_lists, prob_lists, stats_dicts = run_convergence(edges=edges,
                                                                     degrees=degrees,  # type: ignore
                                                                     node_labels=node_labels,
                                                                     perc=perc, 
                                                                     D=D, 
                                                                     mul_fact=mul_fact, 
                                                                     max_workers=min(D, args['num_workers']),
                                                                     algo=sampl_name,
                                                                     seed=base_seed)
    # save data
    out_base = f'{graph_name}__method_{sampl_name}__mul_fact_{mul_fact}__D_{D}__perc_{perc}__seed_{base_seed}'
    save_data(ass_lists, pert_lists, prob_lists, stats_dicts, out_dir, out_base)
