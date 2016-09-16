#!/usr/bin/env python

import os.path
from pyomo.environ import Set, Param, Var, NonNegativeReals


def add_model_components(m, d, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    m.LOAD_ZONES = Set()


def load_model_data(m, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """
    data_portal.load(filename=os.path.join(scenario_directory, "inputs",
                                           "load_zones.tab"),
                     set=m.LOAD_ZONES
                     )
