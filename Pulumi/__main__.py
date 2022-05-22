import json
import pulumi_aws as aws


# defining config file
with open("./config.json") as config_file:
    data = json.load(config_file)

APP_NAME = data["APP_NAME"]
APP_PORT = data["APP_PORT"]
IMAGE_IDENTIFIER = data["IMAGE_IDENTIFIER"]
VPC_ID = data["VPC_ID"]
SUBNETS = data["SUBNETS"]
ACCOUNTID = data["ACCOUNTID"]
REGION = data["REGION"]


app_runner_role = aws.iam.Role(
    resource_name=f"{APP_NAME}-app-runner-role",
    name=f"{APP_NAME}-app-runner-role",
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess",
    ],
    assume_role_policy=json.dumps(
        {
            "Version": "2008-10-17",
            "Statement": [
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": [
                            "build.apprunner.amazonaws.com",
                            "tasks.apprunner.amazonaws.com",
                        ]
                    },
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    ),
)

app_security_group = aws.ec2.SecurityGroup(
    resource_name=f"{APP_NAME}-app-runner-security-group",
    name=f"{APP_NAME}-app-runner-security-group",
    vpc_id=VPC_ID,
    description="Enable app access",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
)
vpc_connector = aws.apprunner.VpcConnector(
    f"{APP_NAME}-vpc-connector",
    security_groups=[app_security_group.id],
    subnets=SUBNETS,
    vpc_connector_name=f"{APP_NAME}-vpc-connector",
    tags={"Name": f"{APP_NAME}-vpc-connector"},
)

app = aws.apprunner.Service(
    f"{APP_NAME}-apprunner",
    service_name=f"{APP_NAME}-apprunner",
    source_configuration=aws.apprunner.ServiceSourceConfigurationArgs(
        authentication_configuration=aws.apprunner.ServiceSourceConfigurationAuthenticationConfigurationArgs(
            access_role_arn=app_runner_role.arn,
        ),
        image_repository=aws.apprunner.ServiceSourceConfigurationImageRepositoryArgs(
            image_configuration=aws.apprunner.ServiceSourceConfigurationImageRepositoryImageConfigurationArgs(
                port=APP_PORT,
            ),
            image_identifier=f"{ACCOUNTID}.dkr.ecr.{REGION}.amazonaws.com/{IMAGE_IDENTIFIER}:latest",
            image_repository_type="ECR",
        ),
    ),
    network_configuration=aws.apprunner.ServiceNetworkConfigurationArgs(
        egress_configuration=aws.apprunner.ServiceNetworkConfigurationEgressConfigurationArgs(
            egress_type="VPC",
            vpc_connector_arn=vpc_connector.arn,
        ),
    ),
    tags={"Name": f"{APP_NAME}-apprunner"},
)
