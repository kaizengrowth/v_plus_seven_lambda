import json
import spacy
import pandas as pd
import re
import string
import sys

# Assume that Spacy and its model are included in the Lambda deployment package
# Or loaded from a Lambda Layer
# nlp = spacy.load("/opt/en_core_web_sm")  # Path when using Lambda Layer
nlp = spacy.load("en_core_web_sm")


def load_dictionary(json_filepath):
    with open(json_filepath, 'r') as f:
        data = json.load(f)
    return data


def process_text(text, data):
    df = pd.DataFrame(data)
    verbs_df = df[df['pos'] == 'v.'].reset_index(drop=True)

    text_without_punctuation = text.translate(
        str.maketrans('', '', string.punctuation))
    words = text_without_punctuation.split()
    print(words)

    # Mapping original words to their lemmatized forms
    original_to_lemmatized = {
        word: nlp(word)[0].lemma_.upper() for word in words if nlp(word)[0].pos_ == 'VERB'
    }

    print(original_to_lemmatized)

    # Mapping from lemmatized verb to its replacement (the 7th verb following it in verbs_df)
    new_verbs_list = {}
    for original_word, lemmatized_word in original_to_lemmatized.items():
        matching_rows = verbs_df[verbs_df['word'].str.upper()
                                 == lemmatized_word]
        if not matching_rows.empty:
            current_index = matching_rows.index[0]
            new_index = (current_index + 7) % len(verbs_df)
            new_verb = verbs_df.iloc[new_index]['word']
            new_verbs_list[original_word] = new_verb
        else:
            new_verbs_list[original_word] = original_word

    print(new_verbs_list)

    # # Replacement
    # pattern = r'\b(?:{})\b'.format(
    #     '|'.join(map(re.escape, lemmatized_verbs.values())))
    # new_text = re.sub(pattern, lambda match: new_verbs_list.get(
    #     match.group(0).upper(), match.group(0)), text, flags=re.IGNORECASE)

    # return new_text

    def replace_func(match):
        word = match.group(0)
        return new_verbs_list.get(word, word)

    pattern = r'\b(' + '|'.join(re.escape(word)
                                for word in set(new_verbs_list.keys())) + r')\b'
    new_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

    return new_text


def lambda_handler(event, context):
    # Extract text and dictionary from event
    text = event['text']
    dictionary_data = event['dictionary']

    # Process the text
    new_text = process_text(text, dictionary_data)

    # Return the processed text
    return {
        'statusCode': 200,
        'body': json.dumps({
            'transformed_text': new_text
        })
    }


def main(text):
    dictionary_data = load_dictionary('dictionary.json')
    new_text = process_text(text, dictionary_data)
    print(new_text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py 'input_string'")
        sys.exit(1)

    input_text = sys.argv[1]
    main(input_text)
