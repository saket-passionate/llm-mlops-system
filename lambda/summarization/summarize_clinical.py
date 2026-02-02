import boto3
import json
import os


sagemaker_client = boto3.client('sagemaker-runtime')
s3 = boto3.client('s3')
ses = boto3.client('ses')

SAGEMAKER_ENDPOINT_NAME = os.environ['SAGEMAKER_ENDPOINT_NAME']


CLINICAL_PROMPT = """
You are a clinical documentation assistant.
Convert the following doctor-patient conversation into a structured clinical note.

Use this format:

Chief Complaint:
History of Present Illness:
Past Medical History:
Medications:
Assessment:
Plan:

Transcript:
"""


def handler(event, context):

    print("Event received:", event)

    record = event['Records'][0]
    bucket_name = record['s3']['bucket']['name']    
    key = record['s3']['object']['key']
    print(f"Processing file from bucket: {bucket_name}, key: {key}")

    # Get the trabnscript file from S3
    obj = s3.get_object(Bucket=bucket_name, Key=key)
    transcript_json = obj['Body'].read().decode('utf-8')  
    transcript_data = json.loads(transcript_json)

    transcript_text = transcript_data["results"]["transcripts"][0]["transcript"] 

    promopt = CLINICAL_PROMPT + transcript_text

    # Invoke SageMaker endpoint
    response = sagemaker_client.invoke_endpoint(
        EndpointName=SAGEMAKER_ENDPOINT_NAME,
        Body=json.dumps(
            {
            "inputs": promopt,
            "max_new_tokens": 512,
            "do_sample": True,
            "top_p": 0.9,
            "temperature": 0.7,
            "repetition_penalty": 1.2
            }
            ),
        ContentType='application/json'
    )

    result = json.loads(response['Body'].read().decode())
    summary = result['generated_text']


    print("Generated Clinical Summary:", summary)

    # Save the summary back to S3
   
    s3.put_object(
        Bucket=bucket_name,
        Key=key.replace("transcripts/", "summaries/").replace(".json", "_summary.txt"),
        Body=summary.encode('utf-8')
    )

    print("Clinical Summary saved to S3.")

    # Send email notification to patient
    ses.send_email(
        Source=os.environ['SOURCE_EMAIL'],
        Destination={
            'ToAddresses': [os.environ['PATIENT_EMAIL']],
        },
        Message={
            'Subject': {
                'Data': 'Your Clinical Summary is Ready',
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {
                    'Data': f'Hello,\n\nYour clinical summary has been generated and saved to your account.\n\nSummary:\n{summary}\n\nBest regards,\nYour Healthcare Team',
                    'Charset': 'UTF-8'
                }
            }
        }
    )

    print("Email notification sent to patient.")

    return {
        'statusCode': 200,
        'body': json.dumps('Clinical summary generated and saved successfully!')
    }



    
