#  Description: run a closed-loop system
#  Update: 2025-04-09, : create file

import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'
from gops.sys_simulator.sys_run import PolicyRunner_Multiopt
import numpy as np
init_path = "FHADP2_240823-152712-upper_20-inner_100000/0th-lower"
abpo_path = "FHADP2_240823-152712-upper_20-inner_100000/19th-lower"
result_path = "../results/pyth_semitruckpu7dof/"
runner = PolicyRunner_Multiopt(
    log_policy_dir_list=[result_path+init_path, result_path+abpo_path],
    trained_policy_iteration_list=["100000", "50000"],
    is_init_info=True,
    init_info={"init_state": [0, 0, 0,  0, 0,  0, 0, 0, 0, 0, 0, 0,
                                  0, 0, 0], "ref_time":0.0,"ref_num": 0},
    save_render=False,
    legend_list=["FHADP", "ABPO"],

    use_opt=True, # Use optimal solution for comparison
    opt_args={
        "opt_controller_type": "MPC",
        "num_pred_step": 100,
        "gamma": 1,
        "mode": "shooting",
        "minimize_options": {
            "max_iter": 10,
            "tol": 1e-5,
            "acceptable_tol": 1e-2,
            "acceptable_iter": 10,
        },
        "use_terminal_cost": False,
    },
    multi_opt=True,
    multi_opt_args={"opt_run_times":2,
        "cost_paras_list":[[1, 0.9, 0.8, 0.5, 0.5, 0.5, 0.5, 0.4, 2.0],
                           [1.29999998, 0.866546, 0.58009083, 0.3951817, 0.49991916,
       0.49986335, 0.49631859, 0.37355246, 1.97355246]],
                    },
    constrained_env=False,
    is_tracking=True,
    dt=0.01,
)

runner.run()
