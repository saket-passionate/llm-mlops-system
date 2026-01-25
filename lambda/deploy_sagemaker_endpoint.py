import boto3
import time

# ===============================
# Configuration
# ===============================
ENDPOINT_NAME = "stablelm-3b-endpoint"
ENDPOINT_CONFIG_NAME = "stablelm-3b-endpoint-config"
MODEL_NAME = "stablelm-3b-model"
MODEL_DATA_URI = "s3://llm-mlops-bucket-ca-central/models/stablelm-3b/stablelm-3b-model.tar.gz"
ECR_IMAGE_URI = "252312373833.dkr.ecr.ca-central-1.amazonaws.com/stablelm-inference:latest"
REGION = "ca-central-1"
ACCOUNT_ID = "252312373833"             

def handler(event, context):
    sagemaker = boto3.client('sagemaker', region_name=REGION)

    # Create Model
    print("Creating SageMaker model...")
    sagemaker.create_model(
        ModelName=MODEL_NAME,
        PrimaryContainer={
            'Image': ECR_IMAGE_URI,
            'ModelDataUrl': MODEL_DATA_URI,
            'Environment': {
                'TRANSFORMERS_CACHE': '/tmp/huggingface/transformers',
                'HF_HOME': '/tmp/huggingface',
            }
        },
        ExecutionRoleArn=f'arn:aws:iam::{ACCOUNT_ID}:role/LLMSageMakerExecutionRole'
    )
    print("Model created.")

    # Create Endpoint Configuration
    print("Creating endpoint configuration...")
    sagemaker.create_endpoint_config(
        EndpointConfigName=ENDPOINT_CONFIG_NAME,
        ProductionVariants=[
            {
                'VariantName': 'AllTraffic',
                'ModelName': MODEL_NAME,
                'InstanceType': 'ml.g5.4xlarge',
                'InitialInstanceCount': 1,
            },
        ]
    )
    print("Endpoint configuration created.")

    # Create Endpoint
    print("Creating SageMaker endpoint...")
    sagemaker.create_endpoint(
        EndpointName=ENDPOINT_NAME,
        EndpointConfigName=ENDPOINT_CONFIG_NAME
    )
    print("Endpoint creation initiated.")

    # Wait for the endpoint to be in service
    print("Waiting for endpoint to be in service...")
    waiter = sagemaker.get_waiter('endpoint_in_service')
    waiter.wait(EndpointName=ENDPOINT_NAME)
    print("Endpoint is in service and ready for inference.")

    return {
        'statusCode': 200,
        'body': f'SageMaker endpoint {ENDPOINT_NAME} is deployed and ready for inference.'
    }   
