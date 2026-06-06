import json
import os
import boto3
import logging
from botocore.exceptions import ClientError

# Configuração de logs para o CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicializa o recurso do DynamoDB fora do handler para reutilizar a conexão (Warm Start)
dynamodb = boto3.resource('dynamodb')

# Busca o nome da tabela dinâmica via variável de ambiente configurada no CDK
TABLE_NAME = os.environ.get('TABLE_NAME', 'ContadorAcessos')
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    
    logger.info("Iniciando processamento de acesso.") # Este log aparecerá no CloudWatch
    """
    Função Lambda responsável por incrementar e retornar o número total 
    de acessos da Landing Page de forma atômica no DynamoDB.
    """
    try:
        # Executa o incremento atômico (+1) na Partition Key 'id' com valor 'hits'
        response = table.update_item(
            Key={'id': 'hits'},
            UpdateExpression="ADD #count_attr :val",
            ExpressionAttributeNames={'#count_attr': 'count'},
            ExpressionAttributeValues={':val': 1},
            ReturnValues="UPDATED_NEW"
        )
        
        # Extrai o valor atualizado retornado pelo DynamoDB
        total_atual = int(response['Attributes']['count'])
        
        # Retorno de sucesso estruturado para o API Gateway
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',  # Libera o acesso para o Frontend (CORS)
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': json.dumps({
                'status': 'sucesso',
                'total_acessos': total_atual
            })
        }
        
    except ClientError as e:
        # Log detalhado que será capturado automaticamente pelo Amazon CloudWatch
        print(f"[ERRO] Falha ao atualizar o DynamoDB: {e.response['Error']['Message']}")
        logger.error(f"Erro ao acessar DynamoDB: {str(e)}") # Log de erro crítico
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'erro',
                'message': 'Erro interno ao processar a requisição.'
            })
        }