#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Operational subsets (that can include more than one operational type)
"""

import csv
from pandas import read_csv
import os.path
from pyomo.environ import Var, Set, Param, PositiveReals, PercentFraction

from gridpath.auxiliary.auxiliary import is_number


def add_model_components(m, d):
    """
    Sum up all operational costs and add to the objective function.
    :param m:
    :param d:
    :return:
    """

    # Generators that incur startup/shutdown costs
    m.STARTUP_COST_PROJECTS = Set(within=m.PROJECTS)
    m.startup_cost_per_mw = Param(m.STARTUP_COST_PROJECTS,
                                  within=PositiveReals)

    m.STARTUP_COST_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.STARTUP_COST_PROJECTS))

    m.SHUTDOWN_COST_PROJECTS = Set(within=m.PROJECTS)
    m.shutdown_cost_per_mw = Param(m.SHUTDOWN_COST_PROJECTS,
                                   within=PositiveReals)

    m.SHUTDOWN_COST_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.SHUTDOWN_COST_PROJECTS))

    # TODO: implement check for which generator types can have fuels
    # Fuels and heat rates
    m.FUEL_PROJECTS = Set(within=m.PROJECTS)

    m.fuel = Param(m.FUEL_PROJECTS, within=m.FUELS)
    m.minimum_input_mmbtu_per_hr = Param(m.FUEL_PROJECTS)
    m.inc_heat_rate_mmbtu_per_mwh = Param(m.FUEL_PROJECTS)

    m.FUEL_PROJECT_OPERATIONAL_TIMEPOINTS = \
        Set(dimen=2,
            rule=lambda mod:
            set((g, tmp) for (g, tmp) in mod.PROJECT_OPERATIONAL_TIMEPOINTS
                if g in mod.FUEL_PROJECTS))

    # Availability derate (e.g. for maintenance/planned outages)
    # This can be optionally loaded from external data, but defaults to 1
    m.availability_derate = Param(
        m.PROJECTS, m.HORIZONS, within=PercentFraction, default=1
    )


def load_model_data(m, d, data_portal, scenario_directory, horizon, stage):
    """

    :param m:
    :param d:
    :param data_portal:
    :param scenario_directory:
    :param horizon:
    :param stage:
    :return:
    """

    # TODO: make startup, shutdown, and fuel columns optional

    # STARTUP_COST_PROJECTS
    def determine_startup_cost_projects():
        """
        If numeric values greater than 0 for startup costs are specified
        for some generators, add those generators to the
        STARTUP_COST_PROJECTS subset and initialize the respective startup
        cost param value
        :param mod:
        :return:
        """
        startup_cost_projects = list()
        startup_cost_per_mw = dict()

        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project",
                                   "startup_cost_per_mw"]
                )
        for row in zip(dynamic_components["project"],
                       dynamic_components["startup_cost_per_mw"]):
            if is_number(row[1]) and float(row[1]) > 0:
                startup_cost_projects.append(row[0])
                startup_cost_per_mw[row[0]] = float(row[1])
            else:
                pass

        return startup_cost_projects, startup_cost_per_mw

    data_portal.data()["STARTUP_COST_PROJECTS"] = {
        None: determine_startup_cost_projects()[0]
    }

    data_portal.data()["startup_cost_per_mw"] = \
        determine_startup_cost_projects()[1]

    # SHUTDOWN_COST_PROJECTS
    def determine_shutdown_cost_projects():
        """
        If numeric values greater than 0 for shutdown costs are specified
        for some generators, add those generators to the
        SHUTDOWN_COST_PROJECTS subset and initialize the respective shutdown
        cost param value
        :param mod:
        :return:
        """

        shutdown_cost_projects = list()
        shutdown_cost_per_mw = dict()

        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project",
                                   "shutdown_cost_per_mw"]
                )
        for row in zip(dynamic_components["project"],
                       dynamic_components["shutdown_cost_per_mw"]):
            if is_number(row[1]) and float(row[1]) > 0:
                shutdown_cost_projects.append(row[0])
                shutdown_cost_per_mw[row[0]] = float(row[1])
            else:
                pass

        return shutdown_cost_projects, shutdown_cost_per_mw

    data_portal.data()["SHUTDOWN_COST_PROJECTS"] = {
        None: determine_shutdown_cost_projects()[0]
    }

    data_portal.data()["shutdown_cost_per_mw"] = \
        determine_shutdown_cost_projects()[1]

    # FUEL_PROJECTS
    def determine_fuel_projects():
        """
        E.g. generators that use coal, gas, uranium
        :param mod:
        :return:
        """
        fuel_projects = list()
        fuel = dict()
        minimum_input_mmbtu_per_hr = dict()
        inc_heat_rate_mmbtu_per_mwh = dict()

        dynamic_components = \
            read_csv(
                os.path.join(scenario_directory, "inputs", "projects.tab"),
                sep="\t", usecols=["project",
                                   "fuel",
                                   "minimum_input_mmbtu_per_hr",
                                   "inc_heat_rate_mmbtu_per_mwh"]
                )

        for row in zip(dynamic_components["project"],
                       dynamic_components["fuel"],
                       dynamic_components["minimum_input_mmbtu_per_hr"],
                       dynamic_components["inc_heat_rate_mmbtu_per_mwh"]):
            # print row[0]
            if row[1] != ".":
                fuel_projects.append(row[0])
                fuel[row[0]] = row[1]
                minimum_input_mmbtu_per_hr[row[0]] = float(row[2])
                inc_heat_rate_mmbtu_per_mwh[row[0]] = float(row[3])
            else:
                pass

        return fuel_projects, fuel, minimum_input_mmbtu_per_hr, \
            inc_heat_rate_mmbtu_per_mwh

    data_portal.data()["FUEL_PROJECTS"] = {
        None: determine_fuel_projects()[0]
    }

    data_portal.data()["fuel"] = determine_fuel_projects()[1]
    data_portal.data()["minimum_input_mmbtu_per_hr"] = \
        determine_fuel_projects()[2]
    data_portal.data()["inc_heat_rate_mmbtu_per_mwh"] = \
        determine_fuel_projects()[3]

    # Availability derates
    availability_file = os.path.join(
        scenario_directory, horizon, stage, "inputs",
        "project_availability.tab"
    )

    if os.path.exists(availability_file):
        data_portal.load(
            filename=availability_file,
            param=m.availability_derate
        )
    else:
        pass


def get_inputs_from_database(
        subscenarios, c, inputs_directory
):
    """

    :param subscenarios: 
    :param c: 
    :param inputs_directory: 
    :return: 
    """
    # Project availabilities
    availabilities = c.execute(
        """SELECT project, horizon, availability
        FROM inputs_project_availability
        INNER JOIN inputs_project_portfolios
        USING (project)
        WHERE project_portfolio_scenario_id = {}
        AND project_availability_scenario_id = {}""".format(
            subscenarios.PROJECT_PORTFOLIO_SCENARIO_ID,
            subscenarios.PROJECT_AVAILABILITY_SCENARIO_ID
        )
    )

    with open(os.path.join(inputs_directory, "project_availability.tab"),
              "w") as \
            availability_tab_file:
        writer = csv.writer(availability_tab_file, delimiter="\t")

        writer.writerow(["project", "horizon", "availability_derate"])

        for row in availabilities:
            writer.writerow(row)
