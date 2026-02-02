import boto3
import os

transcribe = boto3.client('transcribe')

def handler(event, context):
    detail = event['detail']
    bucket = detail['bucket']['name']
    key =  detail['object']['key']

    # Example Key: "input/audio-file.wav"
    job_name = key.split('/')[-1].replace('.', '-')
    job_uri = f's3://{bucket}/{key}'
    print(f"Starting transcription job for: {job_uri}")

    response = transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_uri},
        MediaFormat=key.split('.')[-1],
        LanguageCode='en-US',   
    )

    print(response)
    

    



