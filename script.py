import json
import spacy
import pandas as pd
import re
import boto3

# Assume that Spacy and its model are included in the Lambda Layer
nlp = spacy.load("/opt/en_core_web_sm")


def load_dictionary_from_s3(bucket_name, object_key):
    """Load a dictionary of words from an S3 bucket."""
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    dictionary_data = json.load(response['Body'])
    return dictionary_data


def process_text(text, data):
    """Process the given text to replace verbs based on the provided data."""
    df = pd.DataFrame(data)
    verbs_df = df[df['pos'] == 'v.'].reset_index(drop=True)

    text_without_punctuation = text.translate(
        str.maketrans('', '', string.punctuation))
    words = text_without_punctuation.split()

    # Mapping original words to their lemmatized forms
    original_to_lemmatized = {
        word: nlp(word)[0].lemma_.upper() for word in words if nlp(word)[0].pos_ == 'VERB'
    }

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

    def replace_func(match):
        word = match.group(0)
        return new_verbs_list.get(word, word)

    pattern = r'\b(' + '|'.join(re.escape(word)
                                for word in set(new_verbs_list.keys())) + r')\b'
    new_text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)

    return new_text


def lambda_handler(event, context):
    """AWS Lambda function handler."""
    # Assuming the event contains the S3 bucket and object key for the dictionary,
    # and the text to process.
    bucket_name = event['bucket_name']
    object_key = event['object_key']
    text = event['text']

    dictionary_data = load_dictionary_from_s3(bucket_name, object_key)

    new_text = process_text(text, dictionary_data)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'transformed_text': new_text
        })
    }
