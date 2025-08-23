import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime

def obter_partidos_json():
    """
    Obtém dados dos partidos políticos da API da Câmara dos Deputados.
    
    Esta função faz uma requisição HTTP GET para o endpoint oficial da Câmara
    dos Deputados, recupera os dados em formato XML e os converte para uma
    estrutura de dicionários Python.
    
    Returns:
        list[dict] or None: Lista de dicionários contendo informações dos partidos,
        onde cada dicionário representa um partido com os campos:
        - idPartido (str): ID único do partido
        - siglaPartido (str): Sigla do partido
        - nomePartido (str): Nome completo do partido
        - dataCriacao (str): Data de criação do partido
        - dataExtincao (str): Data de extinção do partido (se aplicável)
        
        Retorna None em caso de erro na requisição ou parse dos dados.
    
    Raises:
        requests.exceptions.RequestException: Erros relacionados à requisição HTTP
        xml.etree.ElementTree.ParseError: Erros no parsing do XML
        Exception: Outros erros inesperados
    """
    url = "https://www.camara.leg.br/SitCamaraWS/Deputados.asmx/ObterPartidosCD"
    
    # Headers para simular um navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        print("Fazendo requisição para a API de partidos...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  
        
        print("Processando dados XML...")
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
        print(f"Erro na requisição HTTP: {e}")
        return None
    except ET.ParseError as e:
        print(f"Erro no parse do XML: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return None

def exportar_partidos_para_json(partidos, nome_arquivo=None):
    """
    Exporta os dados dos partidos para arquivo JSON com codificação UTF-8.
    
    Args:
        partidos (list[dict]): Lista de dicionários contendo dados dos partidos
        nome_arquivo (str, optional): Nome do arquivo de destino. Se não fornecido,
            será gerado automaticamente no formato 'partidos_AAAAMMDD_HHMMSS.json'
    
    Returns:
        bool: True se a exportação foi bem-sucedida, False caso contrário
    
    Notes:
        O arquivo é salvo com indentação de 2 espaços e caracteres Unicode
        preservados (ensure_ascii=False).
    """
    if nome_arquivo is None:
        data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"partidos_{data_hora}.json"
    
    try:
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            json.dump(partidos, f, ensure_ascii=False, indent=2)
        
        print(f"Dados exportados com sucesso para: {nome_arquivo}")
        return True
    except Exception as e:
        print(f"Erro ao exportar para JSON: {e}")
        return False

def obter_partidos_alternativo():
    """
    Alternativa para obtenção de dados de partidos usando endpoint secundário.
    
    Esta função tenta acessar uma URL alternativa da API da Câmara dos Deputados
    quando o endpoint principal retorna erro.
    
    Returns:
        list[dict] or None: Lista de dicionários com dados dos partidos no
        mesmo formato da função principal, ou None em caso de falha.
    """
    url_alternativa = "https://www.camara.gov.br/SitCamaraWS/Deputados.asmx/ObterPartidosCD"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/xml, text/xml, */*',
    }
    
    try:
        print("Tentando URL alternativa...")
        response = requests.get(url_alternativa, headers=headers, timeout=30)
        response.raise_for_status()
        
        print("Processando dados XML da URL alternativa...")
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
        print(f"Erro na URL alternativa: {e}")
        return None

def filtrar_partidos_ativos(partidos):
    """
    Filtra apenas os partidos ativos (sem data de extinção).
    
    Args:
        partidos (list[dict]): Lista completa de partidos
    
    Returns:
        list[dict]: Lista de partidos ativos
    """
    return [partido for partido in partidos if partido.get('dataExtincao') is None]

def filtrar_partidos_extintos(partidos):
    """
    Filtra apenas os partidos extintos (com data de extinção).
    
    Args:
        partidos (list[dict]): Lista completa de partidos
    
    Returns:
        list[dict]: Lista de partidos extintos
    """
    return [partido for partido in partidos if partido.get('dataExtincao') is not None]

if __name__ == "__main__":
    partidos = obter_partidos_json()
    
    if not partidos:
        print("Tentando método alternativo...")
        partidos = obter_partidos_alternativo()
    
    if partidos:
        print(f"Dados de {len(partidos)} partidos obtidos com sucesso!")
        
        exportar_partidos_para_json(partidos)
        
        partidos_ativos = filtrar_partidos_ativos(partidos)
        partidos_extintos = filtrar_partidos_extintos(partidos)
        
        print("\nResumo dos dados:")
        print(f"Total de partidos: {len(partidos)}")
        print(f"Partidos ativos: {len(partidos_ativos)}")
        print(f"Partidos extintos: {len(partidos_extintos)}")
        
        print("\nPartidos ativos:")
        for partido in sorted(partidos_ativos, key=lambda x: x.get('siglaPartido', '')):
            print(f"  {partido.get('siglaPartido', 'N/A')}: {partido.get('nomePartido', 'N/A')}")
        
        if partidos_extintos:
            print(f"\nPrimeiros 5 partidos extintos:")
            for i, partido in enumerate(partidos_extintos[:5]):
                print(f"  {i+1}. {partido.get('siglaPartido', 'N/A')}: {partido.get('nomePartido', 'N/A')} (Extinto em: {partido.get('dataExtincao', 'N/A')})")
            
    else:
        print("Falha ao obter dados dos partidos após todas as tentativas.")
        print("Isso pode ser devido a:")
        print("1. Problemas de conexão com a internet")
        print("2. Mudanças na API da Câmara dos Deputados")
        print("3. Restrições de acesso do servidor")