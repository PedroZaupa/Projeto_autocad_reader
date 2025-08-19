# scripts/ExtratorTopografia/extrair_tabelas.py

import os
import logging
import ezdxf
import pandas as pd
from collections import defaultdict
import math

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def _agrupar_tabelas_por_proximidade(textos: list, dist_max: float = 100.0) -> list:
    """
    Agrupa entidades de texto em clusters (tabelas) com base na proximidade espacial.

    Args:
        textos (list): Uma lista de tuplas (ponto_insercao, texto).
        dist_max (float): A distância máxima entre dois textos para serem considerados
                          parte da mesma tabela. Este valor pode precisar de ajuste.

    Returns:
        list: Uma lista de clusters, onde cada cluster é uma lista de textos
              que compõem uma tabela.
    """
    if not textos:
        return []

    clusters = []
    visitados = set()

    for i, (ponto1, texto1) in enumerate(textos):
        if i in visitados:
            continue

        novo_cluster = []
        fila = [i]
        visitados.add(i)

        while fila:
            indice_atual = fila.pop(0)
            ponto_atual, texto_atual = textos[indice_atual]
            novo_cluster.append((ponto_atual, texto_atual))

            for j, (ponto_vizinho, texto_vizinho) in enumerate(textos):
                if j not in visitados:
                    # Calcula a distância euclidiana entre os pontos
                    dist = math.sqrt((ponto_atual.x - ponto_vizinho.x)**2 + (ponto_atual.y - ponto_vizinho.y)**2)
                    if dist < dist_max:
                        visitados.add(j)
                        fila.append(j)
        
        clusters.append(novo_cluster)
    
    logging.info(f"Identificados {len(clusters)} agrupamentos de tabelas.")
    return clusters

def extrair_tabelas_por_layer(dxf_path: str, pasta_saida: str, nome_layer: str = "Tabela"):
    """
    Extrai textos de um layer, identifica tabelas separadas por proximidade,
    reconstrói cada uma e salva em abas separadas de um único arquivo Excel.
    """
    nome_base_arquivo = os.path.splitext(os.path.basename(dxf_path))[0]
    logging.info(f"Iniciando extração do layer '{nome_layer}' para: {nome_base_arquivo}.dxf")

    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
    except Exception as e:
        logging.error(f"Não foi possível ler o arquivo DXF: {e}")
        return

    # 1. Coleta todos os textos do layer especificado
    query = f'TEXT MTEXT[layer=="{nome_layer}"]i'
    textos_coletados = [(ent.dxf.insert, ent.plain_text() if ent.dxftype() == "MTEXT" else ent.dxf.text) for ent in msp.query(query)]

    if not textos_coletados:
        logging.warning(f"Nenhum texto encontrado no layer '{nome_layer}'.")
        return

    # 2. Etapa Chave: Agrupa os textos em tabelas separadas
    # O valor de dist_max pode precisar de ajuste dependendo da escala e espaçamento do seu desenho.
    # Um valor maior agrupa mais; um menor separa mais.
    tabelas_separadas = _agrupar_tabelas_por_proximidade(textos_coletados, dist_max=150.0)

    # Prepara o arquivo Excel para salvar múltiplas tabelas (abas)
    pasta_tabelas_saida = os.path.join(pasta_saida, "tabelas_extraidas")
    os.makedirs(pasta_tabelas_saida, exist_ok=True)
    caminho_saida_xlsx = os.path.join(pasta_tabelas_saida, f"{nome_base_arquivo}_tabelas_completas.xlsx")

    with pd.ExcelWriter(caminho_saida_xlsx, engine='openpyxl') as writer:
        # 3. Processa cada tabela (cluster) individualmente
        for idx, tabela in enumerate(tabelas_separadas):
            logging.info(f"Processando Tabela {idx + 1} com {len(tabela)} textos...")
            
            linhas_agrupadas = defaultdict(list)
            tolerancia_y = 1.0

            for ponto, texto in tabela:
                chave_y_agrupada = round(ponto.y / tolerancia_y) * tolerancia_y
                linhas_agrupadas[chave_y_agrupada].append((ponto.x, texto.strip()))

            chaves_y_ordenadas = sorted(linhas_agrupadas.keys(), reverse=True)

            dados_finais_tabela = []
            for y in chaves_y_ordenadas:
                linha = sorted(linhas_agrupadas[y], key=lambda item: item[0])
                texto_da_linha = [item[1] for item in linha]
                dados_finais_tabela.append(texto_da_linha)

            # Salva o DataFrame em uma aba separada no mesmo arquivo Excel
            df = pd.DataFrame(dados_finais_tabela)
            df.to_excel(writer, sheet_name=f'Tabela_{idx + 1}', index=False, header=False)
            logging.info(f"Tabela {idx + 1} salva na aba 'Tabela_{idx + 1}'.")

    logging.info(f"✅ Extração concluída. Todas as tabelas salvas em: {caminho_saida_xlsx}")