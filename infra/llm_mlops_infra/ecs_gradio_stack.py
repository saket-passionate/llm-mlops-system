from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ecs_patterns as ecs_patterns,   
    aws_ecr as ecr,
)



class GradioEcsStack(Stack):

    def __init__(self, scope: Stack, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC
        vpc = ec2.Vpc(self, "GradioVpc", max_azs=2, nat_gateways=1)

        # ECS Cluster
        cluster = ecs.Cluster(self, "GradioCluster", vpc=vpc)

        # ECR Repository
        ecr_repository = ecr.Repository(
            self,
            "GradioEcrRepo",
            repository_name="gradio-sagemaker-inference",
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_images=True,
            )


        # Task Definition
        task_definition = ecs.FargateTaskDefinition(
            self,
            "GradioTaskDef",
            cpu=512,
            memory_limit_mib=1024,
        )

        # IAM Permission for ECS Task
        task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "sagemaker:InvokeEndpoint",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=["*"],
            )
        )

        # Container Definition
        container = task_definition.add_container(
            "GradioContainer",
            image=ecs.ContainerImage.from_ecr_repository(ecr_repository, tag="latest"),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="GradioLogs"),
            environment={
                "SAGEMAKER_ENDPOINT_NAME": "stablelm-3b-endpoint",
                "AWS_REGION": "ca-central-1",
            },      
        )

        container.add_port_mappings(
            ecs.PortMapping(container_port=7860)
        )   
        
           
        # ECS Service with Application Load Balancer
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "GradioFargateService",
            cluster=cluster,
            cpu=512,
            memory_limit_mib=1024,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(ecr_repository, tag="latest"),
                container_port=7860,
            ),
            public_load_balancer=True,
            listener_port=80,
            desired_count=1,
        )

        fargate_service.target_group.configure_health_check(
            path="/ping",
            healthy_http_codes="200",
            unhealthy_threshold_count=2,
            healthy_threshold_count=2,
        )

        # Output
        self.gradio_service_url = fargate_service.load_balancer.load_balancer_dns_name