-------------------------------------------------------------------------------
Switch 2.0.9
-------------------------------------------------------------------------------
This release includes several new features, most notably implementation of
pumped storage hydro. It also renames one output file and changes the balancing
rules for hydro systems when there are multiple timeseries in the same
investment period.

The updates are summarized below. For more details, see the
[git commit log](https://github.com/switch-model/switch/blob/master/updates209.txt).

**Changes that may affect existing models and results**

- The `switch_model.generators.extensions.hydro_system` module now tracks hydro
  reservoir levels separately for each timeseries instead of linking them together
  across the whole period.
  - Previously the hydro_system module tracked levels of reservoirs across all
    the timepoints in a period, as if each timeseries was linked to the one
    after it. This was an error, and in models with multiple timeseries with
    different weights, Switch could retain water during low-weight timeseries,
    then release it during high-weight timeseries, effectively producing free
    energy.
  - The new approach matches the general principle in Switch that each
    timeseries is independent and it must be possible to repeat each timeseries
    many times in a row if necessary. Although this is more correct than the
    previous approach, it is also more conservative: hydro networks must now
    reach the same level (or a prespecified level) at the start and end of each
    timeseries, instead of the start and end of each period.
  - Users should now set `res_initial_vol` and `res_final_vol` for each
    timeseries in `reservoir_ts_data.csv` instead of setting `initial_res_vol`
    and `final_res_vol` for each period in reservoirs.csv. The standard upgrade
    script will automatically rename and move these columns if needed. It will
    also interpolate between the previous full-period reservoir volumes to set
    the reservoir volumes at the start and end of each timeseries.
  - For models with a single, long timeseries for each period (the most common
    use case for this module), this change won't affect results. However, for
    models with multiple timeseries in each period with different weights, this
    update may change the model results.
  - The `res_initial_vol` and `res_final_vol` inputs are now optional. If
    `res_initial_vol` is set but not `res_final_vol`, Switch will set the final
    level equal to the initial level. If neither is set, Switch will choose an
    optimal initial volume for each timeseries and also return to that level at
    the end of the timeseries. (For most models, it is best not to set
    `res_final_vol`, so Switch will return the reservoir to the starting level.
    This makes it possible to have an arbitrary number of repetitions of each
    timeseries.)
- The `gen_project_annual_summary.csv` output file has been renamed to
  `dispatch_gen_annual_summary.csv`. The new name is more consistent with the
  other dispatch summaries, such as `dispatch_zonal_annual_summary.csv` or
  `dispatch_annual_summary.csv`.

**New features**

- The `switch_model.generators.extensions.hydro_system` module can now model
  pumped storage hydro systems.
  - To use this feature you must also add
    `switch_model.generators.extensions.storage` somewhere above
    `switch_model.generators.extensions.hydro_system` in `modules.txt`.
  - Hydro generators can be designated as reversible (able to do pumped hydro
    storage) by setting `gen_storage_efficiency` in `gen_info.csv` to a numeric
    value (generally 0.5 - 1.0).
  - When generators are identified as reversible, water can be pumped from the
    node below the generator to the one above, with the specified round-trip
    efficiency. The nodes above and below the generator should have reservoir
    data in reservoirs.csv to indicate the amount of storage available. If you
    currently have a sink node below the dam, you may need to add a reservoir
    with a fixed size for the lower pool, then connect the sink node downstream
    of that.
  - The storage module now defines a new set called ALL_STORAGE_GENS, which will
    rarely be used. This is the union of pumped-storage hydro generators and
    standard storage generators (usually batteries), which are still listed in
    STORAGE_GENS.
- If you have installed pulp (easy to do via pip or conda), you can use the
  cbc solver bundled with it by specifying `--solver pulp_cbc` when running
  Switch. CBC is a fairly fast solver and can be difficult to install on
  Windows, so this may be a convenient way to use it.
- The `switch_model.balancing.diagnose_infeasibility` module now relaxes
  bounds on variables in addition to constraints. These will show up in the
  reporting as `VariableName_bounds`, and can be turned back on via
  `--no-relax VariableName_bounds`. This can give a clearer picture of which
  constraints and/or bounds are interacting to make a model infeasible.
- The `switch_model.hawaii.ev` module now balances EV charging by date instead
  of timeseries, if the tp_date column is provided in timepoints.csv. This
  forces full charging every day when using multi-day timeseries, rather than
  allowing EVs to delay charging multiple days, possibly exceeding their storage
  capacity.


-------------------------------------------------------------------------------
Switch 2.0.8
-------------------------------------------------------------------------------
This release includes several new features, bug fixes and compatibility
improvements. It should have minimal effect on results from existing models
other than some improvements and bug fixes in the electricity_cost.csv output
file.

The updates are summarized below. For more details, see the [git commit log](https://github.com/switch-model/switch/blob/master/updates208.txt).

**Changes that may affect existing models and results**

- In Switch 2.0.7 and earlier, the `SystemCostPerPeriod_Real` column in
  `outputs/electricity_cost.csv` was a (mislabeled) annual cost but
  `SystemDemand_MWh` was a total for the whole period. The
  `EnergyCostReal_per_MWh` was calculated as the ratio of these, making it too
  low by a factor equal to the number of years in the period. Starting with
  Switch 2.0.8, we report both costs and quantities on a per-year basis
  (`SystemCostPerYear_Real` and `SystemDemandPerYear_MWh`), and the error in
  `EnergyCostReal_per_MWh` has been corrected.
- Pyomo dependencies have been updated to to versions 6.0.0-6.7.1 (the current
  latest version).
  - If you are using Pyomo 5.7, you will need to update to at least 6.0. This
    change was made to avoid complex dependencies on `pyutilib`.
- Made `--no-save-solution` the default behavior, so the large `results.pickle`
  file will not be written unless requested. Users who have previously set this
  flag should now remove it. Users who need the `results.pickle` file (sometimes
  useful for reloading and inspecting a previous solution, with
  `--reload-prior-solution`) should add the new `--save-solution-file` flag.
- Fixed a bug in `hawaii.save_results` that erroneously grouped all generators
  into the same zone in `capacity_used_by_technology.csv` and
  `production_by_technology.csv`
- `build_gen.csv` will now contain a `.` instead of `0.0` for periods when
  generators can't be built
- Fixed a bug that previously crashed Switch when using the gurobi or cplex
  solver without any suffixes.
- Fixed a bug that previously dropped users into a debugging terminal when
  an infeasible model was encountered.
- Fixed a bug that crashed `hawaii.save_results` if the model did not use the
  `transmission.local_td` module
- Fixed bugs in `balancing.diagnose_infeasibility` that would crash when
  analyzing singleton constraints or constraints formulated as (lower_bound,
  expression, upper_bound).

**New features**

- Added a hydrogen production module. This produces a fuel (by default called
  "Hydrogen") that can be used by any generator.
  - There is assumed to be one set of hydrogen production equipment per load
    zone, and one possible cost for each component, regardless of location.
    Hydrogen production equipment, once built, continues to the end of the study
    (similar to transmission infrastructure).
  - This feature can be turned on by adding
    `switch_model.energy_sources.hydrogen.production` to your module list and
    adding parameters for each production component to `inputs/hydrogen.csv`.
  - Components include
    - electrolyzer (cost per MW power rating and per kg produced, kg of hydrogen
      produced per MWh of power consumed, lifespan),
    - liquefier/refrigerator (capital and fixed costs per kg/hr of capacity,
      variable cost per kg produced, MWh of electricity required per kg
      liquefied, lifespan) and
    - liquid storage tank (cost per kg of capacity, lifespan).
  - The module is designed to represent storage of liquefied hydrogen in
    NASA-type above ground tanks, but it can be used to represent compressed
    hydrogen storage instead by setting the liquefier energy requirement and
    cost to zero, so compressed hydrogen can be stored as if there were no cost
    for liquefication.
  - This module assumes production within the day can be used without a tank,
    but any surplus or shortfall for the day must be moved to a tank, and the
    tank must be large enough to hold all the withdrawals for the whole year.
    This formulation will work regardless of the actual order of removals, so it
    avoids the need to link sequences of days. However, if tank costs are high,
    it may be overly conservative.
  - If using this module with multi-day timeseries, you should fill in date
    markers in the `td_date` column of `inputs/timepoints.csv` (see below).
  - An example implementation can be found in
    [`examples/hydrogen`](https://github.com/switch-model/switch/tree/master/examples/hydrogen)
  - Future work could extend this to allow different costs for different
    locaitons and vintages, retire components at end of life, allow multiple
    production facilities per zone, better represent compressed (not liquefied)
    storage and consider the sequence of dates in the year when setting the tank
    size.
- Added option to perform optimal early retirement and suspension for generators
  - Setting `gen_can_retire_early` or `gen_can_suspend` flags in `gen_info.csv`
    to `True` or `1` now allows generators to be retired permanently or
    temporarily suspended before they reach their maximum age. In both cases,
    the amount of capacity of a particular vintage that is offline in a given
    period will be shown by the new `SuspendGen` variable. These both default to
    `False`/`0`, and `gen_can_suspend` will take precedence (temporary
    suspension will be allowed) if both are set to `True`/`1`.
  - The `GenCapacity` expression now reports only capacity that has not been
    suspended, and a new column in `gen_cap.csv`, `SuspendGen_total`, shows the
    total capacity in each generation project that is suspended/inactive in each
    period.
  - Suspended generators avoid fixed O&M costs, but must continue to pay
    capital recovery (amortized capital costs) as normal.
- Added generator retrofit capability via a new
  `switch_model.generators.extensions.retrofit` module. This makes it possible
  to define retrofit generators that supersede existing generators.
  - Retrofit options are implemented by defining a new generation project that
    can replace a previously built one (i.e., it performs like the original
    generator plus the retrofit) and adding columns to `gen_retrofits.csv`
    showing all allowed combinations of base projects that can be replaced by
    retrofit projects. In each row, `base_gen_project` shows the name of the
    original (base) project and `retrofit_gen_project` shows the name of a
    retrofit project that can replace it.
  - Retrofit projects will only be built if the base project has also been built
    in the same or an earlier period. When a base project is retrofitted, the
    base project is suspended (via SuspendGen) and the retrofit version is built
    and operated instead. In addition, retrofit projects are automatically
    suspended at the end of life of the base project. (To enable these
    behaviors, `gen_can_retire_early` or `gen_can_suspend` must be set to `True`
    or `1` in `gen_info.csv` for both the base project and the retrofit
    version.)
  - Because of this framing, retrofitted projects will have capital expenditure
    equal to the capital recovery for the base project plus capital recovery for
    the retrofit project. So gen_overnight_cost for the retrofit project should be
    set equal to the cost of the retrofit work, not the combined project. However,
    fixed and variable O&M will no longer be collected for the base project, so
    O&M cost inputs for the retrofit project should be the ones that apply for the
    total retrofitted project.
  - Capital recovery for the retrofitted project will be amortized over the
    remaining life of the base project that it replaces, which may cause faster
    capital recovery than would otherwise be expected for these assets.
  - A working example is available in
    [`examples/retrofits`](https://github.com/switch-model/switch/tree/master/examples/retrofits)
- Added `tp_date` parameter to identify which date each timepoint falls on. This is
  used by modules that enforce constraints between hours of the same date (e.g.,
  hydrogen production or intra-day demand response). It defaults to be the same as
  the timeseries (the previous behavior), which works fine if each timeseries is
  one day long. But if models use multi-day timeseries, they should specify a
  code for the corresponding date for each timepoint in the `tp_date` column of
  `inputs/timepoints.csv`.
- Added `--retire {early, mid, late}` command-line flag. This flag controls
  whether to retire projects at the start of the period when they reach
  end-of-life ('early') (i.e., only run if they survive to the end of the
  period), or retire them if they survive past the middle of the period ('mid'),
  or extend operation to the end of the period when they reach end-of-life
  ('late'). Late is the default and matches previous behavior by Switch. Early
  and mid match some other models' behavior. Note that `early` requires that a
  project's life extends not just up to the end of the period, but beyond it
  into the next period, or else it will retire at the start of the period.
- Added a new, optional `gen_storage_energy_fixed_om` parameter to
  `gen_build_costs.csv` to indicate fixed O&M costs for the energy component of
  storage projects. Note that no column is needed for variable O&M for the
  energy component, because this is already covered by `gen_variable_om` for the
  power component.
- Switch now allows negative values for fixed and variable O&M for generators.
  These can be useful for representing subsidies that produce net-negative
  carrying or operating costs.
- Switch is now compatible with `appsi_highs` and other [appsi_*](https://pyomo.readthedocs.io/en/stable/library_reference/appsi/appsi.solvers.html) solvers.
  - HiGHS is one of the fastest open-source solvers we have found for
    medium-sized models.
    - To use HiGHS, first install Switch following the standard
      instructions, then install HiGHS itself into your environment via either a
      binary download or `conda install highs`, then install the HiGHS-Python
      bindings into your environment via `pip install highspy`, then run with
      `--solver appsi_highs`. (It is also possible to download an AMPL-compatible
      version of HiGHS from https://portal.ampl.com/user/ampl/download/highs,
      place it in your path and then set --solver highs.)
    - `appsi_highs` requires Pyomo 6.4.3 or later. The ampl version of HiGHS can
      be used with any version of Pyomo.
  - CBC is another of the fastest open-source solvers we have found for
    medium-sized models. It can be installed on Linux and macOS via
    `conda install coincbc`, then use `--solver cbc` or `--solver appsi_cbc`.
    It currently has [limited availability](https://stackoverflow.com/questions/58868054/how-to-install-coincbc-using-conda-in-windows) for Windows.


-------------------------------------------------------------------------------
Switch 2.0.7
-------------------------------------------------------------------------------
This release includes a large number of new features and compatibility and
stability improvements. It should have minimal effect on results from existing
models. Huge thanks are due to Josiah Johnston for most of these changes and to
new contributors Desmond Zhong, Brad Venner and Martin Staadecker.

The updates are summarized below. For more details, see the [git commit log](https://github.com/switch-model/switch/blob/master/updates207.txt).

**Changes that may affect existing models and results**

- Changed Pyomo dependencies to versions 5.7.0-6.4.2. This has a few implications:
  - All previous users of Switch will need to upgrade their Pyomo installation,
    since Switch 2.0.6 was only compatible up through Pyomo 5.6.8. The upgrade
    to 5.7.0 is needed to get around a bug in Pyomo 5.6.8 and earlier that would
    incorrectly treat invalid optional data as missing data. If you have invalid
    data in optional columns, you may now receive error messages instead of it
    being silently ignored.
  - Note that Pyomo versions before 5.7.3 don't work with CPLEX version 12.10 or
    later (see https://github.com/Pyomo/pyomo/pull/1792). If using a recent
    version of CPLEX, you should ensure that you also use version 5.7.3 or later
    of Pyomo.
  - If you have older models or custom modules, you should make the following
    changes to ensure compatibility with more recent versions of Pyomo:
    - assign `dimen` values for all Pyomo Sets.
    - initialize Pyomo Sets using ordered containers, not Python sets.
      (`switch_model.utilities.unique_list` can be useful for this)
    - explicitly specify a `within` domain for all Pyomo Sets and Params
    - don't use `+inf`, `-inf`, `+infinity`, `-infinity` or `nan` in input files
      (in some cases, one of these may be the default value for a parameter, so
      the input value can be specified as `.` instead)
- The `generation_projects_info.csv` input file has been renamed to
  `gen_info.csv`. The new name is more consistent with other file names, which
  generally start with "gen_", and may be easier to remember and view in editor
  tabs. Switch 2.0.7 will offer to automatically update this file (and
  others) the first time it is run with an version 2.0.6 inputs directory.
- The `gen_predetermined_cap` column has been renamed to
  `build_gen_predetermined` in `gen_build_predetermined.csv`. This is more
  consistent with the new `build_gen_energy_predetermined` column, and the use
  of 'build' in the names makes it clearer that these columns show the amount of
  new capacity built in each year, not the total amount of capacity in place
  that year.
- The `distribution_loss_rate` column has been moved from the `trans_params.csv`
  input file to `load_zones.csv` and renamed `local_td_loss_rate`. This makes
  the name more accurate and allows it to be varied between load_zones.
- The `gen_multiple_fuels.dat` input file has been replaced with
  `gen_multiple_fuels.csv`. Users should update their model setup scripts to
  create the new file. The .csv file should have two columns: `GENERATION_PROJECT`
  and `fuel`. It should have one row for each allowed fuel for each multi-fuel
  generator.
- The `dispatch-wide.csv` output file has been renamed `dispatch_wide.csv`.
- An extra "m" has been removed from the names of the
  `cumulative_capacity_by_tech_periods.csv` and
  `cumulative_transmission_by_path_periods.csv` output files produced by the
  `reporting.basic_exports` module.
- Switch now implements a check for bidirectional transmission lines being
  specified in input files, so the implementation matches documentation.
- Switch no longer uses the `auto_select`/`autoselect` argument in calls to
  `switch_data.load_aug`. Columns are always auto-selected now unless a 'select'
  argument is passed. You should remove this argument from any custom modules
  you use.
- Curtailable storage charging is now included as a form of reserves in the
  `spinning_reserves` module, matching the `spinning_reserves_advanced` module.
  This may change the results from models that use storage with the
  `spinning_reserve` module.
- `balancing.demand_response_simple` now defaults to providing `'spinning'`
  reserves if a reserve module is loaded, otherwise providing no reserves.
- `balancing.demand_response.iterative` now works with `spinning_reserves_advanced`,
  including a `--demand-response-reserve-types` flag. It also now reports final
  results in a file with no iteration number at the end.
- The internal `zone_rfm` component has been renamed to `zone_fuel_rfm` to make
  it more clear that it identifies the rfm for each zone-fuel combination.
- The output file `gen_cap.csv` now reports storage energy capacity (MWh) in
  place during each study period, in addition to power capacity (MW) in place.
  It also includes the capital recovery for the storage MWh in the reported
  annual capital recovery (previously omitted). The `GenCapitalCosts` column in
  this file has been renamed to `GenCapitalRecovery` to clarify that it is the
  amortized capital repayment that occurs for each project during each year, and
  distinguish it from capital outlay that occurs when the project is first built
  and is later recovered over time via the GenCapitalRecovery.
- The new `gen_build.csv` output file shows the amount of power (MW) and storage
  (MWh) capacity _added_ during each period. This also shows the total capital
  outlay needed for these additions. Switch uses capital outlay to calculate
  annual capital recovery requirements, then includes capital recovery each
  period in the system cost that it optimizes. Switch doesn't use the capital
  outlay for anything except calculating the annual capital recovery required.
  However, capital outlay may be of interest to planners.
- Switch no longer produces the  `storage_builds.csv` output file, since the
  information from this file is now shown in `gen_build.csv` and `gen_cap.csv`.
- When using the `balancing.unserved_load` module and the
  `transmission.local_td` module, unserved load is now applied at the
  distribution node instead of the zone backbone node. This clarifies
  supply-demand balance and avoids some cases where reducing the load at the
  backbone may not be enough to avoid infeasibility. This may slightly change
  the unserved load and  total cost reported in those models, due to avoiding
  the need for local transmission and distribution to meet the unserved portion
  of load.
- Switch now gives a more compact description of the location of errors when
  they occur. If you would like to see the full Python traceback (the former
  behavior), use the new `--full-traceback` flag.
- The `balancing.planning_reserves` module previously assigned a default
  capacity value for solar plants that could not exceed 1, even in timepoints
  when the capacity factor was greater than 1.0. We now allow values greater
  than 1 when calculating the default value for this parameter.
- The `--sorted-output` flag is applied more universally. This ensures most
  outputs will be sorted when requested, including `dispatch.csv`,
  `dispatch_wide.csv` (columns), `gen_cap.csv`,
  `gen_project_annual_summary.csv`, `load_balance.csv`,
  `local_td_energy_balance.csv`, `local_td_energy_balance_wide.csv` and
  `transmission.csv`. Previous versions did not use this flag so universally, so
  you may find the order of some outputs changes when you upgrade.


**New features**

- new `--log-level` flag can be set to `error`, `warning`, `info` or `debug` to
  receive varying amounts of information about the model run. `--verbose` is a
  now a synonym for `--log-level info`, and `--quiet` is equivalent to
  `--log-level warning` (default). Definitions of the levels are as follows:
    - `error`: may be used to give extra explanation when an exception is raised
    - `warning`: warn user about behavior that is most likely wrong but not enough
      to cause an exception (default output level, so users will see this for
      most models)
    - `info`: high-level progress log; used to follow progress of the model
      without seeing every detail
    - `debug`: detailed diagnostic data (e.g., recommend improved practices for
      input data files even if the current files are officially acceptable)
- A new module `balancing.diagnose_infeasibility` can be used to help diagnose
  infeasible models, generally caused by inconsistent input data. This module
  relaxes all constraints, making any model feasible, then seeks to minimize all
  constraint violations, then reports which constraints are violated. Users can
  use a `--no-relax CONSTRAINT1 [CONSTRAINT2 ...]` argument to selectively turn
  some constraints back on, to identify combinations of constraints that cannot
  be enforced simultaneously. This is similar to CPLEX's irreducibly infeasible
  set (IIS) feature, but faster and simpler and works with all solvers.
- Energy balance of the local T&D node is now exported to
  `local_td_energy_balance.csv` and `local_td_energy_balance_wide.csv`.
- Updated simple_hydro to model spillways, allowing river flow to exceed the
  capacity of the generator & reservoir.
- Storage decisions are now shown in dispatch-related output files if the
  storage module is included.
- Expanded export from the generator dispatch module to simplify analysis.
  `gen_project_annual_summary.csv` shows energy production, emissions, capacity
  online, capital and O&M costs, levelized cost of energy, capacity factor and
  storage utilization for each generation project for each study year.
  `dispatch_zonal_annual_summary.csv` shows the same information per technology
  per load zone. `dispatch_annual_summary.csv` shows the same information per
  technology, aggregated across the entire region.
- Implemented predetermined energy capacity for storage, a parallel to
  predetermined power capacity. This is specified in MWh in a new
  `build_gen_energy_predetermined` column in `gen_build_predetermined.csv`. It
  should be left blank (".") for non-storage projects, or you may omit the
  column if your model has no storage projects.
- Added new command-line option `--input-alias` or `--input-aliases`. This
  allows users to specify replacements for individual input files to use in the
  current run. e.g., `--input-alias fuel_cost.csv=fuel_cost_high.csv` would use
  the `fuel_cost_high.csv` file instead of `fuel_cost.csv` in the current run.
  This can be used with one or more substitutions and can be repeated:
  `--input-alias[es]` `file1.csv=file1.alternate.csv`
  `[file2.csv=file2.alternate.csv, ...]`. These are applied as a simple
  replacement on the filename, then added onto the directory specified with
  `--inputs-dir`. So usually the replacement will occur within the
  `--inputs-dir`, but users can specify `some_dir/file.csv` or
  `../some_other_dir/file.csv` in the alias to refer to files in other
  directories relative to the normal location of the file. Filename `none` will
  cause the file to be ignored.
- When using the `hawaii.ev` module, users can now split the EV fleet between
  different charging modes using the `--ev-timing` flag: `--ev-timing EV_TIMING
  [EV_TIMING ...]`. Each EV_TIMING entry consists of a mode and optionally a
  share, e.g., `--ev-timing bau` charges all vehicles in `bau` mode or
  `--ev-timing bau=0.32 optimal=0.68` splits the fleet between `bau` and
  `optimal` mode. Modes are `bau`=business-as-usual (upon arrival), `flat`=around
  the clock, or `optimal` (default). If modes are specified without shares
  assigned, they will receive equal fractions of the unallocated charging.
- It is now possible to put comments on the same line as data in `modules.txt`,
  `options.txt` and `scenarios.txt`. This can be done by placing a `#` followed
  by the comment at the end of the line.
- Zero-weight timeseries are now allowed. These are useful for modeling rare,
  worst-case days or including worse-than-worst (non-real) days as a form of
  planning reserves.
- It is now possible to assign different fuel costs for each timepoint by using
  `energy_sources.fuel_costs.simple_per_timepoint` instead of
  `energy_sources.fuel_costs.simple`. It is also possible to set prices on
  different timescales (e.g., per timeseries) by assigning the same price to all
  timepoints in that period. This file reads input file
  `fuel_cost_per_timepoint.csv`, which should have these columns:
  `fuel_cost_per_timepoint.csv` `load_zone`, `fuel`, `period`,
  `fuel_cost_per_timepoint`.
- The new `fuel_costs.markets_expansion` module allows capacity expansion of
  fuel markets. If using this module, you should add columns
  `rfm_supply_tier_fixed_cost` and `rfm_supply_tier_max_age` to the
  `fuel_supply_curves.csv` input file. These can be specified as `.` for tiers
  that are already available. For candidate tiers that may or may not be built,
  the `rfm_supply_tier_fixed_cost` specifies the fixed cost per MMBtu of fuel
  supply made _available_ by that tier (not necessarily used) and
  `rfm_supply_tier_max_age` specifies the life of the tier if it is activated.
  This module is useful for considering investments in infrastructure that will
  expand the availability of fuels, such as a liquified natural gas (LNG)
  terminal. By testing tiers with different lives (and therefore different costs
  per MMBtu of fuel made available), it is possible to assess questions such as
  whether early fuel infrastructure investment will crowd out later renewable
  deployment. If the power system being studied will block use of a fuel after a
  certain date, then `rfm_supply_tier_max_age` should end before that date, to
  ensure that stranded costs after the end of the study are not omitted from the
  study. To do this, it may be necessary to add side constraints to prevent use
  of long-lived tiers after certain dates. The `No_LNG_In_100_RPS` constraint in
  `switch_model.hawaii.lng_conversion` shows an example of this.
- The new `transmission.copperplate` module can be used to enable unlimited
  power transfer between zones at no cost.
- Switch now allows general-purpose models with no zonal power demand and no
  power system components. This can be useful, e.g., for studying gas networks
  independently from the electricity system.
- Progress in constructing model components is reported in 10% steps if
  `--log-level` is `info`. If `--log-level` is `debug`, these steps are shown
  along with timing to construct each individual component. Constructing model
  components is one of the lengthiest steps in Switch, so this gives more
  reassurance that something is happening.
- New command line option `--skip-generic-output` tells `switch_model.reporting`
  not to save data for each model variable after the plan is optimized. These
  files can also be excluded by omitting the `switch_model.reporting` module
  from your model, which will also prevent creation of `total_cost.txt` and
  `cost_components.csv`. Specifying `--no-post-solve` will prevent running the
  `post_solve` code in all the modules used in the model, and therefore prevent
  all output.
- Model configuration is now saved in `model_config.json` in outputs directory.
- The `demand_response.iterative` module now includes the iteration number in
  result filenames, which can be useful for monitoring progress of the solution.
- `existing_local_td` and `local_td_annual_cost_per_mw` are now optional
  (default 0) when using the `local_td module`. This is useful for models where
  existing local transmission and distribution capacity is unknown (Switch will
  automatically build enough) or where the cost of local T&D capacity is not
  important, e.g., if the user is only concerned about avoiding local T&D
  losses.
- Switch will now report dual values (shadow prices) for the carbon cap in
  `emissions.csv` even for models with integer or binary variables. Note that
  dual values are not defined in general for integer models, and for this reason
  many solvers do not provide them. However, it is common practice to solve
  once, then fix integer variables at their current level, then re-solve the now
  continuous model and obtain dual values for that (this is what the
  `--retrieve-cplex-mip-duals` flag does with the `cplex` solver, and some
  versions of the `cplexamp` solver do this automatically). In this case, the
  shadow price of carbon assumes none of the integer variables move from their
  optimized position (e.g., not turning on one more power plant or abandoning
  the plan to build a plant with a specific minimum size), which should be
  suitable for most applications.
- A solved model will be returned at the end of `switch_model.solve.main()` if
  the `return_model` and `return_instance` arguments are not specified. This can
  be useful for programmatic control of Switch.

**Other changes**

- Switch code has begun to use `m.logger.error()`, `m.logger.warning()`,
  `m.logger.info()` and `m.logger.debug()` for screen output, and this is
  recommended for custom user modules too.
- Changed plotting library from `ggplot` to `plotnine` for optional plots stored
  in `dispatch_annual_summary_fuel.pdf` and `dispatch_annual_summary_tech.pdf`
  (these plots will be generated automatically if you have `plotnine` installed
  in your Python environment)
- Numerous adjustments to improve performance, documentation, warning messages
  or stability. See [git commit
  log](https://github.com/switch-model/switch/blob/master/updates207.txt) for
  details.
- A bug was fixed in the `balancing.planning_reserves` module that may sometimes
  have caused Switch to crash.
- Updated planning reserves input documentation & reading to reflect that some
  parameters are optional and don't have to be specified in files.
- Fixed a bug with fuel unavailability when calculating fuel costs related to
  dispatch with the `fuel_costs.markets` module.
- Switch now uses `SwitchAbstractModel` and `SwitchConcreteModel` classes to
  encapsulate the features we add to the Pyomo base classes. (Mainly of interest
  to core developers.)
- Switch source code now uses the Black autoformatter. This should make the
  source code a little more readable, and is recommended for any contributions
  from users.

-------------------------------------------------------------------------------
Switch 2.0.6
-------------------------------------------------------------------------------
This release fixes a bug where the fixed costs of storage energy capacity (the
MWh part of storage) from all possible build years were mistakenly applied each
period, instead of only using the build years that are still in service in the
current period. This increased the apparent cost of storage by approximately
(study length) / (storage life). This bug was introduced in version 2.0.0b3 and
persisted through version 2.0.5, so results from earlier models will need to be
updated.

This will be the last version of Switch to work in Python 2. It requires at
least Python 2.7.12 and also works with Python 3.

-------------------------------------------------------------------------------
Switch 2.0.5
-------------------------------------------------------------------------------
This release standardizes all inputs and outputs as .csv files.

As usual, when  you first solve an older model, Switch will prompt to backup and
upgrade the  inputs directory. If you accept, it will convert the existing
tab-delimited *.tab files and most ampl-format *.dat files to comma-delimited
*.csv files. It is recommended that you update your model data preparation
scripts to create .csv files directly. Note that non-indexed parameters should
now be stored in .csv files with a header row listing the parameter names and a
single data row showing their values.

All multi-value outputs from Switch are also now in comma-delimited .csv files,
instead of a mix of .csv, .tab and .txt files. (total_cost.txt is unchanged)

This release also includes includes the following minor updates:

- Updated installation instructions
- Switch version number and website are now shown in the startup banner when
  running with --verbose flag; solve messages have also been improved slightly
- Some parsing errors for *.tab files have been fixed in the upgrade scripts;
  this may cause errors during the upgrade process for input files that use
  spaces instead of tabs and were previously upgraded by Switch, producing
  malformed files.
- Fixed several bugs in the documentation and execution of the stochastic
  examples that use the PySP module of the Pyomo package

-------------------------------------------------------------------------------
Switch 2.0.4
-------------------------------------------------------------------------------

This release introduces compatibility with Python 3. As of version 2.0.4, Switch
can now be run with either Python 2.7 or Python 3 (likely to work with 2.7.10+;
has been tested on 2.7.16 and 3.7.3).

This release will prompt to upgrade your model inputs directory, but the only
change it makes is to update switch_inputs_version.txt to 2.0.4.

This release includes the following updates:

- Code has been updated in many places to achieve Python 2/3
  cross-compatibility. Future contributors should ensure that their code is
  compatible with both Python 2 and 3 (e.g., use
  switch_model.utilities.iteritems(dict) instead of dict.iteritems(), be
  prepared for results from dict.keys(), dict.vars(), map(), range(), zip(),
  etc., to be either generators or lists, and use `from __future__ import
  division` whenever doing division).
- Installation instructions in INSTALL have been updated. We now recommend that
  users install dependencies using the conda command first, then install Switch
  using pip. This follows practices recommended in
  https://www.anaconda.com/using-pip-in-a-conda-environment/ and should minimize
  problems caused by incompatibilities between conda and pip.
- Output files (.csv, .tab, .tsv, and .txt) are now consistently written using
  the local system's line endings (LF on Mac or Linux, CRLF on Windows).
  Previously, most of these were written with only LF line endings on Windows.
- A bug was fixed in switch_model.transmission.local_td that prevented the
  carrying cost of Legacy local T&D capacity from being included in the
  objective function. As a result, users of this module will find that Switch
  now reports higher total costs than previously. However, this should not
  affect any of the decisions that Switch makes.
- To make switch_model.transmission.local_td module compatible with Python 3,
  "Legacy" was removed from the list of build years for local T&D capacity
  (Pyomo sorts index keys when solving the model, and Python 3 cannot sort lists
  that mix strings and numbers). Legacy capacity is now read directly from the
  existing_local_td[z] parameter when needed. This does not change the behavior
  of Switch, but "Legacy" rows are no longer written to the BuildLocalTD.tab
  output file. The LOCAL_TD_BLD_YRS set has also been removed. LOAD_ZONES *
  PERIODS can be used instead.
- A new indexed set, CURRENT_AND_PRIOR_PERIODS_FOR_PERIOD[p] has been added.
  This is useful for simple online capacity calculations for assets that cannot
  be retired during the study (e.g., AssetCapacity[p] = sum(BuildCapacity[v] for
  v in CURRENT_AND_PRIOR_PERIODS_FOR_PERIOD[p]))
- Code has been cleaned up a bit internally (e.g., removed trailing whitespace,
  changed "SWITCH" or "SWITCH-Pyomo" to "Switch")

-------------------------------------------------------------------------------
Switch 2.0.3
-------------------------------------------------------------------------------

- Users can now provide data in variable_capacity_factors.tab and
  hydro_timeseries.tab for times before projects are built or after they are
  retired without raising an error. However, the extra datapoints will be
  ignored.
- Various parts of the code have better formatting, documentation and
  performance.
- switch_model.hawaii.smooth_dispatch is now compatible with Pyomo 5.6 and
  later.
- A new '--exact' option in switch_model.hawaii.rps forces the system to
  exactly meet the RPS target and no more. This is useful for studying the cost
  of adopting various levels of renewable power, including levels below the
  least-cost system design (i.e., cases where low shares of renewable power
  cause higher system costs).
- A bug was fixed when calculating the cost of water spillage in
  switch_model.generators.extensions.hydro_system.
- Final reservoir level in switch_model.generators.extensions.hydro_system
  is now stored in a varaible called ReservoirFinalVol. The ReservoirSurplus
  variable has been eliminated.
- Bounds on a number of inputs have been relaxed to allow unusual or edge cases.
  In particular, a number of variables can now be zero instead of strictly
  positive. This allows zero costs, zero capacity limits, zero-based year
  counting, etc.
- The  gen_is_baseload parameter is now optional, with a default value of False
  (0).
- NEW_TRANS_BLD_YRS has been renamed to TRANS_BLD_YRS.
- setup.py now lists an optional dependency on rpy2<3.9 instead of rpy2, because
  later versions of rpy2 require Python 3, which Switch doesn't support yet.
  This only affects the iterative demand response module.
- A new GENS_BY_ENERGY_SOURCE set can be used to identify all the generators
  that use any energy source, either a fuel or a non-fuel energy source.
  GENS_BY_FUEL and GENS_BY_NON_FUEL_ENERGY_SOURCE also still exist.
- We have begun migrating toward using `initialize` instead of `rule` when
  initializing Pyomo components, and recommend that users do the same in their
  custom modules. This matches the current Pyomo API documentation. `rule` also
  works for now, but `initialize` should be more future proof.
- The discrete-build requirement is now enforced on generators with
  predetermined build quantities, in addition to optimized generators.
- The optional psycopg2 dependency has been changed to psycopg2-binary.
- The --debug option now uses the ipdb debugger if available; otherwise it falls
  back to pdb.

-------------------------------------------------------------------------------
Switch 2.0.2
-------------------------------------------------------------------------------

- General
    - Added --assign-current-version argument to `switch upgrade`. This is
      useful for updating version number in example directories to match
      current version of Switch, even if the data files don't need an upgrade.

- Hawaii regional package
    - Fixed bug in hawaii.rps that would crash `switch solve --help`.

-------------------------------------------------------------------------------
Switch 2.0.1
-------------------------------------------------------------------------------

- General
    - Switch is now compatible with Pyomo 5.6+ (in addition to earlier
      versions).
    - A new --no-post-solve option prevents all post-solve actions (e.g., saving
      variable results).
    - If the user specifies --reload-prior-solution, Switch now behaves as if it
      had just solved the model, i.e., after loading the solution, it runs post-
      solve code unless --no-post-solve is specified (useful for re-running
      reporting code), and it only drops to an interactive Python prompt if the
      user also specifies --interact.
    - A new --no-save-solution disables automatic solution-saving. This saves
      time and disk space for models that won't need to be reloaded later.
    - New --quiet and --no-stream-solver arguments cancel --verbose and
      --stream-solver.
    - A new "--save-expression[s] <name1> <name2> ..." argument can be used to
      save values for any Pyomo Expression object to a .tab file after the model
      is solved (similar to the automatic saving of variable values). This also
      works for Param objects.
    - The --include-module(s), --exclude-module(s), --save-expression(s),
      --suffix(es) and --scenario(s) flags can now be used repeatedly on the
      command line, in options.txt or in scenarios.txt. The include and exclude
      options will be applied in the order they are encountered, in options.txt,
      then scenarios.txt, then the command line.
    - A new --retrieve-cplex-mip-duals flag can be used to support retrieving
      duals for a MIP program from the cplex solver (users must also turn on the
      "duals") suffix. This flag patches the Pyomo-generated cplex command
      script to pass the "change problem fix" command to the solver and then
      solve a second time. This fixes integer variables at their final values,
      then re-solves to obtain duals. This flag is not needed with the cplexamp
      solver.
    - A new balancing.demand_response.iterative module has been added. This was
      formerly in the Hawaii regional package. This module performs iterative
      solutions with any convex demand system, based on a bid-response process.
    - New indexed sets have been added to allow efficient selection of groups of
      generators that use a particular technology, fuel or non-fuel energy
      source: GENS_BY_TECHNOLOGY, GENS_BY_FUEL, GENS_BY_NON_FUEL_ENERGY_SOURCE.
    - Generator capacity data is saved to gen_cap.tab instead of gen_cap.txt and
      rows are sorted if user specifies --sorted-output.
    - Even if a model has solver warnings, results will be reported and
      post-solve will be performed if a valid solution is available.
    - A more descriptive warning is given when switch_model.reporting finds an
      uninitialized variable.
    - A warning is given about potential errors parsing arguments in the form
      "--flag=value". Python's argument parsing module can make mistakes with
      these, so "--flag value" is a safer choice.
    - Switch now monkeypatches Pyomo to accelerate reloading prior solutions.
      Previously Pyomo 5.1.1 (and maybe others) took longer to load prior
      solutions than solving the model.
    - At startup, "switch solve-scenarios" will restart jobs that were
      previously interrupted after being started by the same worker (same
      --job-id argument or SWITCH_JOB_ID environment variable). Note that
      workers automatically pull scenarios from the scenario list file until
      there are none left to solve, and avoid solving scenarios that have been
      pulled by other workers. Each worker should be given a unique job ID, and
      this ID should be reused if the worker is terminated and restarted. The
      new behavior ensures that jobs are not abandoned if a worker is restarted.

- Upgrade scripts
    - The upgrade scripts now report changes in module behavior or renamed
      modules while upgrading an inputs directory. This only reports changes to
      modules used in the current model.
    - The hawaii.reserves module is automatically replaced by
      balancing.operating_reserves.areas and
      balancing.operating_reserves.spinning_reserves in the module  list.
    - The hawaii.demand_response module is replaced by
      balancing.demand_response.iterative and hawaii.r_demand_system is replaced
      by balancing.demand_response.iterative.r_demand_system in the module list.
    - "switch_mod" will not be changed to "switch_modelel" if a module file is
      upgraded from 2.0.0b1 to 2.0.0b2 twice.

- Hawaii regional package
    - The hawaii.reserves module has been deprecated and the
      hawaii.demand_response module has been moved (see upgrade scripts)
    - Switch now places limits on down-reserves from pumped-storage hydro.
    - A new --rps-prefer-dist-pv option for hawaii.rps will prevent construction
      of new large PV until 90% of distributed PV potential has been developed.
    - Limits on load-shifting between hours in hawaii.demand_response_simple
      have been formalized.
    - The Hawaii storage energy cost calculation has been fixed.
    - Total production by energy source is reported by hawaii.save_results,
      ad-hoc technologies are added to production_by_technology.tsv, and
      hourly dispatch is disaggregated by non-fuel technologies.
    - Bugs have been fixed in reserve calculation for EVs and in
      hawaii.smooth_dispatch and hawaii.scenario_data.
    - hawaii.smooth_dispatch minimizes total inter-hour change instead of square
      of levels. The old quadratic smoothing method has been moved to
      hawaii.smooth_dispatch.quadratic (slow and possibly buggy).
    - The must-run requirement in hawaii.kalaeloa is turned off when RPS or EV
      share is above 75% (can be overridden by --run-kalaeloa-even-with-high-rps)
    - Support for nominal-dollar fuel price forecasts has been dropped from
      hawaii.scenario_data
    - A new --no-hydrogen flag can be used to deactivate the hydrogen module.
    - The hawaii.ev_advanced module now calculates vehicle fleet emissions.

-------------------------------------------------------------------------------
Switch 2.0.0
-------------------------------------------------------------------------------

First public release of Switch 2. This uses a similar framework to Switch 1,
but with numerous improvements. The most significant are:

- Written in Python instead of AMPL language
- Modular approach, so components can be easily added or removed from model
- Modeling of unit commitment and part load heat rates (optional)
- Generalization of sample timeseries to have arbitrary length instead of single
  days
- Standardized reporting, e.g., automatic export of all variable values
