#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Various auxiliary functions used in other modules
"""
from __future__ import print_function


from builtins import str
from importlib import import_module
import os.path

from db.common_functions import spin_on_database_lock


def load_subtype_modules(
        required_subtype_modules, package, required_attributes
):
    """
    Load subtype modules (e.g. capacity types, operational types, etc).
    This function will also check that the subtype modules have certain
    required attributes.

    :param required_subtype_modules: name of the subtype_modules to be loaded
    :param package: The name of the package the subtype modules reside in. E.g.
        capacity_type modules live in gridpath.project.capacity.capacity_types
    :param required_attributes: module attributes that are required for each of
        the specified required_subtype_modules. E.g. each capacity_type will
        need to have a "capacity_rule" attribute.
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    imported_subtype_modules = dict()
    for m in required_subtype_modules:
        try:
            imp_m = \
                import_module(
                    "." + m,
                    package=package
                )
            imported_subtype_modules[m] = imp_m
            for a in required_attributes:
                if hasattr(imp_m, a):
                    pass
                else:
                    raise Exception(
                        "ERROR! No " + str(a) + " function in subtype module "
                        + str(imp_m) + ".")
        except ImportError:
            print("ERROR! Subtype module " + m + " not found.")

    return imported_subtype_modules


def load_gen_storage_capacity_type_modules(required_capacity_modules):
    """
    Load a specified set of capacity type modules
    :param required_capacity_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_capacity_modules,
        package="gridpath.project.capacity.capacity_types",
        required_attributes=["capacity_rule", "capacity_cost_rule"]
    )


def load_reserve_type_modules(required_reserve_modules):
    """
    Load a specified set of reserve modules
    :param required_reserve_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_reserve_modules,
        package="gridpath.project.operations.reserves",
        required_attributes=[]
    )


# TODO: add curtailment rules as required?
def load_operational_type_modules(required_operational_modules):
    """
    Load a specified set of operational type modules
    :param required_operational_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_operational_modules,
        package="gridpath.project.operations.operational_types",
        required_attributes=["power_provision_rule", "variable_om_cost_rule",
                             "startup_cost_rule",
                             "shutdown_cost_rule", "startup_fuel_burn_rule"]
    )


def load_prm_type_modules(required_prm_modules):
    """
    Load a specified set of prm type modules
    :param required_prm_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_prm_modules,
        package="gridpath.project.reliability.prm.prm_types",
        required_attributes=["elcc_eligible_capacity_rule",]
    )


def load_tx_capacity_type_modules(required_tx_capacity_modules):
    """
    Load a specified set of transmission capacity type modules
    :param required_tx_capacity_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_tx_capacity_modules,
        package="gridpath.transmission.capacity.capacity_types",
        required_attributes=["min_transmission_capacity_rule",
                             "max_transmission_capacity_rule"]
    )


def load_tx_operational_type_modules(required_tx_operational_modules):
    """
    Load a specified set of transmission operational type modules
    :param required_tx_operational_modules:
    :return: dictionary with the imported subtype modules
        {name of subtype module: Python module object}
    """
    return load_subtype_modules(
        required_subtype_modules=required_tx_operational_modules,
        package="gridpath.transmission.operations.operational_types",
        required_attributes=[
            "transmit_power_rule", "transmit_power_losses_lz_from_rule",
            "transmit_power_losses_lz_to_rule"
        ]
    )


def join_sets(mod, set_list):
    """
    Join sets in a list.
    If list contains only a single set, return just that set.

    :param mod:
    :param set_list:
    :return:
    """
    if len(set_list) == 0:
        return []
    elif len(set_list) == 1:
        return getattr(mod, set_list[0])
    else:
        joined_set = set()
        for s in set_list:
            for element in getattr(mod, s):
                joined_set.add(element)
    return joined_set


def generator_subset_init(generator_parameter, expected_type):
    """
    Initialize subsets of generators by subtype based on subtype flags.
    Need to return a function with the model as argument, i.e. 'lambda mod'
    because we can only iterate over the
    generators after data is loaded; then we can pass the abstract model to the
    initialization function.

    :param generator_parameter:
    :param expected_type:
    :return:
    """
    return lambda mod: \
        list(g for g in mod.PROJECTS if getattr(mod, generator_parameter)[g]
             == expected_type)


def check_list_has_single_item(l, error_msg):
    if len(l) > 1:
        raise ValueError(error_msg)
    else:
        pass


def find_list_item_position(l, item):
    """

    :param l:
    :param item:
    :return:
    """
    return [i for i, element in enumerate(l) if element == item]


def check_list_items_are_unique(l):
    """
    Check if items in a list are unique

    :param l:
    A list
    :return:
    Nothing
    """
    for item in l:
        positions = find_list_item_position(l, item)
        check_list_has_single_item(
            l=positions,
            error_msg="Service " + str(item) + " is specified more than once" +
            " in generators.tab.")


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


# TODO: handle non-existing scenarios/scenario_ids
def get_scenario_id_and_name(scenario_id_arg, scenario_name_arg, c, script):
    """
    Get the scenario_id and the scenario_ name. Usually only one is given (the
    other one will be 'None'), so this functions determine the missing one from
    the one that is provided. If both are provided, this function checks whether
    they match.

    :param scenario_id_arg: 
    :param scenario_name_arg: 
    :param c: 
    :param script: 
    :return: (scenario_id, scenario_name)
    """
    if scenario_id_arg is None and scenario_name_arg is None:
        raise TypeError(
            """ERROR: Either scenario_id or scenario_name must be specified. 
            Run 'python """ + script + """'.py --help' for help."""
        )
    elif scenario_id_arg is not None and scenario_name_arg is None:
        scenario_id = scenario_id_arg
        scenario_name = c.execute(
            """SELECT scenario_name
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id)
        ).fetchone()[0]
    elif scenario_id_arg is None and scenario_name_arg is not None:
        scenario_name = scenario_name_arg
        scenario_id = c.execute(
            """SELECT scenario_id
               FROM scenarios
               WHERE scenario_name = '{}';""".format(scenario_name)
        ).fetchone()[0]
    else:
        # If both scenario_id and scenario_name
        scenario_name_db = c.execute(
            """SELECT scenario_name
               FROM scenarios
               WHERE scenario_id = {};""".format(scenario_id_arg)
        ).fetchone()[0]
        if scenario_name_db == scenario_name_arg:
            scenario_id = scenario_id_arg
            scenario_name = scenario_name_arg
        else:
            raise ValueError("ERROR: scenario_id and scenario_name don't "
                             "match in database.")

    return scenario_id, scenario_name


def setup_results_import(conn, cursor, table, scenario_id, subproblem, stage):
    """
    :param conn: the connection object
    :param cursor: the cursor object
    :param table: the results table we'll be inserting into
    :param scenario_id:
    :param subproblem:
    :param stage:

    Prepare for results import: 1) delete prior results and 2) create a
    temporary table we'll insert into first (for sorting before inserting
    into the final table)
    """
    # Delete prior results
    del_sql = """
        DELETE FROM {} 
        WHERE scenario_id = ?
        AND subproblem_id = ?
        AND stage_id = ?;
        """.format(table)
    spin_on_database_lock(conn=conn, cursor=cursor, sql=del_sql,
                          data=(scenario_id, subproblem, stage), many=False)

    # Create temporary table, which we'll use to sort the results before
    # inserting them into our persistent table
    drop_tbl_sql = \
        """DROP TABLE IF EXISTS temp_{}{};
        """.format(table, scenario_id)
    spin_on_database_lock(conn=conn, cursor=cursor, sql=drop_tbl_sql,
                          data=(), many=False)

    # Get the CREATE statemnt for the persistent table
    tbl_sql = cursor.execute("""
        SELECT sql 
        FROM sqlite_master
        WHERE type='table'
        AND name='{}'
        """.format(table)
                             ).fetchone()[0]

    # Create a temporary table with the same structure as the persistent table
    temp_tbl_sql = \
        tbl_sql.replace(
            "CREATE TABLE {}".format(table),
            "CREATE TEMPORARY TABLE temp_{}{}".format(table, scenario_id)
        )

    spin_on_database_lock(conn=conn, cursor=cursor, sql=temp_tbl_sql,
                          data=(), many=False)


def check_for_integer_subdirectories(main_directory):
    """
    :param main_directory: directory where we'll look for subdirectories
    :return: True or False depending on whether subdirectories are found

    Check for subdirectories and return list. Only take subdirectories
    that can be cast to integer (this will exclude other directories
    such as "pass_through_inputs", "inputs", "results", "logs", and so on).
    We do rely on order downstream, so make sure these are sorted.
    """
    subdirectories = sorted(
        [d for d in next(os.walk(main_directory))[1] if is_integer(d)],
        key=int
    )

    # There are subdirectories if the list isn't empty
    return subdirectories


def is_integer(n):
    """
    Check if a value can be cast to integer.
    """
    try:
        int(n)
        return True
    except ValueError:
        return False
