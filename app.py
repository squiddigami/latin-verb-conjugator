import csv
import sys
import time
import json

import pandas as pd
from tabulate import tabulate

from lexeme.lexeme import Lexeme
from uri.uri import update_list



def main():
    update = input("Update list of verbs? WARNING: do not update frequently; likely not necessary. [Yes or Y, enter any other key for No]: ").strip().lower()
    if update in ["y", "yes"]:
        update_list()
    while True:
        lexeme = Lexeme(get_verb())
        get_action(lexeme)


def get_verb():
    #reads uri.csv and creates a dict with keys=lemmas and values=uris
    with open("uri/uri.csv") as file:
        reader = csv.DictReader(file)
        uri = {row["lemma"]: row["uri"] for row in reader}
        while True:
            verb = input("\nWhat verb do you want to conjugate?\nEnter the first principal part (if regular, the -o form): ").strip().lower()
            try:
                return uri[verb]
            except KeyError:
                print("verb not found in database!")
                pass

def get_action(lex):
    action_table = [
        ["Action:", "Enter this:"],
        ["Generate conjugation chart", "C"],
        ["Conjugate specific form", "F"],
        ["Display principal parts", "P"],
        ["Choose new verb", "N"],
        ["Exit program", "X"]
    ]
    while True:
        action = input(f"\nWhat action do you want to take?\n{tabulate(action_table, tablefmt="grid", headers="firstrow")}\nAction: ").strip().lower()
        match action:
            case "c":
                print(chart(lex))
                time.sleep(2)
            case "f":
                print(form(lex))
                time.sleep(2)
            case "p":
                print(lex.principal())
                time.sleep(2)
            case "n":
                break
            case "x":
                sys.exit("Program ended")


def chart(lex):
    with open("chart.json") as file:
        chart = json.load(file)

        finites = get_finites(chart, lex)
        nonfinites = get_nonfinites(chart, lex)
        verbalnouns = get_verbalnouns(chart, lex)


        return(f"\n{str(lex).capitalize()} Conjugation Chart\n\n{finites}\n\n{nonfinites}\n\n{verbalnouns}\n")

def get_finites(chart, lex):
    #create the column and row labels for the finites (indicative, subjunctive, imperative)
    finite_columns = pd.MultiIndex.from_frame(pd.DataFrame(chart["finite_column_names"], columns=["finite forms", ""]))
    finite_indexes = pd.MultiIndex.from_frame(pd.DataFrame(chart["finite_index_names"], columns=["", "", ""]))

    #create indicative and subjunctive forms and the imperatives forms and combine
    indsub = [[lex.conjugate(f"200{person}{number}{tense}{voice}{mood}0") for number in (1, 2) for person in (1, 2, 3)]
        for mood in (1, 2) for voice in (1, 2)
        for tense in range(1, 7) if not ((mood == 2 and tense == 3) or (mood == 2 and tense == 6))]

    imperative = [[lex.conjugate(f"200{person}{number}{tense}{voice}30") for number in (1, 2) for person in (1, 2, 3)]
                for voice in (1, 2) for tense in (1, 3)]

    finite_forms = indsub + imperative

    #create a DataFrame using the smaller DataFrames as columns and indexes and the lists of lists as data
    return pd.DataFrame(finite_forms, columns=finite_columns, index=finite_indexes)


def get_nonfinites(chart, lex):
    #create the column and row labels for the finite nonfinites (infinitives, participles)
    nonfinite_columns = pd.MultiIndex.from_frame(pd.DataFrame(chart["nonfinite_column_names"], columns=["non-finite forms", ""]))
    nonfinite_indexes = pd.MultiIndex.from_frame(pd.DataFrame(chart["nonfinite_index_names"], columns=[""]))

    #create the infinitive and participle forms, then combine
    infinitive = [lex.conjugate(f"20000{tense}{voice}40") for voice in (1, 2) for tense in (1, 3, 4)]
    participle = [lex.conjugate(f"22101{tense}{voice}50") for voice in (1, 2) for tense in (1, 3, 4)]

    nonfinite_forms = [infinitive, participle]

    #create a DataFrame using the smaller DataFrames as columns and indexes and the lists of lists as data
    return pd.DataFrame(nonfinite_forms, columns=nonfinite_columns, index=nonfinite_indexes)


def get_verbalnouns(chart, lex):
    #create the column and row labels for the verbal nouns (gerund and supine)
    verbalnoun_columns = pd.MultiIndex.from_frame(pd.DataFrame(chart["verbalnoun_column_names"], columns=["verbal nouns"]))
    verbalnoun_indexes = pd.MultiIndex.from_frame(pd.DataFrame(chart["verbalnoun_index_names"], columns=[""]))

    #create the gerund and supine forms
    verbalnoun_forms = [[lex.conjugate(f"22{case}0100{mood}0") for case in (2, 3, 4, 5)] for mood in (6, 7)]

    #create a DataFrame using the smaller DataFrames as columns and indexes and the lists of lists as data
    return pd.DataFrame(verbalnoun_forms, columns=verbalnoun_columns, index=verbalnoun_indexes)


def form(lex):
    with open("input_convert.json") as file:
        inputs = json.load(file)
        print("Conjugate a Specific Morpheme:\n")
        mood = get_paradigm(inputs, "mood") #since logic deviates based on mood, the mood must be established first
        conditions = inputs["conditions"][mood]
        errors = inputs["errors"]

        #creates a dict comprehension where
        #for every paradigm in a given mood's necessary conditions
        #   key=paradigm name (voice, tense, etc); value=user input for that paradigm (active, present, etc)
        paradigms = {para: get_valid_input(inputs, para, valid_options, errors[mood]) for para, valid_options in conditions.items()}

        #for most forms, the get_valid_input and get_paradigm functions are sufficient
        #these are called by the "default" key with the value of the lambda function paradigm, which checks the above dict
        subcode_conditions = {
            "gender": "2" if mood in ["5", "6", "7"] else "0",
            #if the form is a participle or gerund, the gender is masculine, else no gender (corrects API irregularities)
            "number": "1" if mood in ["5", "6", "7"] else paradigms.get("number", "0"),
            #if the form is a participle or gerund, the number is singular, else the number is user-inputted (corrects API irregularities)
            "default": lambda paradigm: paradigms.get(paradigm, "0")
        }

        #generates the 6 variable digits inside the 9-digit morphological code
        subcode = ""
        for paradigm in ["gender", "case", "person", "number", "tense", "voice"]:
            subcode += subcode_conditions.get(paradigm, subcode_conditions["default"](paradigm))

        #generates the English-language morphological description of a given form
        description = ""
        for paradigm in ["case", "person", "number", "tense", "voice"]:
            if paradigm in conditions:
                description += f"{inputs["nonmood_paradigm_names"][paradigm][paradigms[paradigm]]} "

        #returns [description] of [lexeme (1st principal part)]: [morpheme (generated form)]
        return f"{description}{inputs["mood_names"][mood]} of {lex}: {lex.conjugate(f"2{subcode}{mood}0")}"

#runs until a valid input is retrieved
def get_valid_input(inputs, para: str, valid_options=None, error_message="invalid input!"):
    while True:
        value = get_paradigm(inputs, para)
        #valid_options can either be a boolean True or a list of valid values
        #"valid" in this case refers to extant within the scope of the paradigm
        #for instance, subjunctive verbs only having four valid tenses
        if valid_options == True or value in valid_options:
            return value
        print(error_message)

def get_paradigm(inputs, para: str):
    while True:
        try:
            #helper function for get_valid_input that allows any input as long as it exists as a morphological descriptor
            #does not differentiate based on previous conditions/inputs
            para_val = inputs[para][input(inputs[para]["prompt"]).strip().lower()]
        except KeyError:
            pass
        else:
            return para_val


if __name__ == "__main__":
    main()
