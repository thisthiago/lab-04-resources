import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime
import time

def obter_lista_deputados():
    """
    Obtém a lista de deputados em exercício da Câmara dos Deputados.
    
    Returns:
        list[dict] or None: Lista de dicionários contendo informações básicas
        dos deputados, incluindo o ideCadastro necessário para obter detalhes.
    """
    url = "https://www.camara.leg.br/SitCamaraWS/Deputados.asmx/ObterDeputados"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/xml, text/xml, */*',
    }
    
    try:
        print("Obtendo lista de deputados...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
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
        
        print(f"Encontrados {len(deputados)} deputados")
        return deputados
        
    except Exception as e:
        print(f"Erro ao obter lista de deputados: {e}")
        return None

def obter_detalhes_deputado(ide_cadastro):
    """
    Obtém detalhes de um deputado usando HTTP GET (como funciona no navegador).
    
    Args:
        ide_cadastro (str): ID do deputado
        
    Returns:
        dict or None: Dicionário com detalhes do deputado
    """
    url = "https://www.camara.leg.br/SitCamaraWS/Deputados.asmx/ObterDetalhesDeputado"
    
    # Parâmetros como na URL que funciona no navegador
    params = {
        'ideCadastro': ide_cadastro,
        'numLegislatura': ''  # Parâmetro vazio
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    }
    
    try:
        print(f"  Obtendo detalhes para ID {ide_cadastro}...")
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"  Erro HTTP {response.status_code} para ID {ide_cadastro}")
            return None
            
        # Verifica se o conteúdo é XML válido
        content = response.content.decode('utf-8').strip()
        if not content:
            print(f"  Resposta vazia para ID {ide_cadastro}")
            return None
        
        # Parse do XML
        root = ET.fromstring(content)
        
        # Encontrar o elemento deputado
        deputado_elem = root.find('.//Deputado')
        if deputado_elem is None:
            print(f"  Elemento 'Deputado' não encontrado para ID {ide_cadastro}")
            return None
        
        # Extrair campos básicos
        detalhes = {}
        campos_basicos = [
            'email', 'nomeProfissao', 'dataNascimento', 'dataFalecimento',
            'ufRepresentacaoAtual', 'situacaoNaLegislaturaAtual', 'ideCadastro',
            'nomeParlamentarAtual', 'nomeCivil', 'sexo'
        ]
        
        for campo in campos_basicos:
            elemento = deputado_elem.find(campo)
            if elemento is not None and elemento.text is not None:
                detalhes[campo] = elemento.text.strip()
            else:
                detalhes[campo] = None
        
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
            detalhes['gabinete'] = {
                'numero': gabinete_elem.findtext('numero'),
                'anexo': gabinete_elem.findtext('anexo'),
                'telefone': gabinete_elem.findtext('telefone')
            }
        else:
            detalhes['gabinete'] = {}
        
        # Comissões (apenas contagem)
        comissoes_elem = deputado_elem.find('comissoes')
        if comissoes_elem is not None and len(comissoes_elem) > 0:
            detalhes['num_comissoes'] = len(comissoes_elem)
        else:
            detalhes['num_comissoes'] = 0
        
        # Períodos de exercício
        periodos_elem = deputado_elem.find('periodosExercicio')
        if periodos_elem is not None and len(periodos_elem) > 0:
            detalhes['num_periodos_exercicio'] = len(periodos_elem)
        else:
            detalhes['num_periodos_exercicio'] = 0
        
        # Histórico de liderança
        historico_lider_elem = deputado_elem.find('historicoLider')
        if historico_lider_elem is not None and len(historico_lider_elem) > 0:
            detalhes['num_liderancas'] = len(historico_lider_elem)
        else:
            detalhes['num_liderancas'] = 0
        
        print(f"  ✓ Detalhes obtidos para ID {ide_cadastro}")
        return detalhes
        
    except requests.exceptions.RequestException as e:
        print(f"  Erro de requisição para ID {ide_cadastro}: {e}")
        return None
    except ET.ParseError as e:
        print(f"  Erro no parse do XML para ID {ide_cadastro}: {e}")
        # Tenta ver o conteúdo que causou o erro
        try:
            print(f"  Conteúdo da resposta: {response.content[:200]}...")
        except:
            pass
        return None
    except Exception as e:
        print(f"  Erro inesperado para ID {ide_cadastro}: {e}")
        return None

def obter_detalhes_completos_deputados(limite=None):
    """
    Obtém lista de deputados e depois detalhes de cada um.
    
    Args:
        limite (int, optional): Número máximo de deputados para processar
    
    Returns:
        list[dict]: Lista completa com informações de todos os deputados
    """
    # Primeiro obtém a lista de deputados
    deputados = obter_lista_deputados()
    
    if not deputados:
        return None
    
    # Aplica limite se especificado
    if limite:
        deputados = deputados[:limite]
        print(f"\nProcessando apenas {limite} deputados (modo teste)")
    
    detalhes_completos = []
    sucessos = 0
    falhas = 0
    
    print(f"\nObtendo detalhes de {len(deputados)} deputados...")
    print("=" * 60)
    
    for i, deputado in enumerate(deputados):
        ide_cadastro = deputado['ideCadastro']
        nome = deputado['nomeParlamentar'] or deputado['nome']
        
        print(f"{i+1}/{len(deputados)} - {nome} (ID: {ide_cadastro})")
        
        # Obtém detalhes do deputado
        detalhes = obter_detalhes_deputado(ide_cadastro)
        
        # Combina informações básicas com detalhes
        if detalhes:
            deputado_completo = {**deputado, **detalhes}
            sucessos += 1
        else:
            # Se não conseguir detalhes, mantém pelo menos as informações básicas
            deputado_completo = deputado
            deputado_completo['detalhes_error'] = 'Não foi possível obter detalhes'
            falhas += 1
        
        detalhes_completos.append(deputado_completo)
        
        # Pequena pausa para não sobrecarregar o servidor
        time.sleep(0.5)
    
    print("=" * 60)
    print(f"Processamento concluído!")
    print(f"Sucessos: {sucessos}")
    print(f"Falhas: {falhas}")
    if len(deputados) > 0:
        print(f"Taxa de sucesso: {(sucessos/len(deputados))*100:.1f}%")
    
    return detalhes_completos

def exportar_dados_completos(dados, nome_arquivo=None):
    """
    Exporta todos os dados para um arquivo JSON.
    
    Args:
        dados (list): Lista com dados completos dos deputados
        nome_arquivo (str, optional): Nome do arquivo de saída
    """
    if nome_arquivo is None:
        data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"deputados_completos_{data_hora}.json"
    
    try:
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        print(f"\nDados exportados com sucesso para: {nome_arquivo}")
        print(f"Total de deputados: {len(dados)}")
        
        return True
    except Exception as e:
        print(f"Erro ao exportar dados: {e}")
        return False

def testar_deputado_especifico(ide_cadastro):
    """
    Testa a obtenção de detalhes para um deputado específico.
    """
    print(f"Testando deputado ID: {ide_cadastro}")
    detalhes = obter_detalhes_deputado(ide_cadastro)
    
    if detalhes:
        print("✓ Detalhes obtidos com sucesso!")
        print(f"Nome: {detalhes.get('nomeParlamentarAtual')}")
        print(f"Partido: {detalhes.get('partidoAtual', {}).get('sigla')}")
        print(f"UF: {detalhes.get('ufRepresentacaoAtual')}")
        print(f"Comissões: {detalhes.get('num_comissoes', 0)}")
        return True
    else:
        print("✗ Falha ao obter detalhes")
        return False

if __name__ == "__main__":
    print("Iniciando coleta de dados dos deputados...")
    print("=" * 60)
    
    # Primeiro testa com um deputado específico que sabemos que funciona
    print("Testando com deputado específico (ID: 141428)...")
    if testar_deputado_especifico("141428"):
        print("\nTeste bem-sucedido! Iniciando coleta completa...")
        print("=" * 60)
        
        # Obtém dados completos (use limite pequeno para teste)
        dados_completos = obter_detalhes_completos_deputados(limite=10)
        
        if dados_completos:
            # Exporta para JSON
            exportar_dados_completos(dados_completos)
            
            # Mostra resumo
            print("\n" + "=" * 60)
            print("RESUMO:")
            print("=" * 60)
            
            com_erro = sum(1 for d in dados_completos if 'detalhes_error' in d)
            sem_erro = len(dados_completos) - com_erro
            
            print(f"Deputados com detalhes completos: {sem_erro}")
            print(f"Deputados apenas com dados básicos: {com_erro}")
            
            # Exemplo dos primeiros deputados com sucesso
            print(f"\nExemplos de deputados com detalhes:")
            exemplos = [d for d in dados_completos if 'detalhes_error' not in d][:3]
            for i, deputado in enumerate(exemplos):
                nome = deputado.get('nomeParlamentarAtual', deputado.get('nomeParlamentar', 'N/A'))
                partido = deputado.get('partidoAtual', {}).get('sigla', deputado.get('partido', 'N/A'))
                uf = deputado.get('ufRepresentacaoAtual', deputado.get('uf', 'N/A'))
                comissoes = deputado.get('num_comissoes', 0)
                print(f"  {i+1}. {nome} ({partido}-{uf}), {comissoes} comissões")
                
        else:
            print("Falha ao obter dados dos deputados")
    else:
        print("Teste falhou. Verifique a conexão.")