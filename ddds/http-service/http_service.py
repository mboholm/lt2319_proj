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


def error_response(message):
    response_template = environment.from_string("""
    {
      "status": "error",
      "message": {{message|json}},
      "data": {
        "version": "1.0"
      }
    }
    """)
    payload = response_template.render(message=message)
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


def multiple_query_response(results):
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


@app.route("/dummy_query_response", methods=['POST'])
def dummy_query_response():
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": "dummy",
            "confidence": 1.0,
            "grammar_entry": null
          }
        ]
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


@app.route("/action_success_response", methods=['POST'])
def action_success_response():
    response_template = environment.from_string("""
   {
     "status": "success",
     "data": {
       "version": "1.1"
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

# MB ...

with open("db_combined_n177.json", "r") as json_file:
    DOGS = json.load(json_file)

@app.route("/selected_dog", methods=['POST'])
def selected_contact():
    print(">>> Selected Dog")
    try:
        payload = request.get_json()

        print("$ Facts:")
        facts = payload["context"]["facts"]
        for k in facts:
            print(k+":", facts[k])
        print("$ Request:")
        req = payload["request"]
        for k in req:
            print(k+":", req[k])

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

        dogs = filter_dogs(scores)

        #contacts = available_contacts(first_name, last_name)
        #print("$ Contacts:", contacts)
        result = []
        for dog in dogs:
            #full_name = full_name_of(contact_id)
            contact_id = 9999999999 # MB ???
            result.append({"value": contact_id, "sort": "dog", "grammar_entry": dog})
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
    #print(payload)
    response = app.response_class(
        response=payload,
        status=200,
        mimetype='application/json'
    )
    return response

def interpretation(value):
    if value >= 3:
        interpret = list(range(value, 6))
    if value <= 2:
        interpret = list(range(0, value+1))
    return interpret

def filter_dogs(scores, db=DOGS):
    scores = [(feat, score) for feat, score in scores if score != None]
    for i, (feature, score) in enumerate(scores):
        score_meaning = interpretation(score)
        if i == 0:
            hits = set()
            hits.update([dog["name"] for dog in db if dog[feature] in score_meaning])

        else:
            new_dogs = [dog["name"] for dog in db if dog[feature] in score_meaning]
            hits = hits.intersection(new_dogs)
    
    return hits
