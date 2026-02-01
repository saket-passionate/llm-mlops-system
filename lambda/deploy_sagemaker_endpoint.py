import boto3
import time
import os

# ===============================
# Configuration
# ===============================

ENDPOINT_CONFIG_NAME = os.environ["ENDPOINT_CONFIG_NAME"]
ENDPOINT_NAME = os.environ["ENDPOINT_NAME"]
MODEL_NAME = os.environ["MODEL_NAME"]
MODEL_DATA_URI = os.environ["MODEL_DATA_URI"]
ECR_IMAGE_URI = os.environ["ECR_IMAGE_URI"]
REGION = os.environ["REGION"]
ACCOUNT_ID = os.environ["ACCOUNT_ID"]
EXECUTION_ROLE_ARN = os.environ["SAGEMAKER_ROLE_ARN"]
       

def handler(event, context):
    sagemaker = boto3.client('sagemaker', region_name=REGION)

    # Check if model exists and delete
    try:
        sagemaker.delete_model(ModelName=MODEL_NAME)
        print("Model deleted.")
    except sagemaker.exceptions.ClientError as e:
        if "Could not find model" in str(e):
            print("Model does not exist, skipping deletion.")
        else:
            raise   

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
        ExecutionRoleArn=EXECUTION_ROLE_ARN
    )
    print("Model created.")

    # Check if endpoint config exists and delete
    try:
        sagemaker.delete_endpoint_config(EndpointConfigName=ENDPOINT_CONFIG_NAME)
        print("Endpoint configuration deleted.")
    except sagemaker.exceptions.ClientError as e:
        if "Could not find endpoint configuration" in str(e):
            print("Endpoint configuration does not exist, skipping deletion.")
        else:
            raise       

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
