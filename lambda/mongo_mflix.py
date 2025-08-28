import json
import boto3
import pymongo
from datetime import datetime
import logging
from botocore.exceptions import ClientError

# Configuração do logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_secret(secret_name, region_name="us-east-1"):
    """Recupera o secret do AWS Secrets Manager"""
    
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(get_secret_value_response['SecretString'])
        return secret
    except ClientError as e:
        logger.error(f"Erro ao recuperar secret: {e}")
        raise e

def connect_to_mongodb(mongo_uri):
    """Conecta ao MongoDB usando a URI fornecida"""
    try:
        # Tentativa 1 - Configuração básica
        logger.info("Tentativa 1 - Configuração básica")
        client = pymongo.MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=20000,
            socketTimeoutMS=20000,
            maxPoolSize=1,
            retryWrites=True
        )
        
        # Teste a conexão
        client.admin.command('ping')
        logger.info("Conexão básica com MongoDB estabelecida")
        return client
        
    except Exception as e1:
        logger.error(f"Tentativa 1 falhou: {e1}")
        
        try:
            # Tentativa 2 - Com TLS básico
            logger.info("Tentativa 2 - Com TLS básico")
            client = pymongo.MongoClient(
                mongo_uri,
                tls=True,
                serverSelectionTimeoutMS=45000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                maxPoolSize=1
            )
            
            client.admin.command('ping')
            logger.info("Conexão TLS com MongoDB estabelecida")
            return client
            
        except Exception as e2:
            logger.error(f"Tentativa 2 falhou: {e2}")
            
            try:
                # Tentativa 3 - Configuração mínima
                logger.info("Tentativa 3 - Configuração mínima")
                client = pymongo.MongoClient(mongo_uri)
                
                client.admin.command('ping')
                logger.info("Conexão mínima com MongoDB estabelecida")
                return client
                
            except Exception as e3:
                logger.error(f"Todas as tentativas falharam. Último erro: {e3}")
                raise e3

def export_collection_to_s3(collection, collection_name, s3_client, bucket_name, prefix):
    """Exporta uma coleção do MongoDB para o S3"""
    try:
        # Contar documentos primeiro
        doc_count = collection.count_documents({})
        logger.info(f"Coleção {collection_name} possui {doc_count} documentos")
        
        if doc_count == 0:
            logger.warning(f"Coleção {collection_name} está vazia")
            return
        
        # Obter documentos
        all_documents = []
        cursor = collection.find()
        
        for doc in cursor:
            # Converter ObjectId para string para serialização JSON
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            # Converter outros tipos não serializáveis
            for key, value in doc.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    doc[key] = value.isoformat()
            all_documents.append(doc)
        
        # Criar nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{prefix}{collection_name}/{timestamp}_{collection_name}.json"
        
        # Converter para JSON
        json_data = json.dumps(all_documents, indent=2, default=str, ensure_ascii=False)
        
        # Upload para S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=json_data.encode('utf-8'),
            ContentType='application/json'
        )
        
        logger.info(f"Coleção {collection_name} exportada: {len(all_documents)} documentos -> {file_name}")
        
    except Exception as e:
        logger.error(f"Erro ao exportar coleção {collection_name}: {e}")
        raise e

def lambda_handler(event, context):
    """Função principal da Lambda"""
    
    # Configurações
    SECRET_NAME = "dev/mongo/sample_mflix"
    BUCKET_NAME = "dev-lab-02-us-east-2-landing"
    S3_PREFIX = "mflix/"
    DATABASE_NAME = "sample_mflix"
    
    COLLECTIONS = [
        "comments",
        "embedded_movies", 
        "movies",
        "sessions",
        "theaters",
        "users"
    ]
    
    # Log do tempo disponível
    remaining_time = context.get_remaining_time_in_millis() if context else 900000
    logger.info(f"Tempo restante no contexto: {remaining_time}ms")
    
    mongo_client = None
    
    try:
        # 1. Recuperar credenciais do Secrets Manager
        logger.info("=== INICIANDO PROCESSO ===")
        logger.info("Recuperando credenciais do Secrets Manager")
        secret = get_secret(SECRET_NAME)
        mongo_uri = secret['MONGO_URI']
        logger.info("Credenciais recuperadas com sucesso")
        
        # 2. Conectar ao MongoDB
        logger.info("=== CONECTANDO AO MONGODB ===")
        mongo_client = connect_to_mongodb(mongo_uri)
        db = mongo_client[DATABASE_NAME]
        
        # Verificar se conseguimos listar as coleções
        available_collections = db.list_collection_names()
        logger.info(f"Coleções disponíveis no banco: {available_collections}")
        
        # 3. Conectar ao S3
        logger.info("=== CONECTANDO AO S3 ===")
        s3_client = boto3.client('s3')
        
        # 4. Processar cada coleção
        logger.info("=== INICIANDO EXPORTAÇÃO ===")
        results = {}
        
        for collection_name in COLLECTIONS:
            try:
                logger.info(f"Processando coleção: {collection_name}")
                
                # Verificar se a coleção existe
                if collection_name not in available_collections:
                    logger.warning(f"Coleção {collection_name} não encontrada")
                    results[collection_name] = "NOT_FOUND"
                    continue
                
                collection = db[collection_name]
                
                # Exportar coleção
                export_collection_to_s3(
                    collection, 
                    collection_name, 
                    s3_client, 
                    BUCKET_NAME, 
                    S3_PREFIX
                )
                results[collection_name] = "SUCCESS"
                
            except Exception as e:
                logger.error(f"Erro ao processar coleção {collection_name}: {e}")
                results[collection_name] = f"ERROR: {str(e)[:100]}..."
        
        # 5. Preparar resposta de sucesso
        logger.info("=== PROCESSO CONCLUÍDO COM SUCESSO ===")
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Exportação concluída com sucesso',
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'available_collections': available_collections,
                'processed_collections': len([k for k, v in results.items() if v == "SUCCESS"])
            }, ensure_ascii=False)
        }
        
        return response
        
    except Exception as e:
        logger.error(f"=== ERRO GERAL NA FUNÇÃO LAMBDA ===")
        logger.error(f"Erro: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'message': 'Falha na execução da função Lambda'
            })
        }
    
    finally:
        # Garantir que a conexão seja fechada
        if mongo_client:
            try:
                mongo_client.close()
                logger.info("Conexão MongoDB fechada")
            except:
                pass