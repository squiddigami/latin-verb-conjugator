import json
import re

import requests

#constants
FIRST_PP_CODE = "200111110"
PRES_INF_CODE = "200001140"
PERF_ACT_CODE = "200114110"
SUPINE_CODE = "224010070"

class Lexeme:
    def __init__(self, uri: str):
        """
        Initializes Lexeme object using the verb's URI (unique identifier)
        with instance variables:
            conj: (conjugation; 1, 2, 3 or 4),
            deponent: (verbs that cannot have passive forms; True or False),
            pp2, pp3, pp4: (stems of the necessary principal parts, "-" if they do not exist)
            pp1: (standard "dictionary" entry; the 1st person singular present active indicative)
        """
        r = requests.get(f"https://latinwordnet.exeter.ac.uk/api/lemmas/?uri={uri}").json()
        morpho = r["results"][0]["morpho"]
        if match := re.search(r"^v1spi(a|d)--([1-4])(-|i)$", morpho):
            self.conj: str = str(match.group(2))
            self.deponent: bool = True if match.group(1) == "d" else False
        else:
            raise ValueError("Unrecognized morphology!")
        self.pp1 = r["results"][0]["lemma"]
        self.pp2, self.pp3, self.pp4 = r["results"][0]["principal_parts"].split()

        """
        Retrieves all irregular forms, then places them into an instance dict where
        key=morpheme (converted from the API morphological syntax into this project's 9-digit syntax): value=form
        """
        if temp := (r["results"][0]["irregular_forms"]):
            irregular_forms: tuple = temp.split()
            with open("lexeme/api_convert.json") as file:
                convert = json.load(file)
                self.irregulars = {self.encode(convert, keyform.split("=")[0]): keyform.split("=")[1] for keyform in irregular_forms}
        else:
            self.irregulars = {}



    def __str__(self):
        return self.conjugate(FIRST_PP_CODE) #returns the 1st principal part or "lemma" form


    def principal(self):
        """
        dictionary entry for a verb includes the 'ego' (regular -o) form, as well as these two or three parts, if they exist
        """
        if self.deponent:
            return f"{self.conjugate(FIRST_PP_CODE)} (present infinitive {self.conjugate(PRES_INF_CODE)}, perfect active {self.conjugate(PERF_ACT_CODE)}"
        return f"{self.conjugate(FIRST_PP_CODE)} (present infinitive {self.conjugate(PRES_INF_CODE)}, perfect active {self.conjugate(PERF_ACT_CODE)}, supine {self.conjugate(SUPINE_CODE)})"


    def encode(self, convert, morpho: str):
        """
        Mainly for the conversion, storage, and recall of irregular forms.
        Converts the LatinWordNet API's 10-character alphanumeric code into a 9-character numeric code.
        Each digit is specified in both formats using brackets [] in the key below.
        """
        #LatinWordNet API:[POS][PERSON/DEGREE][NUMBER][TENSE][MOOD][VOICE][GENDER][CASE][DECLENSION/CONJUGATION][i-VARIANCE]
        #This project:[POS][GENDER][CASE][PERSON][NUMBER][TENSE][VOICE][MOOD][DEGREE]
        if match := re.search(r"^([nvarp])([123pcs-])([sp-])([pif-])([ismnpgdu-])([apd-])([fmn-])([ngdabv-])([12345-][i-])$", morpho):
            pos = convert[0][match.group(1)]
            gender = convert[6][match.group(7)]
            # most morphological differences between forms occur on the basis of mood
            # both this project and the API categorize participles, gerunds, as being "moods" of verbs
            if match.group(5) == "g":
                case = "2"
                gender = "2"
            else:
                case = convert[7][match.group(8)]
            if match.group(5) in ["g", "d"]: #unlike this project, the API differentiates between gerunds in the genitive case and other-case gerunds
                person, number, tense, voice = "0", "1", "0", "0"
            else:
                tense = convert[3][match.group(4)]
                voice = convert[5][match.group(6)]
                person = "0"
                number = convert[2][match.group(3)]
                if match.group(5) == "p":
                    number = "1"
                elif match.group(5) == "n":
                    number = "0"
                elif match.group(5) == "m":
                    person = "2"
                else:
                    if not match.group(5) == "m":
                        person = convert[1][match.group(2)] if match.group(1) == "v" else "0"
            mood = convert[4][match.group(5)]
            degree = convert[9][match.group(2)] if match.group(1) == "a" else "0"
            return pos + gender + case + person + number + tense + voice + mood + degree
        else:
            raise ValueError("invalid morphology!")


    def conjugate(self, code: str):
        """
        conjugates a given form by determining the stem and ending
        first checks for irregularity, in which case the irregular form is returned.

        dissects the 9-digit morphological code, extracting the case, tense, voice, and mood
        combines person and number into pernum for ease of use when finding the ending

        the "ending" is considered to be everything outside of the stem
        while manual Latin conjugation would use patterns in stem vowels, the Conjugator considers the vowel to be part of the ending

        for example:

        Latin grammar: 3rd-SG-IMP-ACT-IND   (am)    (a)         (bat)
                                            (stem)  (stem vowel)(ending)

        Conjugator: code=200312110  (am)    (abat)
                                    (stem)  (ending)

        If the ending is None or the stem does not exist (API indicating there are no existing forms that use it),
        conjugate returns "-"
        """
        if code in list(self.irregulars):
            return self.irregulars[code]
        if code[0] == "2": #checks that code is a verb
            if code == FIRST_PP_CODE:
                return self.pp1 #returns the 1st person singular present active indicative (lemma form)
            case, tense, voice, mood = code[2], code[5], code[6], code[7]
            person_number = {"00": "0", "01": "0", "02": "0", "11": "1", "21": "2", "31": "3", "12": "4", "22": "5", "32": "6"}
            pernum = person_number[code[3:5]]
            #with a default value of pp2, determines which principal part should serve as the stem
            stem = self.stem(tense, voice, mood)
            #determines the ending
            ending = self.ending(self.conj, mood, voice, tense, pernum, case)
            return stem + ending if ending and not stem == "-" else "-"
        else:
            raise ValueError("cannot conjugate non-verbs!")

    def stem(self, tense, voice, mood):
        """
        determines the principal part that serves as the stem for a given form.
        in a Latin dictionary, the conjugated forms of the principal parts are given, while the API provides only the bare stems. for example:

        Dictionary: amo, amare, amaui, amatus (functionality replaced by the lexeme.principal function)
        API: amo,  am, amau, amat

        the 'default' stem is given as the 2ndpp
        """
        stem = self.pp2
        if mood in ["1", "2"] and int(tense) > 3:
            stem = self.pp3 if voice == "1" else self.pp4
        if mood == "4":
            if not tense == "1":
                stem = self.pp4
                if tense == "4" and voice == "1":
                    stem = self.pp3
        if mood == "5":
            if tense == "3" and voice == "1" or tense == "4":
                stem = self.pp4
        if mood == "7":
            stem = self.pp4
        return stem


    def ending(self, conj, mood, voice, tense, pernum, case):
        """
        determines the ending (including stem vowel) for a given form.
        the "endings" file is sorted by (dicts of) conjugation pattern, mood, voice, tense, and lists of endings of six pernums for finite forms
        """
        with open("lexeme/regular_endings.json") as file:
            endings = json.load(file)
            voice_option = "2" if self.deponent else voice
            #the API morphology codes three voices: active, passive, and deponent
            #the Conjugator uses self.deponent for deponency and conjugates all deponent verbs as active, but using passive endings
            match mood:
                case "1" | "2" | "3":
                    return endings[conj][mood][voice_option][tense][int(pernum) - 1]
                case "4" | "5":
                    return endings[conj][mood][voice_option][tense] #nonfinites are not conjugated by pernum
                case "6" | "7":
                    return endings[conj][mood][case] #verbalnouns are only conjugated by case

