from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    RemovalPolicy,
    Duration
)



class AudioIngestionStack(Stack):
    def __init__(self, scope: Stack, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket for Audio Ingestion
        audio_bucket = s3.Bucket(
            self, 
            "AudioIngestionBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            event_bridge_enabled=True
        )


         # Lambda Function to handle audio events
        transcription_lambda = _lambda.Function(
            self,
            "TranscriptionLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,    
            handler="start_transcription.handler",
            code=_lambda.Code.from_asset("../lambda/transcription"),
            timeout=Duration.seconds(30),
        )

        audio_bucket.grant_read(transcription_lambda)

        # Event Bridge Rule to trigger Lambda on new audio file upload
        audio_upload_rule = events.Rule(
            self,
            "AudioUploadRule",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                detail={
                    "bucket": {
                        "name": [audio_bucket.bucket_name]
                    },
                    "object": {
                        "key": [{
                            "prefix": "input/"  # Adjust prefix as needed
                        }]
                    }
                }
            )
        )

        audio_upload_rule.add_target(targets.LambdaFunction(transcription_lambda))  

        # IAM Permissions
        transcription_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "transcribe:StartTranscriptionJob",
                    "transcribe:GetTranscriptionJob",
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                resources=["*"]
            )
        )   
        audio_bucket.grant_read_write(transcription_lambda) 

        transcription_lambda.add_permission(
            "AllowEventBridgeInvoke",
            principal=iam.ServicePrincipal("events.amazonaws.com"),
            action="lambda:InvokeFunction"
        )

        # Sagemaker Trigger Lambda
        summarize_lambda = _lambda.Function(
            self,
            "SummarizeLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="summarize_clinical.handler",
            code=_lambda.Code.from_asset("../lambda/summarization"),
            timeout=Duration.seconds(300),
            environment={
                "PATIENT_EMAIL": "saketthavananilindan@gmail.com",
                "SAGEMAKER_ENDPOINT_NAME": "stablelm-3b-endpoint",
                "SOURCE_EMAIL": "saketthavananilindan@gmail.com"
            }
        )

        summarize_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "sagemaker:InvokeEndpoint"
                ],
                resources=["*"]
            )
        )

        # Add S3 trigger for summarize_lambda on transcription output
        audio_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(summarize_lambda),
            s3.NotificationKeyFilter(
                prefix="transcripts/",
                suffix=".json"
                )
        )  
       

        audio_bucket.grant_read_write(summarize_lambda)  


        


