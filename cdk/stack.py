from aws_cdk import (
    Stack,
    Duration,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_wafv2 as wafv2,
    aws_route53 as route53,
    aws_logs as logs,
)
from constructs import Construct

class ContadorAcessosStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. DynamoDB
        tabela = dynamodb.Table(
            self, "TabelaContador",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        # 2. Lambda com Monitoramento CloudWatch
        funcao_lambda = _lambda.Function(
            self, "LambdaContador",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("../src/backend"),
            environment={"TABLE_NAME": tabela.table_name},
            log_retention=logs.RetentionDays.ONE_WEEK # Configuração do CloudWatch Logs
        )

        tabela.grant_read_write_data(funcao_lambda)

        # 3. API Gateway
        api = apigw.LambdaRestApi(self, "ApiContador", handler=funcao_lambda)

        # 4. WAF (Web Application Firewall)
        web_acl = wafv2.CfnWebACL(
            self, "WafProtecao",
            default_action={"allow": {}},
            scope="CLOUDFRONT",
            visibility_config={"cloudWatchMetricsEnabled": True, "metricName": "WafMetrics", "sampledRequestsEnabled": True},
            rules=[ # Aqui entrariam as regras de Rate Limiting
                wafv2.CfnWebACL.RuleProperty(
                    name="RateLimitRule",
                    priority=1,
                    statement=wafv2.CfnWebACL.StatementProperty(
                        rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                            limit=1000, # Bloqueia se um IP fizer mais de 1000 requisições em 5 min
                            aggregate_key_type="IP"
                        )
                    ),
                    action={"block": {}},
                    visibility_config={
                        "sampledRequestsEnabled": True,
                        "cloudWatchMetricsEnabled": True,
                        "metricName": "RateLimitMetric"
                    }
                )
            ]
        )
        # 5. CloudFront (CDN)
        distribuicao = cloudfront.Distribution(
            self, "CloudFrontDist",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.RestApiOrigin(api),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            web_acl_id=web_acl.attr_arn
        )
        # 6. Route 53 (DNS)(Exemplo de integração)
        # Para isso funcionar, você precisaria de um domínio (ex: 'meusite.com')
        # já registrado no Route 53 como uma Hosted Zone.
        
        # Se você tiver um domínio, descomente e ajuste as linhas abaixo:
        
        # hosted_zone = route53.HostedZone.from_lookup(
        #     self, "HostedZone",
        #     domain_name="seudominio.com"
        # )
        
        # route53.ARecord(
        #     self, "AliasRecord",
        #     zone=hosted_zone,
        #     target=route53.RecordTarget.from_alias(targets.CloudFrontTarget(distribuicao))
        # )