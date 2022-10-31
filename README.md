# LT2319 Project

## Report
Report, data and presentation can be found in `report`.

## Training RASA
Training data was generated using `lookup-entries`:

```tala generate rasa proj_fido eng --lookup-entries dog:dogs.csv > ../rasa_nlu/training-data-eng.yml```

Before training, user answers related to comparison were edited: `predicate.None` was specified as `predicate.target_dog` and `predicate.compare_with`. 

