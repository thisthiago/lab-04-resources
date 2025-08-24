import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
import json
import boto3
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lock para logging thread-safe
log_lock = threading.Lock()

def obter_lista_deputados():
    """Obtém lista de deputados"""
    url = "https://www.camara.leg.br/SitCamaraWS/Deputados.asmx/ObterDeputados"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/xml, text/xml, */*',
    }

    try:
        logger.info("Obtendo lista de deputados...")
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as response:
            xml_content = response.read()

        root = ET.fromstring(xml_content)
        deputados = []

        for deputado_elem in root.findall('deputado'):
            deputado = {
                'ideCadastro': deputado_elem.findtext('ideCadastro'),
                'nome': deputado_elem.findtext('nome'),
                'nomeParlamentar': deputado_elem.findtext('nomeParlamentar'),
                'partido': deputado_elem.findtext('partido'),
                'uf': deputado_elem.findtext('uf'),
                'urlFoto': deputado_elem.findtext('urlFoto'),
                'condicao': deputado_elem.findtext('condicao'),
                'gabinete': deputado_elem.findtext('gabinete'),
                'anexo': deputado_elem.findtext('anexo'),
                'fone': deputado_elem.findtext('fone'),
                'email': deputado_elem.findtext('email')
            }
            deputados.append(deputado)

        logger.info(f"Encontrados {len(deputados)} deputados")
        return deputados

    except Exception as e:
        logger.error(f"Erro ao obter lista de deputados: {e}")
        return None

def obter_detalhes_deputado_thread_safe(deputado, contador_global):
    """Obtém detalhes de um deputado específico (thread-safe)"""
    ide_cadastro = deputado['ideCadastro']
    nome = deputado['nomeParlamentar'] or deputado['nome']
    thread_id = threading.current_thread().name
    
    url = "https://www.camara.leg.br/SitCamaraWS/Deputados.asmx/ObterDetalhesDeputado"
    
    params = {
        'ideCadastro': ide_cadastro,
        'numLegislatura': ''
    }
    
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    }
    
    try:
        req = urllib.request.Request(full_url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as response:
            status = response.getcode()
            if status != 200:
                with log_lock:
                    contador_global['processados'] += 1
                    logger.warning(f"[{thread_id}] HTTP {status} para {nome} (ID: {ide_cadastro}) - {contador_global['processados']}/{contador_global['total']}")
                return {
                    **deputado,
                    'detalhes_error': f'HTTP {status}',
                    'error_type': 'http_error'
                }
            
            content = response.read().decode('utf-8').strip()
        
        if not content:
            with log_lock:
                contador_global['processados'] += 1
                logger.warning(f"[{thread_id}] Resposta vazia para {nome} (ID: {ide_cadastro}) - {contador_global['processados']}/{contador_global['total']}")
            return {
                **deputado,
                'detalhes_error': 'Resposta vazia',
                'error_type': 'empty_response'
            }
        
        # Parse do XML
        root = ET.fromstring(content)
        deputado_elem = root.find('.//Deputado')
        
        if deputado_elem is None:
            with log_lock:
                contador_global['processados'] += 1
                logger.warning(f"[{thread_id}] Elemento 'Deputado' não encontrado para {nome} (ID: {ide_cadastro}) - {contador_global['processados']}/{contador_global['total']}")
            return {
                **deputado,
                'detalhes_error': 'Elemento Deputado não encontrado',
                'error_type': 'parse_error'
            }
        
        # Extrair detalhes
        detalhes = {}
        campos_basicos = [
            'email', 'nomeProfissao', 'dataNascimento', 'dataFalecimento',
            'ufRepresentacaoAtual', 'situacaoNaLegislaturaAtual', 'ideCadastro',
            'nomeParlamentarAtual', 'nomeCivil', 'sexo'
        ]
        
        for campo in campos_basicos:
            elemento = deputado_elem.find(campo)
            detalhes[campo] = elemento.text.strip() if elemento is not None and elemento.text else None
        
        # Partido atual
        partido_elem = deputado_elem.find('partidoAtual')
        if partido_elem is not None:
            detalhes['partidoAtual'] = {
                'sigla': partido_elem.findtext('sigla'),
                'nome': partido_elem.findtext('nome')
            }
        else:
            detalhes['partidoAtual'] = {}
        
        # Gabinete
        gabinete_elem = deputado_elem.find('gabinete')
        if gabinete_elem is not None:
            detalhes['gabinete_detalhes'] = {
                'numero': gabinete_elem.findtext('numero'),
                'anexo': gabinete_elem.findtext('anexo'),
                'telefone': gabinete_elem.findtext('telefone')
            }
        else:
            detalhes['gabinete_detalhes'] = {}
        
        # Contadores
        comissoes_elem = deputado_elem.find('comissoes')
        detalhes['num_comissoes'] = len(comissoes_elem) if comissoes_elem is not None else 0
        
        periodos_elem = deputado_elem.find('periodosExercicio')
        detalhes['num_periodos_exercicio'] = len(periodos_elem) if periodos_elem is not None else 0
        
        historico_lider_elem = deputado_elem.find('historicoLider')
        detalhes['num_liderancas'] = len(historico_lider_elem) if historico_lider_elem is not None else 0
        
        # Combinar dados básicos com detalhes
        deputado_completo = {**deputado, **detalhes}
        deputado_completo['detalhes_success'] = True
        deputado_completo['processed_by_thread'] = thread_id
        
        # Log de sucesso (a cada 20 sucessos)
        with log_lock:
            contador_global['processados'] += 1
            contador_global['sucessos'] += 1
            if contador_global['sucessos'] % 20 == 0:
                logger.info(f"[{thread_id}] ✓ {nome} processado com sucesso - {contador_global['sucessos']} sucessos de {contador_global['processados']} processados")
        
        return deputado_completo
        
    except urllib.error.URLError as e:
        with log_lock:
            contador_global['processados'] += 1
            logger.error(f"[{thread_id}] URL Error para {nome} (ID: {ide_cadastro}): {e} - {contador_global['processados']}/{contador_global['total']}")
        return {
            **deputado,
            'detalhes_error': f'URL Error: {str(e)}',
            'error_type': 'url_error'
        }
    except ET.ParseError as e:
        with log_lock:
            contador_global['processados'] += 1
            logger.error(f"[{thread_id}] Parse Error para {nome} (ID: {ide_cadastro}): {e} - {contador_global['processados']}/{contador_global['total']}")
        return {
            **deputado,
            'detalhes_error': f'Parse error: {str(e)}',
            'error_type': 'xml_parse_error'
        }
    except Exception as e:
        with log_lock:
            contador_global['processados'] += 1
            logger.error(f"[{thread_id}] Erro inesperado para {nome} (ID: {ide_cadastro}): {e} - {contador_global['processados']}/{contador_global['total']}")
        return {
            **deputado,
            'detalhes_error': f'Unexpected error: {str(e)}',
            'error_type': 'unexpected_error'
        }

def obter_todos_detalhes_paralelo(deputados, max_workers=10):
    """Obtém detalhes de todos os deputados usando ThreadPoolExecutor"""
    logger.info(f"Iniciando processamento paralelo com {max_workers} workers para {len(deputados)} deputados")
    
    # Contador global compartilhado entre threads
    contador_global = {
        'processados': 0,
        'sucessos': 0,
        'total': len(deputados)
    }
    
    resultados = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="DeputadoWorker") as executor:
        # Submeter todas as tarefas
        future_to_deputado = {
            executor.submit(obter_detalhes_deputado_thread_safe, deputado, contador_global): deputado 
            for deputado in deputados
        }
        
        # Coletar resultados conforme completam
        for future in as_completed(future_to_deputado):
            deputado = future_to_deputado[future]
            try:
                resultado = future.result()
                resultados.append(resultado)
            except Exception as exc:
                nome = deputado['nomeParlamentar'] or deputado['nome']
                logger.error(f"Deputado {nome} gerou exceção: {exc}")
                # Adicionar como erro
                resultado_erro = {
                    **deputado,
                    'detalhes_error': f'Future exception: {str(exc)}',
                    'error_type': 'future_exception'
                }
                resultados.append(resultado_erro)
    
    elapsed_time = time.time() - start_time
    logger.info(f"Processamento paralelo concluído em {elapsed_time:.2f} segundos")
    logger.info(f"Total: {len(resultados)}, Sucessos: {contador_global['sucessos']}, Erros: {len(resultados) - contador_global['sucessos']}")
    
    return resultados

def analisar_resultados(resultados):
    """Analisa os resultados e separa por categorias"""
    sucessos = []
    erros = []
    contadores_erro = {}
    
    for resultado in resultados:
        if resultado.get('detalhes_success'):
            sucessos.append(resultado)
        else:
            erros.append(resultado)
            error_type = resultado.get('error_type', 'unknown')
            contadores_erro[error_type] = contadores_erro.get(error_type, 0) + 1
    
    return sucessos, erros, contadores_erro

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

def lambda_handler(event, context):
    try:
        # Configurações
        bucket = 'dev-lab-02-us-east-2-landing'
        base_key = 'camara/detalhesDeputados'
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Configurações de paralelismo e limite
        max_workers = event.get('max_workers', 20) if event else 8  # Reduzido para evitar sobrecarregar a API
        limite = event.get('limite', None) if event else None
        
        logger.info(f"Configurações - Limite: {limite}, Max workers: {max_workers}")
        
        # Obter lista de deputados
        logger.info("=== FASE 1: Obtendo lista de deputados ===")
        deputados = obter_lista_deputados()
        
        if not deputados:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Falha ao obter lista de deputados',
                    'error': 'API_ERROR'
                })
            }
        
        # Aplicar limite se especificado
        if limite:
            deputados = deputados[:limite]
            logger.info(f"Aplicado limite de {limite} deputados")
        
        # Obter detalhes de todos os deputados em paralelo
        logger.info("=== FASE 2: Obtendo detalhes em paralelo ===")
        resultados = obter_todos_detalhes_paralelo(deputados, max_workers)
        
        if not resultados:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Falha ao processar deputados',
                    'error': 'PROCESSING_ERROR'
                })
            }
        
        # Analisar resultados
        logger.info("=== FASE 3: Analisando resultados ===")
        sucessos, erros, contadores_erro = analisar_resultados(resultados)
        
        logger.info(f"Análise concluída - Sucessos: {len(sucessos)}, Erros: {len(erros)}")
        
        # Salvar arquivos no S3
        logger.info("=== FASE 4: Salvando arquivos no S3 ===")
        
        # 1. Arquivo unificado (TODOS os resultados)
        key_unificado = f"{base_key}/deputados_unificado_{timestamp}.json"
        sucesso_unificado = salvar_s3(resultados, bucket, key_unificado)
        
        # 2. Apenas sucessos
        key_sucessos = f"{base_key}/deputados_sucessos_{timestamp}.json"
        sucesso_sucessos = salvar_s3(sucessos, bucket, key_sucessos) if sucessos else True
        
        # 3. Apenas erros (para análise)
        key_erros = f"{base_key}/deputados_erros_{timestamp}.json"
        sucesso_erros = salvar_s3(erros, bucket, key_erros) if erros else True
        
        # 4. Resumo compacto (apenas campos essenciais dos sucessos)
        deputados_resumo = []
        for resultado in sucessos:
            resumo = {
                'ideCadastro': resultado.get('ideCadastro'),
                'nome': resultado.get('nome'),
                'nomeParlamentar': resultado.get('nomeParlamentar'),
                'nomeParlamentarAtual': resultado.get('nomeParlamentarAtual'),
                'partido': resultado.get('partido'),
                'partidoAtual': resultado.get('partidoAtual', {}),
                'uf': resultado.get('uf'),
                'ufRepresentacaoAtual': resultado.get('ufRepresentacaoAtual'),
                'condicao': resultado.get('condicao'),
                'situacaoNaLegislaturaAtual': resultado.get('situacaoNaLegislaturaAtual'),
                'email': resultado.get('email'),
                'sexo': resultado.get('sexo'),
                'dataNascimento': resultado.get('dataNascimento'),
                'num_comissoes': resultado.get('num_comissoes', 0),
                'num_periodos_exercicio': resultado.get('num_periodos_exercicio', 0),
                'num_liderancas': resultado.get('num_liderancas', 0)
            }
            deputados_resumo.append(resumo)
        
        key_resumo = f"{base_key}/deputados_resumo_{timestamp}.json"
        sucesso_resumo = salvar_s3(deputados_resumo, bucket, key_resumo)
        
        # Compilar estatísticas detalhadas
        stats = {
            'timestamp': timestamp,
            'configuracoes': {
                'limite_aplicado': limite,
                'max_workers': max_workers,
                'total_solicitados': len(deputados),
                'total_processados': len(resultados)
            },
            'resultados': {
                'total_deputados': len(resultados),
                'sucessos': len(sucessos),
                'erros': len(erros),
                'taxa_sucesso': f"{(len(sucessos)/len(resultados)*100):.1f}%" if resultados else "0%"
            },
            'tipos_erro': contadores_erro,
            'arquivos_salvos': {
                'unificado': f"s3://{bucket}/{key_unificado}" if sucesso_unificado else None,
                'sucessos': f"s3://{bucket}/{key_sucessos}" if sucesso_sucessos else None,
                'erros': f"s3://{bucket}/{key_erros}" if sucesso_erros and erros else None,
                'resumo': f"s3://{bucket}/{key_resumo}" if sucesso_resumo else None
            }
        }
        
        # Exemplos de sucessos
        exemplos_sucessos = []
        for deputado in sucessos[:5]:
            nome = deputado.get('nomeParlamentarAtual', deputado.get('nomeParlamentar', 'N/A'))
            partido = deputado.get('partidoAtual', {}).get('sigla', deputado.get('partido', 'N/A'))
            uf = deputado.get('ufRepresentacaoAtual', deputado.get('uf', 'N/A'))
            comissoes = deputado.get('num_comissoes', 0)
            exemplos_sucessos.append(f"{nome} ({partido}-{uf}), {comissoes} comissões")
        
        if exemplos_sucessos:
            stats['exemplos_sucessos'] = exemplos_sucessos
        
        # Exemplos de erros
        exemplos_erros = []
        for erro in erros[:3]:
            nome = erro.get('nomeParlamentar', erro.get('nome', 'N/A'))
            tipo_erro = erro.get('error_type', 'unknown')
            msg_erro = erro.get('detalhes_error', 'N/A')
            exemplos_erros.append(f"{nome}: {tipo_erro} - {msg_erro}")
        
        if exemplos_erros:
            stats['exemplos_erros'] = exemplos_erros
        
        logger.info("=== PROCESSAMENTO CONCLUÍDO ===")
        logger.info(f"Estatísticas finais: {json.dumps(stats, ensure_ascii=False, indent=2)}")
        
        # Determinar status da resposta
        todos_salvos = sucesso_unificado and sucesso_sucessos and sucesso_erros and sucesso_resumo
        
        if todos_salvos:
            status_code = 200
            message = 'Processamento paralelo concluído com sucesso - todos os arquivos salvos no S3'
        else:
            status_code = 207
            message = 'Processamento concluído com falhas parciais no salvamento de arquivos'
        
        return {
            'statusCode': status_code,
            'body': json.dumps({
                'message': message,
                'stats': stats
            }, ensure_ascii=False, indent=2)
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