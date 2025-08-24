import requests
import xml.etree.ElementTree as ET
import json
import boto3
from datetime import datetime
import logging

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def obter_partidos_json():
    url = "https://www.camara.leg.br/SitCamaraWS/Deputados.asmx/ObterPartidosCD"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        logger.info("Fazendo requisição para a API de partidos...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  
        
        logger.info("Processando dados XML...")
        root = ET.fromstring(response.content)
        
        partidos = []
        
        for partido_elem in root.findall('partido'):
            partido = {}
            
            campos = [
                'idPartido', 'siglaPartido', 'nomePartido', 
                'dataCriacao', 'dataExtincao'
            ]
            
            for campo in campos:
                elemento = partido_elem.find(campo)
                if elemento is not None and elemento.text is not None:
                    partido[campo] = elemento.text.strip()
                else:
                    partido[campo] = None
            
            partidos.append(partido)
        
        return partidos
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição HTTP: {e}")
        return None
    except ET.ParseError as e:
        logger.error(f"Erro no parse do XML: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return None

def obter_partidos_alternativo():
    url_alternativa = "https://www.camara.gov.br/SitCamaraWS/Deputados.asmx/ObterPartidosCD"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/xml, text/xml, */*',
    }
    
    try:
        logger.info("Tentando URL alternativa...")
        response = requests.get(url_alternativa, headers=headers, timeout=30)
        response.raise_for_status()
        
        logger.info("Processando dados XML da URL alternativa...")
        root = ET.fromstring(response.content)
        partidos = []
        
        for partido_elem in root.findall('.//partido'):
            partido = {
                'idPartido': partido_elem.findtext('idPartido'),
                'siglaPartido': partido_elem.findtext('siglaPartido'),
                'nomePartido': partido_elem.findtext('nomePartido'),
                'dataCriacao': partido_elem.findtext('dataCriacao'),
                'dataExtincao': partido_elem.findtext('dataExtincao')
            }
            partidos.append(partido)
        
        return partidos
        
    except Exception as e:
        logger.error(f"Erro na URL alternativa: {e}")
        return None

def salvar_s3(dados, bucket, key):
    try:
        s3_client = boto3.client('s3')
        
        json_data = json.dumps(dados, ensure_ascii=False, indent=2)
        
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json_data.encode('utf-8'),
            ContentType='application/json; charset=utf-8'
        )
        
        logger.info(f"Dados salvos com sucesso no S3: s3://{bucket}/{key}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao salvar no S3: {e}")
        return False

def filtrar_partidos_ativos(partidos):
    return [partido for partido in partidos if partido.get('dataExtincao') is None]

def filtrar_partidos_extintos(partidos):
    return [partido for partido in partidos if partido.get('dataExtincao') is not None]

def lambda_handler(event, context):
    try:
        partidos = obter_partidos_json()
        
        if not partidos:
            logger.info("Tentando método alternativo...")
            partidos = obter_partidos_alternativo()
        
        if not partidos:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Falha ao obter dados dos partidos após todas as tentativas',
                    'error': 'API_ERROR'
                })
            }
        
        # Gerar timestamp para o arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        bucket = 'dev-lab-02-us-east-2-landing'
        base_key = 'camara/partidos'
        
        # Salvar dados completos
        key_completo = f"{base_key}/partidos_completo_{timestamp}.json"
        sucesso_completo = salvar_s3(partidos, bucket, key_completo)
        
        # Estatísticas
        stats = {
            'total_partidos': len(partidos),
            'timestamp': timestamp,
            'arquivos_salvos': {
                'completo': f"s3://{bucket}/{key_completo}" if sucesso_completo else None,
            }
        }
        
        logger.info(f"Processamento concluído: {stats}")
        
        if sucesso_completo:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Dados processados e salvos com sucesso no S3',
                    'stats': stats
                })
            }
        else:
            return {
                'statusCode': 207,
                'body': json.dumps({
                    'message': 'Processamento parcialmente concluído - alguns arquivos falharam',
                    'stats': stats
                })
            }
            
    except Exception as e:
        logger.error(f"Erro geral na Lambda: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Erro interno da função Lambda',
                'error': str(e)
            })
        }