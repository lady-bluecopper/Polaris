import sys
import os
sys.path.insert(1,'../')
import src.utils as ut # type: ignore
import src.loaders as ld # type: ignore
import src.ConfigModel_MCMC as mcmc # type: ignore
import src.MCMC_LA as la # type: ignore
import src.MCMC_LW as lw # type: ignore
import src.CM as cm # type: ignore
import numpy as np


def run_sampler(edges: list[tuple[int,int]],
                degrees: dict[int, int],
                node_labels: dict[int, int],
                num_graphs: int,
                swaps: int,
                algo: str, 
                out_dir: str,
                graph_name: str,
                max_workers: int=10,
                actual_swaps: bool=False,
                seed: int=0):
    '''
    INPUT
    ======
    edges (list): list of edges in the original graph.
    degrees (dict): degree of each node.
    node_labels (dict): label of each node.
    num_graphs (int): number of random graphs to generate.
    swaps (int): number of iterations to perform before returning the current state. 
    algo (str): name of the sampler to use to move in the state space.
    out_dir (str): where the graph should be stored.
    graph_name (str): name of the observed graph.
    max_workers (int): max number of concurrent threads.
    actual_swaps (bool): if True, an iteration is counted only if the
                         transition to the next state was accepted.
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
        
    mcmc.get_graph_parallel_chains(sampler, 
                                   out_dir,
                                   graph_name,
                                   algo,
                                   num_graphs, 
                                   swaps, 
                                   max_workers, 
                                   actual_swaps, 
                                   seed) 
    

if __name__ == '__main__':

    args = ld.read_arguments()

    base_path = args['base_path']
    data_dir = args['data_dir']
    graph_name = args['graph_name']
    num_graphs = args['num_samples']
    sampl_name = args['algorithm']
    base_seed = args['seed']
    if args['actual_swaps'] == 'True':
        actual = True
    else:
        actual = False
    
    data_dir = f'{base_path}/{data_dir}'
    out_dir = f'{base_path}/out'
    os.makedirs(out_dir, exist_ok=True)
    
    file_path = f'{data_dir}/{graph_name}.tsv'
    edges = ld.read_tsv_graph(file_path)
    degrees = ut.compute_degree_sequence_from_list(edges)
    
    lab_path = f'{data_dir}/{graph_name}_labels.tsv'
    node_labels, inner_outer_labels = ld.read_node_labels(lab_path, degrees.keys())
    
    if args['num_swaps'] < 0:
        swaps = int(len(edges) * np.log(len(edges)))    
    else:
        swaps = args['num_swaps']
        
    run_sampler(edges=edges,
                degrees=degrees, # type: ignore
                node_labels=node_labels,
                num_graphs=num_graphs,
                swaps=swaps,
                algo=sampl_name,
                out_dir=out_dir,
                graph_name=graph_name,
                max_workers=min(num_graphs, args['num_workers']),
                actual_swaps=actual,
                seed=base_seed)
