import boto3
import time

## Configure these variables as needed
REGION = 'ca-central-1'
ACCOUNT_ID = boto3.client('sts').get_caller_identity().get('Account')  
BUCKET_NAME = 'llm-rag-bucket-ca-central'          

MODEL_NAME = 'stablelm-3b-model'
ENDPOINT_CONFIG_NAME = 'stablelm-3b-config'
ENDPOINT_NAME = 'stablelm-3b-endpoint'

ECR_IMAGE_URI = f'{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/stablelm-inference:latest'
MODEL_DATA_URI = "s3://llm-rag-bucket-ca-central/models/stablelm-3b/stablelm-3b-model.tar.gz"

INSTANCE_TYPE = 'ml.g5.xlarge'

## Create Sagemaker Execution Role ARN


EXECUTION_ROLE_ARN = 'arn:aws:iam::252312373833:role/MlopsPipelineStack-SageMakerExecutionRole7843F3B8-84gSLJ2pWKPJ'


## Create SageMaker client

sagemaker = boto3.client('sagemaker', region_name=REGION)



#IF MODEL EXSISTS THEN DELETE AND 
try:
    sagemaker.delete_model(ModelName=MODEL_NAME)
    print("Model deleted.")
except:
    pass

## Create Model
print("Creating SageMaker model...")
sagemaker.create_model(
    ModelName=MODEL_NAME,
    PrimaryContainer={
        'Image': ECR_IMAGE_URI,
        'ModelDataUrl': MODEL_DATA_URI,
        'Environment': {
            'TRANSFORMERS_CACHE': '/tmp/huggingface/transformers' ,
            'HF_HOME': '/tmp/huggingface' ,  
        }     
    },
    ExecutionRoleArn=EXECUTION_ROLE_ARN
)
print("Model created.")


## Create Endpoint Configuration
try:
    sagemaker.delete_endpoint_config(EndpointConfigName=ENDPOINT_CONFIG_NAME)
    print("Endpoint configuration deleted.")
except:
    pass

print("Creating endpoint configuration...")
sagemaker.create_endpoint_config(
    EndpointConfigName=ENDPOINT_CONFIG_NAME,
    ProductionVariants=[
        {
            'VariantName': 'AllTraffic',
            'ModelName': MODEL_NAME,
            'InstanceType': INSTANCE_TYPE,
            'InitialInstanceCount': 1,
        },
    ]   
)   
print("Endpoint configuration created.")

# Create Endpoint
try:
    sagemaker.delete_endpoint(EndpointName=ENDPOINT_NAME)
    print("Endpoint deleted.")
    time.sleep(60)  # Wait for deletion to complete
except:
    pass  

print("Creating endpoint...")
sagemaker.create_endpoint(
    EndpointName=ENDPOINT_NAME,
    EndpointConfigName=ENDPOINT_CONFIG_NAME
)
print("Endpoint creation initiated.")           
print("Waiting for endpoint to be in service...")
waiter = sagemaker.get_waiter('endpoint_in_service')
waiter.wait(EndpointName=ENDPOINT_NAME)
print("Endpoint is in service and ready to use.")




