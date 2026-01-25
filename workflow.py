
# Code Build downloads LLM Model, packages it and upload to S3 for SageMaker deployment
# Code Build Create a Docker Image with Inference Script and push to ECR
# Code Deploy Deploys Infrastructure using CDK to create bucket, roles, policies, sageMaker endpoint permissions
# Docker Image and S3 create an event to trigger lambda function
# Lambda Function Triggers Sagemaker Endpoint Deployment Script
# SageMaker Endpoint is deployed and ready for inference
# Deploy as API to gradio UI
# How can I amke an llm system on aws and also include rag then 
