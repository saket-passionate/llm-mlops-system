from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_ecr as ecr,
    aws_codebuild as codebuild,
    aws_codepipeline_actions as codepipeline_actions
    )
from constructs import Construct    

class LLmMlopsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket for model artifacts
        model_bucket = s3.Bucket(self, "LLMModelBucket")

        # IAM Role for SageMaker
        sagemaker_role = iam.Role(
            self, "LLMSageMakerExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com")
        )

        # Attach necessary policies to the role
        sagemaker_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")
        )
        model_bucket.grant_read(sagemaker_role) 
        sagemaker_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        )       

        sagemaker_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchFullAccess")
        )

        sagemaker_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly")
        )         

        # ECR Repository for Docker Image
        ecr_repository = ecr.Repository.from_repository_name(
            self, "LLMECRRepository", "stablelm-3b-inference"
        )

        ecr_repository.grant_pull(sagemaker_role)
        model_bucket.grant_read(sagemaker_role)

        # Lambda function to deploy SageMaker Endpoint
        lambda_fn = _lambda.Function(
            self, "DeployLLMSageMakerEndpoint",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="deploy_sagemaker_endpoint.handler",
            code=_lambda.Code.from_asset("../lambda_package.zip"),
            memory_size=512,
        )

        # Grant necessary permissions to the Lambda function
        lambda_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "sagemaker:CreateModel",
                    "sagemaker:CreateEndpointConfig",
                    "sagemaker:CreateEndpoint",
                    "sagemaker:DescribeEndpoint",
                    "sagemaker:DeleteModel",
                    "sagemaker:DeleteEndpointConfig",
                ],
                resources=["*"],
            )
        )

        
        # CodeBuild Project to build and push Docker image to ECR
        codebuild_project = codebuild.Project(
            self, "stablelm-3b-docker-build",
            source=codebuild.Source.git_hub(
                owner="saket-passionate",
                repo="llm-mlops-system",
                branch_or_ref="main",
            ),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_6_0,
                privileged=True
            ),
            build_spec=codebuild.BuildSpec.from_source_filename(
                "/infra/docker_buildspec.yml"
            )
        )
        
        ecr_repository.grant_pull_push(codebuild_project.role)
        model_bucket.grant_read_write(codebuild_project.role)

        # CodePipeline to download model and upload to S3
        codebuild_project_model = codebuild.Project(
            self, "stablelm-3b-model-upload",
            source=codebuild.Source.git_hub(
                owner="saket-passionate",
                repo="llm-mlops-system",
                branch_or_ref="main",
            ),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_6_0,
                privileged=True
            ),
            build_spec=codebuild.BuildSpec.from_source_filename(
                "/infra/model_download_buildspec.yml"
            )
        )

        codebuild_project.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "codeconnections:GetConnection",
                    "codeconnections:GetConnectionToken",
                    "codeconnections:UseConnection",
                    ],
                    resources=[
                        "*"
                ],
            )
        )
        codebuild_project_model.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "codeconnections:GetConnection",
                    "codeconnections:GetConnectionToken",
                    "codeconnections:UseConnection",
                    ],
                    resources=[
                        "*"
                ],
            )
        )

        ecr_repository.grant_pull_push(codebuild_project_model.role)
        model_bucket.grant_read_write(codebuild_project_model.role)

        



         




          


        


