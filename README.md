# LT2319 Project

## Report
Report, data and presentation can be found in `report/`.

## Training RASA
Training data was generated using `lookup-entries`:

```tala generate rasa proj_fido eng --lookup-entries dog:dogs.csv > ../rasa_nlu/training-data-eng.yml```

In an attempt to improve the systems performance on MOP comparison, user answers related to comparison in the training data were edited: `predicate.None` was specified as `predicate.target_dog` and `predicate.compare_with`. This did not seem to improve performance however.

## Local and API mode
In the present implementation, it is possible to run FiDo in one of two database modes:
1. *local mode*, which uses the local database (`db_combined_n177.json`) for incremental search and where user answers to system preference probing questions are interpreted along the lines of (numeric) bipolar gradeables, i.e. covering a range of values
2. *API mode*, which uses the web API for incremental search and where user answers to system preference probing questions are interpreted strictly.

The two modes can be set by a global parameter of the `http_service.py` file: for *API mode* set `db_mode_is_API` to `True`; for *local mode* set `db_mode_is_API` to `False`. 

## Interaction tests
Iteraction tests presuppose *local mode* (`db_mode_is_API = False`).

## Unresolved issues
* Tests for comparisons does not work `http://pipline/interact` mode.
* There is not proper transition to the action defined by `on_too_many_hits_action`
