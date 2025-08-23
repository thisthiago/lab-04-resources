import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime

def obter_deputados_json():
    """
    Obtém dados dos deputados em exercício da API da Câmara dos Deputados.
    
    Esta função faz uma requisição HTTP GET para o endpoint oficial da Câmara
    dos Deputados, recupera os dados em formato XML e os converte para uma
    estrutura de dicionários Python.
    
    Returns:
        list[dict] or None: Lista de dicionários contendo informações dos deputados,
        onde cada dicionário representa um deputado com os campos:
        - ideCadastro (int): ID único do parlamentar
        - condicao (str): Condição do deputado (Titular ou Suplente)
        - nome (str): Nome civil completo do parlamentar
        - nomeParlamentar (str): Nome de tratamento/apresentação
        - urlFoto (str): URL da foto oficial do deputado
        - sexo (str): Gênero (masculino ou feminino)
        - uf (str): Unidade da Federação de representação
        - partido (str): Sigla do partido político
        - gabinete (str): Número do gabinete
        - anexo (str): Prédio onde está localizado o gabinete
        - fone (str): Telefone do gabinete
        - email (str): E-mail institucional
        
        Retorna None em caso de erro na requisição ou parse dos dados.
    
    Raises:
        requests.exceptions.RequestException: Erros relacionados à requisição HTTP
        xml.etree.ElementTree.ParseError: Erros no parsing do XML
        Exception: Outros erros inesperados
    """
    url = "https://www.camara.leg.br/SitCamaraWS/Deputados.asmx/ObterDeputados"
    
    # Headers para simular um navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        print("Fazendo requisição para a API...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  
        
        print("Processando dados XML...")
        root = ET.fromstring(response.content)
        
        deputados = []
        
        for deputado_elem in root.findall('deputado'):
            deputado = {}
            
            campos = [
                'ideCadastro', 'condicao', 'nome', 'nomeParlamentar', 
                'urlFoto', 'sexo', 'uf', 'partido', 'gabinete', 
                'anexo', 'fone', 'email'
            ]
            
            for campo in campos:
                elemento = deputado_elem.find(campo)
                if elemento is not None and elemento.text is not None:
                    if campo in ['ideCadastro']:
                        try:
                            deputado[campo] = int(elemento.text)
                        except ValueError:
                            deputado[campo] = elemento.text.strip()
                    else:
                        deputado[campo] = elemento.text.strip()
                else:
                    deputado[campo] = None
            
            deputados.append(deputado)
        
        return deputados
        
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição HTTP: {e}")
        return None
    except ET.ParseError as e:
        print(f"Erro no parse do XML: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return None

def exportar_para_json(deputados, nome_arquivo=None):
    """
    Exporta os dados dos deputados para arquivo JSON com codificação UTF-8.
    
    Args:
        deputados (list[dict]): Lista de dicionários contendo dados dos deputados
        nome_arquivo (str, optional): Nome do arquivo de destino. Se não fornecido,
            será gerado automaticamente no formato 'deputados_AAAAMMDD_HHMMSS.json'
    
    Returns:
        bool: True se a exportação foi bem-sucedida, False caso contrário
    
    Notes:
        O arquivo é salvo com indentação de 2 espaços e caracteres Unicode
        preservados (ensure_ascii=False).
    
    Examples:
        >>> deputados = obter_deputados_json()
        >>> exportar_para_json(deputados, 'meus_deputados.json')
        Dados exportados com sucesso para: meus_deputados.json
        True
    """
    if nome_arquivo is None:
        data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"deputados_{data_hora}.json"
    
    try:
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            json.dump(deputados, f, ensure_ascii=False, indent=2)
        
        print(f"Dados exportados com sucesso para: {nome_arquivo}")
        return True
    except Exception as e:
        print(f"Erro ao exportar para JSON: {e}")
        return False


def obter_deputados_alternativo():
    """
    Alternativa para obtenção de dados de deputados usando endpoint secundário.
    
    Esta função tenta acessar uma URL alternativa da API da Câmara dos Deputados
    quando o endpoint principal retorna erro. Utiliza método simplificado de
    parsing XML com findtext para maior robustez.
    
    Returns:
        list[dict] or None: Lista de dicionários com dados dos deputados no
        mesmo formato da função principal, ou None em caso de falha.
    
    Notes:
        Utiliza a URL 'www.camara.gov.br' como alternativa à 'www.camara.leg.br'
        que pode estar com restrições de acesso.
    """
    url_alternativa = "https://www.camara.gov.br/SitCamaraWS/Deputados.asmx/ObterDeputados"
    
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
        deputados = []
        
        for deputado_elem in root.findall('.//deputado'):
            deputado = {
                'ideCadastro': deputado_elem.findtext('ideCadastro'),
                'condicao': deputado_elem.findtext('condicao'),
                'nome': deputado_elem.findtext('nome'),
                'nomeParlamentar': deputado_elem.findtext('nomeParlamentar'),
                'urlFoto': deputado_elem.findtext('urlFoto'),
                'sexo': deputado_elem.findtext('sexo'),
                'uf': deputado_elem.findtext('uf'),
                'partido': deputado_elem.findtext('partido'),
                'gabinete': deputado_elem.findtext('gabinete'),
                'anexo': deputado_elem.findtext('anexo'),
                'fone': deputado_elem.findtext('fone'),
                'email': deputado_elem.findtext('email')
            }
            deputados.append(deputado)
        
        return deputados
        
    except Exception as e:
        print(f"Erro na URL alternativa: {e}")
        return None

if __name__ == "__main__":
    # Primeira tentativa com a URL principal
    deputados = obter_deputados_json()
    
    # Se falhar, tentar URL alternativa
    if not deputados:
        print("Tentando método alternativo...")
        deputados = obter_deputados_alternativo()
    
    if deputados:
        print(f"Dados de {len(deputados)} deputados obtidos com sucesso!")
        
        # Exportar para JSON
        exportar_para_json(deputados)
        
        # Mostrar informações básicas
        print("\nResumo dos dados:")
        print(f"Total de deputados: {len(deputados)}")
        
        # Contar por partido
        partidos = {}
        for deputado in deputados:
            partido = deputado.get('partido', 'N/A')
            partidos[partido] = partidos.get(partido, 0) + 1
        
        print("Distribuição por partido:")
        for partido, quantidade in sorted(partidos.items(), key=lambda x: x[1], reverse=True):
            print(f"  {partido}: {quantidade}")
        
        # Contar por UF
        ufs = {}
        for deputado in deputados:
            uf = deputado.get('uf', 'N/A')
            ufs[uf] = ufs.get(uf, 0) + 1
        
        print("\nDistribuição por UF:")
        for uf, quantidade in sorted(ufs.items(), key=lambda x: x[1], reverse=True):
            print(f"  {uf}: {quantidade}")
            
        # Mostrar alguns exemplos
        print("\nPrimeiros 5 deputados:")
        for i, deputado in enumerate(deputados[:5]):
            print(f"  {i+1}. {deputado.get('nomeParlamentar', 'N/A')} ({deputado.get('partido', 'N/A')}-{deputado.get('uf', 'N/A')})")
            
    else:
        print("Falha ao obter dados dos deputados após todas as tentativas.")
        print("Isso pode ser devido a:")
        print("1. Problemas de conexão com a internet")
        print("2. Mudanças na API da Câmara dos Deputados")
        print("3. Restrições de acesso do servidor")