import json
import spacy
import pandas as pd
from spacy.lang.en import English
from spacy.pipeline import EntityRuler
import boto3
import os

# Assume the Spacy model and dictionary.json are packaged with the deployment
# and loaded from the /tmp directory since Lambda's filesystem is read-only except for /tmp.

# Define the Lambda handler function


def lambda_handler(event, context):
    # Load the dictionary from a JSON file packaged with the deployment
    dictionary_path = '/tmp/dictionary.json'
    with open(dictionary_path, 'r') as f:
        data = json.load(f)

    # Load the SpaCy model packaged with the deployment
    nlp = spacy.load("/tmp/en_core_web_sm")

    # Assume 'text' is passed in the event object
    text = event.get('text', '')

    # Your processing logic here
    # ...

    # Instead of print, return the result as part of the response
    return {
        'statusCode': 200,
        'body': json.dumps({
            'transformed_text': new_text
        })
    }
