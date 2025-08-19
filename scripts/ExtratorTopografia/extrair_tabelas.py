# scripts/ExtratorTopografia/extrair_tabelas.py

import os
import logging
import ezdxf
import pandas as pd
from collections import defaultdict

# Configuração do logging para melhor visualização do processo
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def extrair_tabelas_por_layer(dxf_path: str, pasta_saida: str, nome_layer: str = "Tabela"):
    """
    Extrai textos de um layer específico no modelspace, reconstrói a estrutura
    da tabela baseando-se na posição dos textos e salva em Excel.

    Args:
        dxf_path (str): Caminho para o arquivo DXF.
        pasta_saida (str): Pasta onde os resultados serão salvos.
        nome_layer (str): Nome do layer que contém os dados da tabela.
    """
    nome_base_arquivo = os.path.splitext(os.path.basename(dxf_path))[0]
    logging.info(f"Iniciando extração de tabela do layer '{nome_layer}' para o arquivo: {nome_base_arquivo}.dxf")

    if not os.path.exists(dxf_path):
        logging.error(f"Arquivo DXF não encontrado: {dxf_path}")
        return

    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
    except Exception as e:
        logging.error(f"Não foi possível ler o arquivo DXF: {e}")
        return

    # 1. Consulta eficiente para selecionar apenas textos (TEXT, MTEXT) no layer especificado
    # A sintaxe '[layer=="{nome_layer}"]i' faz a busca ignorando maiúsculas/minúsculas
    query = f'TEXT MTEXT[layer=="{nome_layer}"]i'
    textos_tabela = msp.query(query)

    if not textos_tabela:
        logging.warning(f"Nenhum texto encontrado no layer '{nome_layer}'. Verifique o nome do layer no arquivo DWG.")
        return

    logging.info(f"Encontrados {len(textos_tabela)} elementos de texto no layer '{nome_layer}'.")

    # 2. Agrupamento dos textos por linha (coordenada Y)
    linhas_agrupadas = defaultdict(list)
    tolerancia_y = 1.0  # Tolerância para agrupar textos que não estão perfeitamente alinhados

    for entidade_texto in textos_tabela:
        try:
            texto = entidade_texto.plain_text() if entidade_texto.dxftype() == "MTEXT" else entidade_texto.dxf.text
            ponto_insercao = entidade_texto.dxf.insert
            
            # Agrupa pela coordenada Y com tolerância
            chave_y_agrupada = round(ponto_insercao.y / tolerancia_y) * tolerancia_y
            
            # Adiciona a coordenada X e o texto para ordenação posterior
            linhas_agrupadas[chave_y_agrupada].append((ponto_insercao.x, texto.strip()))

        except (AttributeError, ValueError) as e:
            logging.warning(f"Ignorando uma entidade de texto com erro: {e}")

    if not linhas_agrupadas:
        logging.error("Falha ao agrupar os textos em linhas.")
        return

    # 3. Ordenação das linhas e colunas para montar a tabela
    # Ordena as linhas de cima para baixo (Y decrescente)
    chaves_y_ordenadas = sorted(linhas_agrupadas.keys(), reverse=True)

    dados_finais_tabela = []
    for y in chaves_y_ordenadas:
        linha = linhas_agrupadas[y]
        # Ordena as colunas da esquerda para a direita (X crescente)
        linha_ordenada = sorted(linha, key=lambda item: item[0])
        # Extrai apenas o texto já ordenado
        texto_da_linha = [item[1] for item in linha_ordenada]
        dados_finais_tabela.append(texto_da_linha)

    # 4. Salvando os dados em um arquivo Excel
    try:
        df = pd.DataFrame(dados_finais_tabela)

        # Opcional: Tenta usar a primeira linha como cabeçalho, se fizer sentido
        if not df.empty and len(df.columns) > 1:
            # Garante que os nomes das colunas sejam strings únicos
            header = df.iloc[0]
            df.columns = [str(h) for h in header]
            df = df.iloc[1:].reset_index(drop=True)

        # Cria a pasta de saída se ela não existir
        pasta_tabelas_saida = os.path.join(pasta_saida, "tabelas_extraidas")
        os.makedirs(pasta_tabelas_saida, exist_ok=True)
        
        caminho_saida_xlsx = os.path.join(pasta_tabelas_saida, f"{nome_base_arquivo}_layer_{nome_layer}.xlsx")
        
        df.to_excel(caminho_saida_xlsx, index=False)
        logging.info(f"✅ Tabela extraída com sucesso e salva em: {caminho_saida_xlsx}")

    except Exception as e:
        logging.error(f"Erro ao salvar o arquivo Excel: {e}")

# Para testar este script isoladamente, você precisaria de um arquivo de configuração
# e um arquivo DXF. A execução principal continua sendo pelo `main.py`.