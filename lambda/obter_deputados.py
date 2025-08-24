import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import json
import boto3
from datetime import datetime

s3_client = boto3.client('s3')
BUCKET = "dev-lab-02-us-east-2-landing"
BASE_KEY = "camara/deputados"


def obter_deputados_xml(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/xml, text/xml, */*',
    }

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as response:
            xml_content = response.read()
        root = ET.fromstring(xml_content)
        deputados = []

        for dep_elem in root.findall('.//deputado'):
            dep = {
                'ideCadastro': dep_elem.findtext('ideCadastro'),
                'condicao': dep_elem.findtext('condicao'),
                'nome': dep_elem.findtext('nome'),
                'nomeParlamentar': dep_elem.findtext('nomeParlamentar'),
                'urlFoto': dep_elem.findtext('urlFoto'),
                'sexo': dep_elem.findtext('sexo'),
                'uf': dep_elem.findtext('uf'),
                'partido': dep_elem.findtext('partido'),
                'gabinete': dep_elem.findtext('gabinete'),
                'anexo': dep_elem.findtext('anexo'),
                'fone': dep_elem.findtext('fone'),
                'email': dep_elem.findtext('email')
            }
            deputados.append(dep)

        return deputados
    except Exception as e:
        print(f"Erro ao obter dados de {url}: {e}")
        return None


def salvar_no_s3(dados, bucket, key):
    try:
        json_data = json.dumps(dados, ensure_ascii=False, indent=2)
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json_data.encode('utf-8'),
            ContentType='application/json; charset=utf-8'
        )
        return True
    except Exception as e:
        print(f"Erro ao salvar no S3: {e}")
        return False


def lambda_handler(event, context):
    # URLs principal e alternativa
    url_principal = "https://www.camara.leg.br/SitCamaraWS/Deputados.asmx/ObterDeputados"
    url_alternativa = "https://www.camara.gov.br/SitCamaraWS/Deputados.asmx/ObterDeputados"

    deputados = obter_deputados_xml(url_principal)

    if not deputados:
        print("Tentando URL alternativa...")
        deputados = obter_deputados_xml(url_alternativa)

    if not deputados:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Falha ao obter dados dos deputados',
                'error': 'API_ERROR'
            })
        }

    # Gerar nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    key = f"{BASE_KEY}/deputados_{timestamp}.json"

    sucesso = salvar_no_s3(deputados, BUCKET, key)

    if sucesso:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Dados dos deputados processados e salvos com sucesso no S3',
                's3_path': f"s3://{BUCKET}/{key}",
                'total_deputados': len(deputados)
            }, ensure_ascii=False)
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Falha ao salvar os dados no S3',
                's3_path': f"s3://{BUCKET}/{key}"
            })
        }
