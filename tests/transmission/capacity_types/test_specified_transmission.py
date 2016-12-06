#!/usr/bin/env python

from collections import OrderedDict
from importlib import import_module
import os.path
import sys
import unittest

from tests.common_functions import create_abstract_model, \
    add_components_and_load_data

TEST_DATA_DIRECTORY = \
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data")

# Import prerequisite modules
PREREQUISITE_MODULE_NAMES = [
    "temporal.operations.timepoints", "temporal.investment.periods",
    "transmission"]
NAME_OF_MODULE_BEING_TESTED = \
    "transmission.capacity.capacity_types.specified_transmission"
IMPORTED_PREREQ_MODULES = list()
for mdl in PREREQUISITE_MODULE_NAMES:
    try:
        imported_module = import_module("." + str(mdl), package='modules')
        IMPORTED_PREREQ_MODULES.append(imported_module)
    except ImportError:
        print("ERROR! Module " + str(mdl) + " not found.")
        sys.exit(1)
# Import the module we'll test
try:
    MODULE_BEING_TESTED = import_module("." + NAME_OF_MODULE_BEING_TESTED,
                                        package='modules')
except ImportError:
    print("ERROR! Couldn't import module " + NAME_OF_MODULE_BEING_TESTED +
          " to test.")


class TestSpecifiedTransmission(unittest.TestCase):
    """

    """

    def test_add_model_components(self):
        """
        Test that there are no errors when adding model components
        :return:
        """
        create_abstract_model(prereq_modules=IMPORTED_PREREQ_MODULES,
                              module_to_test=MODULE_BEING_TESTED,
                              test_data_dir=TEST_DATA_DIRECTORY,
                              horizon="",
                              stage=""
                              )

    def test_load_model_data(self):
        """
        Test that data are loaded with no errors
        :return:
        """
        add_components_and_load_data(prereq_modules=IMPORTED_PREREQ_MODULES,
                                     module_to_test=MODULE_BEING_TESTED,
                                     test_data_dir=TEST_DATA_DIRECTORY,
                                     horizon="",
                                     stage=""
                                     )

    def test_data_loaded_correctly(self):
        """
        Test that the data loaded are as expected
        :return:
        """
        m, data = add_components_and_load_data(
            prereq_modules=IMPORTED_PREREQ_MODULES,
            module_to_test=MODULE_BEING_TESTED,
            test_data_dir=TEST_DATA_DIRECTORY,
            horizon="",
            stage=""
        )
        instance = m.create_instance(data)

        # Set: SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS
        expected_periods = [("Tx1", 2020), ("Tx1", 2030)]
        actual_periods = [
            (tx, p) for (tx, p)
            in instance.SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS
            ]
        self.assertListEqual(expected_periods, actual_periods)

        # Param: specified_tx_min_mw
        expected_min = OrderedDict(sorted({
            ("Tx1", 2020): -10, ("Tx1", 2030): -10
                                          }.items()
                                          )
                                   )
        actual_min = OrderedDict(sorted({
            (tx, p): instance.specified_tx_min_mw[tx, p] for (tx, p)
            in instance.SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS
                                        }.items()
                                        )
                                 )
        self.assertDictEqual(expected_min, actual_min)

        # Param: specified_tx_max_mw
        expected_max = OrderedDict(sorted({
            ("Tx1", 2020): 10, ("Tx1", 2030): 10
                                          }.items()
                                          )
                                   )
        actual_max = OrderedDict(sorted({
            (tx, p): instance.specified_tx_max_mw[tx, p] for (tx, p)
            in instance.SPECIFIED_TRANSMISSION_LINE_OPERATIONAL_PERIODS
                                        }.items()
                                        )
                                 )
        self.assertDictEqual(expected_max, actual_max)