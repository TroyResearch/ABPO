# ABPO (Approximate Bi-level Policy Optimization)

## Installation
ABPO requires:
1. Windows 7 or greater or Linux.
2. Python 3.6 or greater. We recommend using Python 3.8.
3. The installation path must be in English.

You can install ABPO through the following steps:
```bash
# clone ABPO repository
git clone https://github.com/TroyResearch/ABPO.git
cd ABPO
# create conda environment
conda env create -f gops_environment.yml
conda activate gops
# install GOPS
pip install -e .
```

## Documentation
The tutorials and API documentation are hosted on [gops.readthedocs.io](https://gops.readthedocs.io/en/latest/).

## Quick Start
This is an example of running finite-horizon Approximate Dynamic Programming (FHADP) on inverted double pendulum environment. 
Train the policy by running:
```bash
python example_train/fhadp/fhadp2_mlp_semitruckpu7dof_serial.py
```
After training, test the policy by running:
```bash
python example_run/run_semitruckpu7dof_abpo.py
```



