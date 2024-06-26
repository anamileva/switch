# Copyright (c) 2015-2024 The Switch Authors. All rights reserved.
# Licensed under the Apache License, Version 2.0, which is in the LICENSE file.
import os, shutil, argparse, glob
import pandas as pd
import switch_model.upgrade
from pyomo.environ import DataPortal

upgrades_from = "2.0.5"
upgrades_to = "2.0.6"

replace_modules = {
    # modules to be replaced in the module list
    # old_module: [new_module1, new_module2, ...],
    "switch_model.hawaii.psip_2016_12": ["switch_model.hawaii.heco_outlook_2020_06"],
    "switch_model.hawaii.kalaeloa": ["switch_model.hawaii.oahu_plants"],
}

module_messages = {
    # description of significant changes to particular modules other than
    # moving/renaming
    # old_module: message
}


def upgrade_input_dir(inputs_dir):
    """
    Upgrade the input directory.
    """
    # Write a new version text file. We do this early so that if the update
    # fails and then the user tries again it won't try to upgrade a second time,
    # overwriting their backup.
    switch_model.upgrade._write_input_version(inputs_dir, upgrades_to)

    # rename modules and report changes
    update_modules(inputs_dir)

    # rename_file('fuel_cost.csv', 'fuel_cost_per_period.csv')
    # rename_column('fuel_cost_per_period.csv', 'fuel_cost', 'period_fuel_cost')


def rename_file(old_name, new_name, optional_file=True):
    old_path = os.path.join(inputs_dir, old_name)
    new_path = os.path.join(inputs_dir, new_name)
    if optional_file and not os.path.isfile(old_path):
        return
    shutil.move(old_path, new_path)


def rename_column(file_name, old_col_name, new_col_name, optional_file=True):
    path = os.path.join(inputs_dir, file_name)
    if optional_file and not os.path.isfile(path):
        return
    df = pd.read_csv(path, na_values=["."], sep=",")  # for 2.0.5+
    df.rename(columns={old_col_name: new_col_name}, inplace=True)
    df.to_csv(path, sep=",", na_rep=".", index=False)


def item_list(items):
    """Generate normal-text version of list of items, with commas and "and" as needed."""
    return " and ".join(", ".join(items).rsplit(", ", 1))


def update_modules(inputs_dir):
    """Rename modules in the module list if needed (list is sought in
    standard locations) and return list of alerts for user."""

    modules_path = os.path.join(inputs_dir, "modules.txt")
    if not os.path.isfile(modules_path):
        modules_path = os.path.join(inputs_dir, "..", "modules.txt")
    if not os.path.isfile(modules_path):
        modules_path = "modules.txt"
    if not os.path.isfile(modules_path):
        raise RuntimeError(
            "Unable to find modules or modules.txt file for input directory '{}'. "
            "This file should be located in the input directory, its parent, or "
            "the current working directory.".format(inputs_dir)
        )
    modules_path = os.path.normpath(modules_path)  # tidy up for display later

    # Upgrade module listings
    # Each line of the original file is either a module identifier or a comment
    with open(modules_path) as f:
        old_module_list = [line.strip() for line in f.read().splitlines()]

    # rename modules as needed
    new_module_list = []
    for module in old_module_list:
        try:
            new_modules = replace_modules[module]
            switch_model.upgrade.print_verbose(
                "Module {old} has been replaced by {new} in {file}.".format(
                    old=module, new=item_list(new_modules), file=modules_path
                )
            )
        except KeyError:
            new_modules = [module]
        new_module_list.extend(new_modules)

    if new_module_list != old_module_list:
        # write new modules list
        with open(modules_path, "w") as f:
            for module in new_module_list:
                f.write(module + "\n")

    # report any significant changes in the previously active modules
    for module in old_module_list:
        try:
            switch_model.upgrade.print_verbose(
                "ATTENTION: {}".format(module_messages[module])
            )
        except KeyError:
            pass

