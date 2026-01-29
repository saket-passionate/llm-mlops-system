from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_ecr as ecr,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    RemovalPolicy
    )
from constructs import Construct

from llm_mlops_infra.ecs_gradio_stack import GradioEcsStack    

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
        ecr_repository = ecr.Repository(
            self, "LLMECRRepository",
            repository_name="llm-ecr-repo",
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_images=True,
        )

        ecr_repository.grant_pull(sagemaker_role)
        model_bucket.grant_read(sagemaker_role)

        # Lambda function to deploy SageMaker Endpoint
        lambda_fn = _lambda.Function(
            self, "DeployLLMSageMakerEndpoint",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="deploy_sagemaker_endpoint.handler",
            code=_lambda.Code.from_asset("../lambda"),
            memory_size=512,
            environment={
                "SAGEMAKER_ROLE_ARN": sagemaker_role.role_arn,
                "ECR_IMAGE_URI": ecr_repository.repository_uri + ":latest",
                "MODEL_DATA_URI": f"s3://{model_bucket.bucket_name}/models/stablelm-3b/stable-3b-model.tar.gz",
                "MODEL_NAME": "stablelm-3b-model",
                "ENDPOINT_CONFIG_NAME": "stablelm-3b-endpoint-config",
                "ENDPOINT_NAME": "stablelm-3b-endpoint",
                "REGION": self.region,
                "ACCOUNT_ID": self.account,
            }
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
                    "sagemaker:DeleteEndpoint"
                ],
                resources=["*"],
            )
        )
        lambda_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "iam:PassRole",
                ],
                resources=["*"]
            )
        )

        # CodeBuild Project to build and push ECS GradioDocker image to ECR
        codebuild_gradio_job = codebuild.Project(
            self, "GradioDockerBuild",
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
                "infra/gradio_image_buildspec.yml"
            ),
            environment_variables={
                "ECR_REPOSITORY": codebuild.BuildEnvironmentVariable(
                    value="gradio-sagemaker-inference"
                ),
                "AWS_ACCOUNT_ID": codebuild.BuildEnvironmentVariable(
                    value=self.account
                ),      
                "REGION": codebuild.BuildEnvironmentVariable(
                    value=self.region
                ),
                "IMAGE_NAME": codebuild.BuildEnvironmentVariable(
                    value="gradio-ui"
                )
            }
        )

        codebuild_gradio_job.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "ecr:InitiateLayerUpload",
                    "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload",
                    "ecr:PutImage",
                    
                ],
                resources=["*"],    
            )
        )

        
        # CodeBuild Project to build and push Docker image to ECR
        codebuild_docker_job = codebuild.Project(
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
                "infra/docker_buildspec.yml"
            ),
            environment_variables={
                "ECR_REPOSITORY": codebuild.BuildEnvironmentVariable(
                    value=ecr_repository.repository_name
                ),
                "AWS_ACCOUNT_ID": codebuild.BuildEnvironmentVariable(
                    value=self.account
                ),          
                "REGION": codebuild.BuildEnvironmentVariable(
                    value=self.region
                ),
                "IMAGE_NAME": codebuild.BuildEnvironmentVariable(
                    value="stablelm-3b-inference"
                )

            }
        )

        ecr_repository.grant_pull_push(codebuild_docker_job.role)
        model_bucket.grant_read_write(codebuild_docker_job.role)

        # CodePipeline to download model and upload to S3
        codebuild_model_dowload = codebuild.Project(
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
                "infra/model_download_buildspec.yml"
            ),
            environment_variables={
                "S3_MODEL_PATH": codebuild.BuildEnvironmentVariable(
                    value="s3://{model_bucket.bucket_name}/models/stablelm-3b/stable-3b-model.tar.gz"
                ),
            }
        )
        

        codebuild_model_dowload.add_to_role_policy(
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
        codebuild_model_dowload.add_to_role_policy(
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

        ecr_repository.grant_pull_push(codebuild_model_dowload.role)
        model_bucket.grant_read_write(codebuild_model_dowload.role)

        # CodePipeline to orchestrate the process
        source_output = codepipeline.Artifact()

        pipeline = codepipeline.Pipeline(
            self, "GenAICodePipeline",
            
            stages=[
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[
                        codepipeline_actions.CodeStarConnectionsSourceAction(
                            action_name="GitHub_Source",
                            connection_arn="arn:aws:codeconnections:ca-central-1:252312373833:connection/0cb5616f-e4f5-4a61-b0a6-76ed2b47b54b",  # Replace with your CodeStar Connection ARN
                            output=source_output,
                            owner="saket-passionate",
                            repo="llm-mlops-system",
                            branch="main",
                        )
                    ],
                ),      
                codepipeline.StageProps(
                    stage_name="BuildAndPushGradioImage",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="BuildAndPushGradioImage",
                            project=codebuild_gradio_job,
                            input=source_output, 
                        )
                    ],
                ),

                codepipeline.StageProps(
                    stage_name="BuildAndPushDockerImage",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="BuildAndPushDockerImage",
                            project=codebuild_docker_job,
                            input=source_output, 
                        )
                    ],
                ),

                codepipeline.StageProps(
                    stage_name="DownloadAndPackageModel",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="DownloadAndPackageModel",
                            project=codebuild_model_dowload,
                            input=source_output,
                        )
                    ],
                ),

            codepipeline.StageProps(
                stage_name="DeploySageMakerEndpoint",
                actions=[
                    codepipeline_actions.LambdaInvokeAction(
                        action_name="DeploySageMakerEndpoint",
                        lambda_=lambda_fn
                       )
                    ],
                )
            ]
        )

        pipeline.role.add_to_policy(
            iam.PolicyStatement(
                actions=["codestar-connections:UseConnection"],
                resources=[
                    "arn:aws:codeconnections:ca-central-1:252312373833:connection/0cb5616f-e4f5-4a61-b0a6-76ed2b47b54b"
                    ],
            ),
        )   

        pipeline.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "lambda:InvokeFunction",
                    "lambda:ListFunctions",
                    "s3:fullaccess",
                    "ecr:fullaccess",
                    "codebuild:StartBuild",
                    "codebuild:BatchGetBuilds",
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



         




          


        


