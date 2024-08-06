# Polaris

![Polaris](img/panel.jpg)

## Overview

This package includes Polaris, a network null model for chromatic multigraphs that preserve the joint color matrix, which specifies the number of edges connecting nodes of two given colors.
The JCM is the basic property that determines color assortativity, a fundamental aspect in studying homophily and segregation in polarized networks.

To sample from this ensemble, we develop a suite of two Markov Chain Monte Carlo (MCMC) algorithms: Polaris-B is an adaptation of the generic Metropolis-Hastings algorithm, and Polaris-M is a specialized algorithm with higher acceptance probabilities.

## Content

    data/            ... datasets used in the experimental evaluation
    src/             ... Python and Bash scripts
    environment.yml  ... required Python libraries

## Requirements

To run the Python scripts in the folder *src*, you must install the libraries listed in the file *environment.yml*.

A conda environment can be easily created by running the following commands:

```sh
conda env create -f environment.yml
conda activate pol
```

## Input Format

The file containing the edges in the multigraph must be a tab-separated list of integers, where each integer represents a node and each li e represents an edge.
Node IDs must be integers in the range *[0, N)*, where *N* is the number of distinct nodes.
The filename must have the extension *.tsv*.

The file containing the node labels must be a tab-separated list, where the first element is a node ID and the second element is its label.
The filename must be *<dataset\_name>\_labels.tsv*.

The folder *data* includes some of the datasets used in our experimental evaluation of Polaris.

## License
This package is released under the GNU General Public License.

## Source Files
The *src* folder includes the following files:
 - *CM*: implementation of the Configuration Model.
 - *ConfigModel\_MCMC*: methods to progress the Markov chain and sample random multigraphs.
 - *MCMC\_LA*: implementation of Polaris-B.
 - *MCMC\_LW*: implementation of Polaris-M.
 - *assortativity*: custom implementation of the color assortativity of a chromatic multigraph.
 - *loaders*: argument parser and methods to read data from disk.
 - *run*: Bash script to run the experiments for multiple datasets and samplers.
 - *run\_convergence*: Python script to run the convergence experiment.
 - *run\_sampling*: Python script to run the sampling experiment.
 - *utils*: some useful methods.

## Usage

You can use Polaris-B and Polaris-M by executing the script *run.sh*, which configures all the necessary parameters, briefly introduced in the following section.

Alternatively, you can run the sampling experiment (i.e., generate random multigraphs) using the script *run\_sampling.py*, or conduct the convergence experiment (i.e., study the mixing time of the samplers) using the script *run\_convergence.py*.

By default, *run\_sampling.py* sets the number of iterations to *|E|log(|E|)*. 
Pass the argument *- -num\_swaps* to specify a different number of iterations.

### Parameters

 - *datasets*: list of dataset filenames (without the extension) for the experiment.
 - *base\_path*: path to the directory with the dataset and output directories.
 - *data\_dir*: directory where the datasets are stored.
 - *algos*: list of sampler names for generating random multigraphs (options: CM for Configuration Model, LA for Polaris-B, and LW for Polaris-M).
 - *mul\_fact*: multiplying factor for setting the number of iterations in the convergence experiment. The number of iterations is calculated as *mul\_fact |E|*.
 - *D*: number of parallel Markov chains to run in the convergence experiment.
 - *perc*: frequency (in terms of *perc |E|* iterations) at which statistics are saved during the convergence experiment.
 - *S*: number of random multigraphs to generate in the sampling experiment.
 - *actual*: whether the specified number of iterations in the sampling experiment represents the actual swaps to perform.
 - *num\_workers*: maximum number of threads for parallel computation.
 - *seed*: seed value for reproducibility.
 - *exper*: experimental mode flag. Set to 0 to run the sampling experiment (i.e., generate *S* random multigraphs with the selected sampler) and to 1 to run the convergence experiment (i.e., study the mixing time of the selected sampler).

## Output
The output files will be saved in the folder *base\_path/out*.

The sampling experiment writes a file for each random multigraph generated.
The filename includes the following information:
1. name of the original dataset;
2. name of the sampler used;
3. number of iterations performed by the sampler;
4. runtime (s) to generate the random multigraph;
5. seed used to generate the random multigraph;
6. value of the *actual* parameter.

The convergence experiment writes four output files:
1. *assortativities*: degree assortativity values of the states visited in each Markov chain. Values are stored every *perc |E|* iterations.
2. *perturbations*: Manhattan distance between the original edge weight matrix and the edge weight matrices of the states visited in each Markov chain. Values are stored every *perc |E|* iterations.
3. *acceptance*: transition probabilities of accepted and rejected transitions to the next state.
4. *stats*: various statistics such as elapsed time, acceptance ratio, number of iterations, ID of the Markov chain, total time spent in an iteration where the transition was accepted, total time spent in an iteration where the transition was rejected, number of edges, and sampler name.
