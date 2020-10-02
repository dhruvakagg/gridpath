#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.


import os.path
import pandas as pd
from pyomo.environ import Set, Expression, Param

from gridpath.auxiliary.auxiliary import join_sets
from gridpath.project.reliability.prm.common_functions import \
    load_prm_type_modules
from gridpath.auxiliary.dynamic_components import prm_cost_group_sets, \
    prm_cost_group_prm_type


def add_model_components(m, d, scenario_directory, subproblem, stage):
    """

    :param m:
    :param d:
    :return:
    """

    m.PRM_COST_GROUPS = Set(
            initialize=lambda mod:
            join_sets(mod, getattr(d, prm_cost_group_sets))
            )

    def group_prm_type_init(mod, group):
        """
        Figure out the PRM type of each group
        :param mod:
        :param group:
        :return:
        """
        for group_set in getattr(d, prm_cost_group_sets):
            for element in getattr(mod, group_set):
                if element == group:
                    return getattr(d, prm_cost_group_prm_type)[group_set]

    m.group_prm_type = Param(
        m.PRM_COST_GROUPS, within=["energy_only_allowed"],
        initialize=lambda mod, g: group_prm_type_init(mod, g)
    )

    # Import all possible PRM modules
    project_df = pd.read_csv(
        os.path.join(scenario_directory, str(subproblem), str(stage),
                     "inputs", "projects.tab"),
        sep="\t",
        usecols=["project", "prm_type"]
    )
    required_prm_modules = [
        prm_type for prm_type in project_df.prm_type.unique() if
        prm_type != "."
    ]

    imported_prm_modules = load_prm_type_modules(required_prm_modules)

    # For each PRM project type, get the group costs
    def group_cost_rule(mod, group, p):
        prm_type = mod.group_prm_type[group]
        return imported_prm_modules[prm_type]. \
            group_cost_rule(mod, group, p)

    m.PRM_Group_Costs = Expression(
        m.PRM_COST_GROUPS, m.PERIODS,
        rule=group_cost_rule
    )
