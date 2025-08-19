# scripts/ExtratorTopografia/extrair_tabelas.py

import os
import logging
import ezdxf
import pandas as pd
from collections import defaultdict
import math
import numpy as np

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def _agrupar_tabelas_por_proximidade(textos: list, dist_max: float) -> list:
    """Fase 1: Agrupa textos em clusters com base na proximidade espacial geral."""
    if not textos: return []
    clusters, visitados = [], set()
    for i, (ponto1, texto1) in enumerate(textos):
        if i in visitados: continue
        novo_cluster, fila = [], [i]
        visitados.add(i)
        while fila:
            idx_atual = fila.pop(0)
            ponto_atual, texto_atual = textos[idx_atual]
            novo_cluster.append((ponto_atual, texto_atual))
            for j, (ponto_vizinho, texto_vizinho) in enumerate(textos):
                if j not in visitados:
                    dist = math.hypot(ponto_atual.x - ponto_vizinho.x, ponto_atual.y - ponto_vizinho.y)
                    if dist < dist_max:
                        visitados.add(j)
                        fila.append(j)
        clusters.append(novo_cluster)
    logging.info(f"Fase 1: Identificados {len(clusters)} agrupamentos de proximidade.")
    return clusters

def _dividir_cluster_por_gaps(cluster: list, eixo: str, tolerancia: float, multiplicador_gap: float) -> list:
    """Divide um cluster com base em grandes vãos em um determinado eixo ('x' ou 'y')."""
    if len(cluster) < 2: return [cluster]

    # Agrupa textos por posição aproximada no eixo para encontrar as coordenadas das linhas/colunas
    posicoes_agrupadas = defaultdict(list)
    for ponto, texto in cluster:
        coordenada = ponto.y if eixo == 'y' else ponto.x
        chave = round(coordenada / tolerancia) * tolerancia
        posicoes_agrupadas[chave].append((ponto, texto))
        
    if len(posicoes_agrupadas) < 2: return [cluster]

    posicoes = sorted(posicoes_agrupadas.keys())
    gaps = np.diff(posicoes)
    
    if len(gaps) == 0: return [cluster]
    
    mediana_gap = np.median(gaps)
    if mediana_gap == 0: return [cluster]

    limite_gap = mediana_gap * multiplicador_gap
    
    sub_clusters, cluster_atual = [], []
    for i, pos in enumerate(posicoes):
        cluster_atual.extend(posicoes_agrupadas[pos])
        if i < len(gaps) and gaps[i] > limite_gap:
            sub_clusters.append(cluster_atual)
            cluster_atual = []
            
    sub_clusters.append(cluster_atual)
    
    if len(sub_clusters) > 1:
        logging.info(f"Cluster dividido em {len(sub_clusters)} sub-grupos pela análise de vão no eixo '{eixo}'.")
        
    return sub_clusters

def extrair_tabelas_por_layer(
    dxf_path: str, 
    pasta_saida: str, 
    nome_layer: str = "Tabela",
    dist_max: float = 150.0,
    tolerancia_y: float = 2.5,
    multiplicador_gap_y: float = 4.0,
    tolerancia_x: float = 5.0,
    multiplicador_gap_x: float = 2.0
):
    """
    Extrai tabelas de um layer, com lógica de cluster e divisão por vãos verticais e horizontais.
    """
    nome_base_arquivo = os.path.splitext(os.path.basename(dxf_path))[0]
    logging.info(f"Iniciando extração do layer '{nome_layer}' para: {nome_base_arquivo}.dxf")

    try: doc = ezdxf.readfile(dxf_path); msp = doc.modelspace()
    except Exception as e: logging.error(f"Não foi possível ler o arquivo DXF: {e}"); return

    query = f'TEXT MTEXT[layer=="{nome_layer}"]i'
    textos_coletados = [(ent.dxf.insert, ent.plain_text() if ent.dxftype() == "MTEXT" else ent.dxf.text) for ent in msp.query(query)]

    if not textos_coletados: logging.warning(f"Nenhum texto encontrado no layer '{nome_layer}'."); return

    # FASE 1: Agrupar por proximidade geral
    clusters_iniciais = _agrupar_tabelas_por_proximidade(textos_coletados, dist_max)

    # FASE 2: Refinar clusters, primeiro dividindo por vãos verticais e depois horizontais
    tabelas_finais = []
    for cluster in clusters_iniciais:
        sub_clusters_verticais = _dividir_cluster_por_gaps(cluster, 'y', tolerancia_y, multiplicador_gap_y)
        for sub_cluster_v in sub_clusters_verticais:
            sub_clusters_horizontais = _dividir_cluster_por_gaps(sub_cluster_v, 'x', tolerancia_x, multiplicador_gap_x)
            tabelas_finais.extend(sub_clusters_horizontais)
    
    logging.info(f"Processamento finalizado. Total de {len(tabelas_finais)} tabelas encontradas.")

    pasta_tabelas_saida = os.path.join(pasta_saida, "tabelas_extraidas")
    os.makedirs(pasta_tabelas_saida, exist_ok=True)
    caminho_saida_xlsx = os.path.join(pasta_tabelas_saida, f"{nome_base_arquivo}_tabelas_finais.xlsx")

    with pd.ExcelWriter(caminho_saida_xlsx, engine='openpyxl') as writer:
        # Ordena as tabelas finais pela posição (de cima para baixo, depois esquerda para direita)
        tabelas_finais.sort(key=lambda t: (-max(p.y for p, _ in t), min(p.x for p, _ in t)))

        for idx, tabela in enumerate(tabelas_finais):
            linhas_agrupadas = defaultdict(list)
            for ponto, texto in tabela:
                chave_y = round(ponto.y / tolerancia_y) * tolerancia_y
                linhas_agrupadas[chave_y].append((ponto.x, texto.strip()))
            
            chaves_y_ordenadas = sorted(linhas_agrupadas.keys(), reverse=True)
            dados_finais = [sorted(linhas_agrupadas[y], key=lambda i: i[0]) for y in chaves_y_ordenadas]
            dados_finais = [[texto for x, texto in linha] for linha in dados_finais]

            df = pd.DataFrame(dados_finais)
            df.to_excel(writer, sheet_name=f'Tabela_{idx + 1}', index=False, header=False)
            logging.info(f"Tabela {idx + 1} ({len(df)} linhas) salva na aba 'Tabela_{idx + 1}'.")

    logging.info(f"✅ Extração concluída. Salvo em: {caminho_saida_xlsx}")