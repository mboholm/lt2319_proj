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

# MB ...

#run = 0
filtered_dogs = set()
phase = None

with open("db_combined_n177.json", "r") as json_file:
    DOGS = json.load(json_file)

@app.route("/select_dog", methods=['POST'])
def select_dog():
    #global run
    global phase
    global filtered_dogs

    try:
        payload = request.get_json()
        #print("$ PAYLOAD", payload)

        #print("$ Facts:")
        #facts = payload["context"]["facts"]
        #for k in facts:
        #    print(k+":", facts[k])
        #print("$ Request:")
        #req = payload["request"]
        #for k in req:
        #    print(k+":", req[k])

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
        #if phase == None:
        #    dogs = set(["Katten Gustaf", "Mamma mu"])
        #run += 1

        print(">>> Selected Dog", "PHASE:", phase)
        print("$", dogs)

        #contacts = available_contacts(first_name, last_name)
        #print("$ Contacts:", contacts)
        result = []
        for dog in sorted(list(dogs)):
            #full_name = full_name_of(contact_id)
            #contact_id = 999 # MB ???
            value = create_value(dog)
            result.append({"value": value, "sort": "dog", "grammar_entry": dog})
        #print("$", result)
        #print("$")
        #print(selected_contact_response(result))
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
    #print("$ Payload, response:", payload)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response

def create_value(ds): # ds=dog string
    ds = ds.replace(" ", "_")
    ds = ds.replace("-", "_")
    ds = ds.replace("(", "")
    ds = ds.replace(")", "")
    ds = ds.replace("’", "")
    ds = ds.replace("é", "e")
    ds = ds.lower()
    return ds

def interpretation(value):

    translation = {word:no for word, no in zip(["zero", "one", "two", "three", "four", "five"], [0,1,2,3,4,5])}

    value = translation[value]


    if value >= 3:
        interpret = list(range(value, 6))
    if value <= 2:
        interpret = list(range(0, value+1))
    return interpret

def filter_dogs(scores, db=DOGS):

	# OBS! Should return ALL dogs in zero phase. There is code for such a funcion in "resolve" directory (version) of project

    hits=set()
    scores = [(feat, score) for feat, score in scores if score != None]
    for i, (feature, score) in enumerate(scores):
        score_meaning = interpretation(score)
        if i == 0:
            hits.update([dog["name"] for dog in db if dog[feature] in score_meaning])

        else:
            new_dogs = [dog["name"] for dog in db if dog[feature] in score_meaning]
            hits = hits.intersection(new_dogs)
    
    return hits

@app.route("/dummy_action", methods=['POST'])
def dummy_action():
    print(">>> Dummy Action")
    try:
        #payload = request.get_json()
        #selected_contact = payload["request"]["parameters"]["selected_contact"]["value"]
        #number = PHONE_NUMBERS.get(selected_contact)
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

@app.route("/dog_describer", methods=['POST'])
def dog_describer():

	try:
		payload = request.get_json()
		my_dog = payload["request"]["parameters"]["what_dog_to_describe"]["grammar_entry"]
		data_entry = [dog for dog in DOGS if dog["name"] == my_dog][0]
		content = json2content(data_entry)
		#c_value = create_value(content)
		c_value = my_dog+"_description"

		return query_response(c_value, content)
	except BaseException as exception:
		return error_response(message=str(exception)) 


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

#core_features = ["trainability", "shedding", "energy", "barking", "protectiveness", "good_with_children"]

def json2content(json):
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

	try:
		payload = request.get_json()
		target = payload["request"]["parameters"]["target_dog"]["grammar_entry"]
		compare_with = payload["request"]["parameters"]["compare_with"]["grammar_entry"]
		feature = payload["request"]["parameters"]["comp_feature"]["value"]
		feature = feature.replace("comp_", "")

		compare_str = get_comparison(target, compare_with, feature)

		#c_value = create_value(content)
		c_value = f"{target}_{compare_with}_comparison"

		return query_response(c_value, compare_str)
	except BaseException as exception:
		return error_response(message=str(exception)) 

def get_comparison(target, compare_with, feature):

	trg_value = int([dog[feature] for dog in DOGS if dog["name"] == target])
	lm_value  = int([dog[feature] for dog in DOGS if dog["name"] == compare_with])

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

	comparison = f"{target_dog} {semantics[feature][evaluation]} {compare_with}"

	return comparison


# @app.route("/give_dog_list", methods=['POST'])
# def give_dog_list(max_len=4):
#     try:
#         #payload = request.get_json()

#         GE_as_str = ", ".join(list(filtered_dogs)[:max_len])
#         VL_as_str = "_".join([create_value(dog) for dog in filtered_dogs][:max_len])

#         return query_response(VL_as_str, GE_as_str)
#     except BaseException as exception:
#         return error_response(message=str(exception))    



