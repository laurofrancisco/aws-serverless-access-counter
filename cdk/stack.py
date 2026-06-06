from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
)
from constructs import Construct

class ContadorAcessosStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Cria a Tabela no DynamoDB
        tabela = dynamodb.Table(
            self, "TabelaContador",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        # 2. Cria a Função Lambda (apontando para a pasta src/backend)
        funcao_lambda = _lambda.Function(
            self, "LambdaContador",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("../src/backend"),
            environment={
                "TABLE_NAME": tabela.table_name # Passa o nome da tabela para o código Python
            }
        )

        # 3. Dá permissão para o Lambda escrever no DynamoDB (AWS IAM)
        tabela.grant_read_write_data(funcao_lambda)

        # 4. Cria o API Gateway apontando para o Lambda
        api = apigw.LambdaRestApi(
            self, "ApiContador",
            handler=funcao_lambda
        )
        
        # (Aqui também entrariam as configurações do CloudFront, WAF e Route 53...)