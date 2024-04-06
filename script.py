import json
import spacy
import pandas as pd
import boto3
import re
import string

# Assume that Spacy and its model are included in the Lambda deployment package
# Or loaded from a Lambda Layer
nlp = spacy.load("/opt/en_core_web_sm")  # Path when using Lambda Layer


def process_text(text, data):
    df = pd.DataFrame(data)
    verbs_df = df[df['pos'] == 'v.'].reset_index(drop=True)

    # Remove punctuation and process text
    text_without_punctuation = text.translate(
        str.maketrans('', '', string.punctuation))
    words = text_without_punctuation.split()

    # Find and lemmatize verbs
    lemmatized_verbs = {word: nlp(word)[0].lemma_.upper(
    ) for word in words if nlp(word)[0].pos_ == 'VERB'}

    # Find new verbs after applying the transformation
    new_verbs_list = {lemma: verbs_df.loc[(df[df['word'] == lemma].index[0] + 7) % len(
        verbs_df), 'word'] for lemma in lemmatized_verbs.values()}

    # Perform the replacement
    pattern = r'\b(?:{})\b'.format(
        '|'.join(map(re.escape, lemmatized_verbs.keys())))
    new_text = re.sub(pattern, lambda match: new_verbs_list.get(
        lemmatized_verbs[match.group(0)]), text)

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
