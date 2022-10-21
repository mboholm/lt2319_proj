# -*- coding: utf-8 -*-

import json

#import requests # MB

from flask import Flask, request
from jinja2 import Environment

app = Flask(__name__)
environment = Environment()


def jsonfilter(value):
    return json.dumps(value)


environment.filters["json"] = jsonfilter


def validator_response(is_valid):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "is_valid": {{is_valid|json}}
      }
    }
    """)
    payload = response_template.render(is_valid=is_valid)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response


########################

filtered_dogs = set()
phase = None
descr_id = 1
comp_id  = 1
most_id  = 1
least_id = 1

db_MODE="local"
#db_MODE="API"

########################

if db_MODE == "local":
    with open("db_combined_n177.json", "r") as json_file:
        DOGS = json.load(json_file)


@app.route("/select_dog", methods=['POST'])
def select_dog():
    """ Selecting dogs for incremental search.
    """

    global phase
    global filtered_dogs

    try:
        payload = request.get_json()

        trainability_dict = payload["request"]["parameters"]["pf_trainability"]
        shedding_dict = payload["request"]["parameters"]["pf_shedding"]
        energy_dict = payload["request"]["parameters"]["pf_energy"]
        barking_dict = payload["request"]["parameters"]["pf_barking"]
        protectiveness_dict = payload["request"]["parameters"]["pf_protectiveness"]

        trainability_score = trainability_dict["value"] if trainability_dict else None
        shedding_score = shedding_dict["value"] if shedding_dict else None
        energy_score = energy_dict["value"] if energy_dict else None
        barking_score = barking_dict["value"] if barking_dict else None
        protectiveness_score = protectiveness_dict["value"] if protectiveness_dict else None

        scores = [("trainability", trainability_score), ("shedding", shedding_score), ("energy", energy_score), ("barking", barking_score), ("protectiveness", protectiveness_score)]
        build_up = [feature for feature, score in scores if score != None]
        
        if len(build_up) > 0:
            phase = build_up [-1]

        dogs = filter_dogs(scores)

        filtered_dogs = dogs

        print(">>> Selected Dog", "PHASE:", phase)
        print("$", dogs)

        result = []
        for dog in sorted(list(dogs)):
            value = create_value(dog)
            result.append({"value": value, "sort": "dog", "grammar_entry": dog})

        return selected_dog_response(result)
    except BaseException as exception:
        return error_response(message=str(exception))

def selected_dog_response(results):
    print(">>> Selected Dog Response")
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "result": [
        {% for result in results %}
          {
            "value": {{result.value|json}},
            "confidence": 1.0,
            "grammar_entry": {{result.grammar_entry|json}}
          }{{"," if not loop.last}}
        {% endfor %}
        ]
      }
    }
    """)
    payload = response_template.render(results=results)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response

def create_value(ds): 
    """ Cleanes a string to serve as value """

    # ds=dog string
    ds = ds.replace(" ", "_")
    ds = ds.replace("-", "_")
    ds = ds.replace("(", "")
    ds = ds.replace(")", "")
    ds = ds.replace("’", "")
    ds = ds.replace("é", "e")
    ds = ds.lower()
    #ds = ds.capitalize()
    return ds

def interpretation(value, mode="graded_bipolar", preferred=None):
    """ Takes a preference score for a feature (answer from the user) and returns an interpretation of that score
        with regard to how the score should be interpreted for including dogs from the database.

        Four modes:
        graded_bipolar
        acceptable_level (requires preferred = True, or preferred = False)
        strict
        importance
    """

    translation = {word:no for word, no in zip(["zero", "one", "two", "three", "four", "five"], [0,1,2,3,4,5])}

    value = translation[value]

    if mode=="graded_bipolar":
    # Graded bipolar question: to what degree should your dog (be) F?
        if value >= 3:
            interpret = list(range(value, 6))
        if value <= 2:
            interpret = list(range(0, value+1))

    if mode=="acceptable_level":
        if preferred:
            # On a scale from zero to five, how trainable must your dog be?
            interpret = list(range(value, 6))
        else:
            # On a scale from zero to five, to what degree can your dog shed?
            interpret = list(range(0, value+1))

    if mode=="strict":
        interpret = [value]

    if mode=="importance":
        # (On a scale from 0 to 5) To what extent is F important for you?
        interpret = list(range(value, 6))

    return interpret

def filter_dogs(scores):
    """ Takes a set of scores for a set of features and returns the dogs that satisfy those 
        scores (given some interpretation of the scores)
    """

    scores = [(feat, score) for feat, score in scores if score != None]

    if scores == []:
        #return set([dog["name"] for dog in DOGS])
        return go_lden_retriever()

    else:
        hits=set()
        for i, (feature, score) in enumerate(scores):
            score_meaning = interpretation(score)
            if i == 0:
                #hits.update([dog["name"] for dog in DOGS if dog[feature] in score_meaning])
                hits.update(go_lden_retriever(feature2dog=feature, multiple_conditions=score_meaning))

            else:
                #new_dogs = [dog["name"] for dog in DOGS if dog[feature] in score_meaning]
                new_dogs = go_lden_retriever(feature2dog=feature, multiple_conditions=score_meaning)
                hits = hits.intersection(new_dogs)
        
        return hits


def go_lden_retriever(dog2feature="name", name=None, feature2dog=None, multiple_conditions=None, database=db_MODE):
    """ GO to (Local) Database ENtry RETRIEVER
        Returns from the database a list of: 1. dog entries (dict/json), 2. dog names, OR 3. their score on some feature 

        database = "local"  Uses local database
        database = "API"    Uses API

        param dog2feature   Default "name". Set to some (other) feature F to get score for F of dog named by param name; 
                            set accordingly, go_lden_retriever will return a list with a single element (the score).
        param name          Default None. Set param name to the name of the dog you want from the database. 
        param feature2dog   Default None.           
    """


    if database == "local":
        if multiple_conditions != None: # gets the dog names (list) of dogs having a value on param feature2dog that is in param multiple_conditions 
            print("GT1")
            dogs_in_the_yard = [dog["name"] for dog in DOGS if dog[feature2dog] in multiple_conditions] 

        if dog2feature == None: # gets the dict/json for the dog named by param name (single element of list) 
            (print("GT2"))
            dogs_in_the_yard = [dog for dog in DOGS if dog["name"] == name] 

        if name == None and feature2dog==None: # gets all dog names in the database; NOT POSSIBLE FOR API
            print("GT3")
            dogs_in_the_yard = [dog["name"] for dog in DOGS]

        if dog2feature != None and name != None: # gets the score for a feature defined by param dog2feature of a dog named by param name
            print("GT4")
            dogs_in_the_yard = [dog[dog2feature] for dog in DOGS if dog["name"] == name]

    return dogs_in_the_yard


@app.route("/suggest_dog", methods=['POST'])
def suggest_dog():
    print(">>> Suggest Dog Action")
    try:
        # Presently, does not do anything more tahn being activated
        return successful_action_response()
    except BaseException as exception:
        return error_response(message=str(exception))


def successful_action_response():
    print(">>> Successful Action Response")
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0"
      }
    }
    """)
    payload = response_template.render()
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response

def query_response(value, grammar_entry):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": {{value|json}},
            "confidence": 1.0,
            "grammar_entry": {{grammar_entry|json}}
          }
        ]
      }
    }
    """)
    payload = response_template.render(value=value, grammar_entry=grammar_entry)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response

@app.route("/dog_describer", methods=['POST'])
def dog_describer():
    global descr_id

    try:
        payload = request.get_json()
        my_dog = payload["request"]["parameters"]["what_dog_to_describe"]["grammar_entry"]
        #data_entry = [dog for dog in DOGS if dog["name"] == my_dog][0]
        data_entry = go_lden_retriever(dog2feature=None, name=my_dog, feature2dog="name")[0]
        content = json2content(data_entry)
        c_value = "description_"+str(descr_id)
        descr_id += 1

        return query_response(c_value, content)
    except BaseException as exception:
        return error_response(message=str(exception)) 

#core_features = ["trainability", "shedding", "energy", "barking", "protectiveness", "good_with_children"]

def json2content(json):
    """ Takes a dict/json for a dog and returns a decription of that dog. 
    """

    # Template:
    # Rottweiler is a dog which is easy to tain. It sheds to some extent. It is high in energy and barks quite alot. It is very protective. It is OK with children
    # {name} is a dog which is {value_train} train. It sheds {value_shed}. It is {value_enery} in energy and barks {value}. It is {value_potect} protective. It is {} with children. 

    tr_scale = ["very hard to", "hard to", "quite hard", "easy", "quite easy", "very easy"]
    sh_ba_scale = ["almost nothing", "very litte", "little", "to some extent", "much", "very much"]
    en_scale = ["very low", "low", "quite low", "quite high", "high", "very high"]
    pr_scale = ["very much not", "quite not", "somewhat not", "somewhat", "quite", "very"]
    go_scale = ["extremly bad", "very bad", "bad", "good", "very good", "extremly good"]

    content = f"{json['name']} is a dog which is {tr_scale[int(json['trainability'])]} to train. It sheds {sh_ba_scale[int(json['shedding'])]}. It is {en_scale[int(json['energy'])]} in energy and barks {sh_ba_scale[int(json['barking'])]}. It is {pr_scale[int(json['protectiveness'])]} protective. It is {go_scale[int(json['good_with_children'])]} with children"

    return content

@app.route("/dog_comparator", methods=['POST'])
def dog_comparator():
    """ For comparing dogs.
    """
    global comp_id

    try:
        payload = request.get_json()
        target = payload["request"]["parameters"]["target_dog"]["grammar_entry"]
        compare_with = payload["request"]["parameters"]["compare_with"]["grammar_entry"]
        feature = payload["request"]["parameters"]["feature_of_comparison"]["value"]
        #feature = feature.replace("comp_", "")

        compare_str = get_comparison(target, compare_with, feature)

        c_value = "comparison_"+str(comp_id)
        comp_id += 1

        return query_response(c_value, compare_str)
    except BaseException as exception:
        return error_response(message=str(exception)) 

def get_comparison(target, compare_with, feature):
    """ BUilds a comparison-utterance.
    """

    #trg_value = int([dog[feature] for dog in DOGS if dog["name"] == target][0])
    #lm_value  = int([dog[feature] for dog in DOGS if dog["name"] == compare_with][0])
    trg_value = int(go_lden_retriever(dog2feature=feature, name=target, feature2dog="name")[0])
    lm_value  = int(go_lden_retriever(dog2feature=feature, name=compare_with, feature2dog="name")[0])

    if trg_value-lm_value == 0:
        evaluation = "zero"
    else:
        if trg_value>lm_value:
            evaluation = "pos"
        else:
            evaluation = "neg"

    semantics = {
    "trainability": {
        "pos": "is easier to train than",
        "neg": "is harder to train than",
        "zero": "is as easy to train as",
        }, 
    "shedding": {
        "pos": "sheds more than",
        "neg": "sheds less than",
        "zero": "sheds as much as",
        },  
    "energy": {
        "pos": "has more energy than",
        "neg": "has less energy than",
        "zero": "has as much energy as",
        }, 
    "barking": {
        "pos": "barks more than",
        "neg": "barks less than",
        "zero": "barks as much as",
        },  
    "protectiveness": {
        "pos": "is more protective than",
        "neg": "is less protective than",
        "zero": "is as protective as",
        },  
    "good_with_children": {
        "pos": "is better with children than",
        "neg": "is worse with children than",
        "zero": "is as good with children as",
        }
    }

    comparison = f"{target} {semantics[feature][evaluation]} {compare_with}"

    return comparison

@app.route("/most_dog_finder", methods=['POST'])
def most_dog_finder():
    """ For telling which dog, **among the remaining ones**, that has the highest value of some feature.  
    """
    global most_id

    try:
        payload = request.get_json()
        feature = payload["request"]["parameters"]["feature_of_most"]["value"]
        most = get_top(feature, "most") # a list
        most_str = say_top(most, feature, "most")
        c_value = "most_dog_"+str(most_id)
        most_id += 1

        return query_response(c_value, most_str)
    except BaseException as exception:
        return error_response(message=str(exception))


@app.route("/least_dog_finder", methods=['POST'])
def least_dog_finder():
    """ For telling which dog, **among the remaining ones**, that has the lowest value of some feature.  
    """
    global least_id

    try:
        payload = request.get_json()
        feature = payload["request"]["parameters"]["feature_of_least"]["value"]
        least = get_top(feature, "least")
        least_str = say_top(least, feature, "least")
        c_value = "least_dog_"+str(least_id)
        least_id += 1

        return query_response(c_value, least_str)
    except BaseException as exception:
        return error_response(message=str(exception))


def get_top(feature, mode, R_set = None):
    """ Gets the dog(s) with the highest/lowest value of some feature.

    param mode     If "most", finds dog(s) with the highest value
                   If "least", finds dog(s) with the lowest value 

    NOTE: the function considers only the R_set (filtered_dogs), not all dogs in the database (DOGS or API). 
    """
    
    print("¥", "FOR DEBUGGING -- Length 'filtered_dogs':", len(filtered_dogs))

    R_set = list(filtered_dogs)

    first_dog = R_set[0]
    top_dog = set()
    top_dog.add(first_dog)

    top_value = [int(x) for x in go_lden_retriever(dog2feature=feature, name=first_dog, feature2dog="name")][0]
    for f_dog in R_set[1:]:
        dog_json = go_lden_retriever(dog2feature=None, name=f_dog, feature2dog="name")[0]
        value = int(dog_json[feature])
        if value == top_value:
            top_dog.add(dog_json["name"])

        if mode == "most":
            if value > top_value:
                top_dog = set()
                top_dog.add(dog_json["name"])
                top_value = value
        if mode == "least":
            if value < top_value:
                top_dog = set()
                top_dog.add(dog_json["name"])
                top_value = value                              

    top_dog = list(top_dog)
    return top_dog

def say_top(top, feature, pol):
    """ Builds an utterance for the top dog(s) found.
    """

    template = {
    "trainability": "The ___ trainable dog* & ", 
    "shedding": "The dog* that shed? the ___ & ",
    "energy": "The dog* with ___ energy & ",
    "barking": "The dog* that bark? the ___ & ",  
    "protectiveness": "The ___ protective dog* & ",  
    "good_with_children": "The dog* that & ___ good with children & "
    }

    sent = template[feature]
    if len(top) > 1: #plural
        sent = sent.replace("*", "s")
        sent = sent.replace("&", "are")
        sent = sent.replace("?", "")
    else:
        sent = sent.replace("*", "")
        sent = sent.replace("&", "is")
        sent = sent.replace("?", "s")

    sent = sent.replace("___", pol)

    sent = sent + ", ".join(top)

    return sent






# @app.route("/give_dog_list", methods=['POST'])
# def give_dog_list(max_len=4):
#     try:
#         #payload = request.get_json()

#         GE_as_str = ", ".join(list(filtered_dogs)[:max_len])
#         VL_as_str = "_".join([create_value(dog) for dog in filtered_dogs][:max_len])

#         return query_response(VL_as_str, GE_as_str)
#     except BaseException as exception:
#         return error_response(message=str(exception))    





# def error_response(message):
#     response_template = environment.from_string("""
#     {
#       "status": "error",
#       "message": {{message|json}},
#       "data": {
#         "version": "1.0"
#       }
#     }
#     """)
#     payload = response_template.render(message=message)
#     response = app.response_class(
#         response=payload,
#         status=200,
#         mimetype='application/json'
#     )
#     return response


# def query_response(value, grammar_entry):
#     response_template = environment.from_string("""
#     {
#       "status": "success",
#       "data": {
#         "version": "1.1",
#         "result": [
#           {
#             "value": {{value|json}},
#             "confidence": 1.0,
#             "grammar_entry": {{grammar_entry|json}}
#           }
#         ]
#       }
#     }
#     """)
#     payload = response_template.render(value=value, grammar_entry=grammar_entry)
#     response = app.response_class(
#         response=payload,
#         status=200,
#         mimetype='application/json'
#     )
#     return response


# def multiple_query_response(results):
#     response_template = environment.from_string("""
#     {
#       "status": "success",
#       "data": {
#         "version": "1.0",
#         "result": [
#         {% for result in results %}
#           {
#             "value": {{result.value|json}},
#             "confidence": 1.0,
#             "grammar_entry": {{result.grammar_entry|json}}
#           }{{"," if not loop.last}}
#         {% endfor %}
#         ]
#       }
#     }
#      """)
#     payload = response_template.render(results=results)
#     response = app.response_class(
#         response=payload,
#         status=200,
#         mimetype='application/json'
#     )
#     return response

# @app.route("/dummy_query_response", methods=['POST'])
# def dummy_query_response():
#     response_template = environment.from_string("""
#     {
#       "status": "success",
#       "data": {
#         "version": "1.1",
#         "result": [
#           {
#             "value": "dummy",
#             "confidence": 1.0,
#             "grammar_entry": null
#           }
#         ]
#       }
#     }
#      """)
#     payload = response_template.render()
#     response = app.response_class(
#         response=payload,
#         status=200,
#         mimetype='application/json'
#     )
#     return response


# @app.route("/action_success_response", methods=['POST'])
# def action_success_response():
#     response_template = environment.from_string("""
#    {
#      "status": "success",
#      "data": {
#        "version": "1.1"
#      }
#    }
#    """)
#     payload = response_template.render()
#     response = app.response_class(
#         response=payload,
#         status=200,
#         mimetype='application/json'
#     )
#     return response