# Table Assignment using Simulated Annealing

This code is for BNL EIC Networking Kickoff Event.

Goal: given N participants and M tables for a networking events, folks are evenly distributed among tables such that tablemates have diverse backgrond but similar interests.

## Setup Environment

```bash
conda create -n apoc python=3.10
conda activate apoc
conda install pandas numpy matplotlib openpyxl tqdm
```

## Usage

```bash
python main.py -m <num-of-tables> <input.xlsx>
```

An output `xlsx` file will be produced to map individuals to a table along with the primary topic of the table.

To run this code through multiple table options:

```bash
for m in $(seq 18 27);do python assign_table.py -m $m <input.xlsx> >m$m.txt; done
```


## Some Details.

- Since each participants can choose multiple topics of interests, they are one-hot encoded and the topic score is calculated by maximum overlapping. 
- Diversity score is calculated as $b^k$ where $b$ is a base parameter and $k$ is the number of uniqueness.
- Diffenrent scores are linearly combined.
