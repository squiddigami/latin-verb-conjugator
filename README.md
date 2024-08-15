# Latin Verb Conjugator
#### Video Demo: [https://www.youtube.com/watch?v=_FMUC9SOHac](https://www.youtube.com/watch?v=_FMUC9SOHac)
## Description

This program conjugates Latin verbs. It uses the Latin WordNet API, an ongoing project of the University of Exeter, which has a database of over seventy-five thousand Latin words, including over ten thousand verbs. The Latin Verb Conjugator therefore has the ability to conjugate any of these verbs, into as many as a hundred and seventy forms each, including finite moods, nonfinite forms, and verbal nouns.
## Background

In Latin dictionaries, non-defective verbs typically have four principal parts:
1. first person singular present active indicative (la: "amo" | en: "I love")
2. present active infinitive (la: "amare" | en: "to love")
3. the first person singular perfect active indicative (la: "amavi" | en: "I loved")
4. the accusative supine (la: "amatum" | en: "to love") (alternatively the perfect passive participle)

The Latin WordNet API provides the first principal part as the "lemma" form and the stems of the latter three as principal parts. project.py takes in the first principal part and checks it against *uri.csv* to retrieve its URI (unique identifier on the API). It then accesses that verb's information using the URI, including its lemma form, its principal parts, and its irregular forms, storing all of this information in instance variables in the initialized Lexeme class. Also stored is the verb's deponency status, which is the quality of some verbs to take passive voice endings but always be active in meaning.

Note: Latin had no "v" (or "j"), which the API reflects, so all words with "v" are spelled with "u"
For example, "ueni uidi uici."

## Usage

### uri
uri.py counts the number of verbs in the API and creates the file *uri.csv* containing each lemma and the corresponding URI in the function **update_list**

project.py only calls this function if the user inputs yes. This **should _not_ be done frequently** as the amount of requests being passed to the API is very large if done.

### lexeme
lexeme.py contains the Lexeme class, which has the instance variables conj (conjugation: a pattern of endings that the verb follows) pp1 (principal part), pp2, pp3, deponent, and irregulars.
#### lexeme.encode
The **encode** function is used to convert the Latin WordNet API's morphological codes into the Latin Verb Conjugator's format, for the purpose of storing irregular forms.

API format:
(xxxxxxxxxx), where each of 10 characters represents:
 - part of speech
 - person (if verb), degree (if adjective)
 - number
 - tense
 - mood
 - voice
 - gender
 - case
 - declension (if noun or derived part), conjugation (if verb or derived part)
 - there exist an "i" variant of both the third declension and the third conjugation, for which an "i" is specified here

Conjugator Format:
(xxxxxxxxx), where each of 9 digits represents:
 - part of speech
 - gender
 - case
 - person
 - number
 - tense
 - voice
 - mood
 - degree

The API uses "-", while the conjugator uses "0" to indicate that a given paradigm does not exist in a form (such as gender for finite verbs). The full key is provided in *api_convert.json*.

#### lexeme.conjugate
The **conjugate** function uses the 9-digit code to conjugate a given verb form.

First the code is checked against the keys of the "irregulars" dictionary, and if found, the corresponding value, the irregular form, is returned. Otherwise the code is dissected to determine each paradigm. Because most Latin endings do not have a heavy distinct pattern across person, the three person and two number paradigms are combined into six pernums. then the helper function **lexeme.stem** uses paradigm logic to determine the stem, and **lexeme.ending** determines the ending and retrieves it from *regular_endings.json*.

Because some forms are never possible (such as future or future perfect subjunctives), lexeme.conjugate checks if the ending exists and if the stem is not "-" (the API's indication that no parts exist which use that stem). If not, then the combined form of stem and ending is returned.

### project.py

First calls **get_verb** to initialize the Lexeme object with a valid URI if given. Then calls **get_action** for further actions, and repeats.

#### get_action

The user is continually prompted to make one of five actions, using time.sleep to wait between each action output and the next prompt. The principal parts of a verb can be displayed. A new verb can be chosen, and **get_action** will be re-called. The program can be ended.

**chart** and **form** are detailed below.

#### chart

The format of the chart is modeled off a Wiktionary conjugation chart (e.g. [https://en.wiktionary.org/wiki/amo#Conjugation](https://en.wiktionary.org/wiki/amo#Conjugation))

Three DataFrames are created and displayed top-to-bottom, all of which use MultiIndexes made from DataFrames as column and index names. The values for these names are found in *chart.json*. The first displays finite forms, including indicative, subjunctive, and imperative mood verbs conjugated for voice, tense, number, and person. The second displays nonfinite forms, including infinitives and participles, conjugated for voice and tense. The third displays verbal nouns, including the gerund and the supine, conjugated for case.

#### form

Gets step-by-step user input to manually create one of the forms found in the conjugation chart, using **api_convert.json** as the *inputs* file throughout.

First calls **get_paradigm** to get the mood, then a dict for that mood's given conditions, and a dict for error messages.

The conditions dict provides the paradigms needed to conjugate a verb in that mood, along with the valid options for each paradigm. These paradigms are placed in a dict, with the given paradigm as key and the return value of **get_valid_input** called on the paradigm and its valid options. Any error messages that may be created are displayed.

To correct for API irregularities, the gender of all participles and gerunds is set to masculine, while their number is set to singular. If they are not one of these forms, the gender is set to none, while the number is set to the user-input value (or none if not applicable).

The subcode_conditions dict stores these values, as well as a lambda function that gets the user-input value.

Since all forms generated are verbs and have no degree, the subcode comprises the inner seven digits of the Conjugator's morphological code format, and **lexeme.conjugate** is called and the form is displayed alongside an English-language representation of the applicable dparadigm values.

##### get_paradigm

Takes as arguments the *inputs* file and a paradigm. Called on its own only once in **form**, to get the mood, which determines the logic for the rest of the steps. Otherwise called by **get_valid_input**. Considers as valid any input that is existing as a key within the *inputs* file.

##### get_valid_input

Takes as arguments the *inputs* file, a paradigm, valid_options (which can be a bool True, indicating that all inputs considered valid by **get_paradigm** are valid, or a list of valid inputs) and an optional error message. This function allows for checking the validity of inputs based on previous inputs, whereas **get_paradigm** checks for overall validity.

For example, Latin has six verb tenses: present, imperfect, future, perfect, pluperfect, and future perfect.
However, the future and future perfect do not exist in the subjunctive mood. **get_valid_input** ensures (on a mood-differentiating level) that the input is valid.
