#!/usr/bin/env python
# Copyright 2017 Blue Marble Analytics LLC. All rights reserved.

"""
Various auxiliary functions used in other modules
"""

from importlib import import_module
import os.path
import pandas as pd
import traceback


def get_required_subtype_modules_from_projects_file(
    scenario_directory, subproblem, stage, which_type
):
    """
    Get a list of unique types from projects.tab.
    """
    project_df = pd.read_csv(
        os.path.join(
            scenario_directory, str(subproblem), str(stage), "inputs",
            "projects.tab"
        ),
        sep="\t"
    )

    required_modules = project_df[which_type].unique()

    return required_modules


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
            print("ERROR! Unable to import subtype module " + m + ".")
            traceback.print_exc()

    return imported_subtype_modules


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


# TODO: make this function even more generic, so that we can initialize a
#  subset of any set, not just PROJECTS
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


def cursor_to_df(cursor):
    """
    Convert the cursor object with query results into a pandas DataFrame.
    :param cursor: cursor object with query result
    :return:
    """
    df = pd.DataFrame(
        data=cursor.fetchall(),
        columns=[s[0] for s in cursor.description]
    )
    return df


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
