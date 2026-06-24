import os
import re
import json
import logging
import ezdxf
import pandas as pd
from extrator.utils import limpar_texto_autocad

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def coletar_linhas_texto(dxf_path):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    linhas = []
    for entity in msp.query("TEXT MTEXT"):
        texto_original = entity.plain_text().replace("¶", "\n") if entity.dxftype() == "MTEXT" else entity.dxf.text
        texto_limpo = limpar_texto_autocad(texto_original)
        linhas.extend([t.strip() for t in texto_limpo.splitlines() if t.strip()])
    return linhas

def extrair_campos(linhas):
    padroes = {
        "metadados": [r"LOTE", r"GLEBA", r"LONDRINA", r"PARANÁ", r"CNPJ", r"CPF", r"PROCESSO", r"ESCALA"],
        "geodesia": [r"DATUM", r"SIRGAS", r"UTM", r"LATITUDE", r"LONGITUDE", r"N\s*=", r"E\s*=", r"ALTITUDE"],
        "quadro_areas": [r"ÁREA", r"SISTEMA VIÁRIO", r"INSTITUCIONAL", r"FAIXA.*COPEL"],
        "zoneamento": [r"ZONA", r"ZR\d", r"ZM"],
        "art_rrt": [r"ART", r"RRT", r"CREA", r"CAU"]
    }
    dados = {}
    for chave, lista_padroes in padroes.items():
        regex = re.compile("|".join(lista_padroes), re.IGNORECASE)
        dados[chave] = [ln for ln in linhas if regex.search(ln)]
    return dados

def processar_quadro_areas(linhas_quadro):
    dados = []
    regex_valor = re.compile(r"^(.*?)\s*[:.]*\s*([\d.,]+)\s*m²?$", re.IGNORECASE)
    for linha in linhas_quadro:
        match = regex_valor.search(linha)
        if match:
            desc = match.group(1).strip().replace(":", "").strip()
            val_str = match.group(2).replace(".", "").replace(",", ".")
            try:
                val = float(val_str)
                dados.append({"Descrição": desc, "Área (m²)": val})
            except ValueError:
                logging.warning(f"Não foi possível converter o valor de área '{val_str}' na linha: '{linha}'")
    return pd.DataFrame(dados)

def salvar_resultados(dados, df_areas, base_nome, pasta_saida):
    os.makedirs(pasta_saida, exist_ok=True)
    caminho_json = os.path.join(pasta_saida, f"{base_nome}_resumo.json")
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    logging.info(f"Resumo de dados salvo em: {caminho_json}")

    if not df_areas.empty:
        caminho_excel = os.path.join(pasta_saida, f"{base_nome}_quadro_areas.xlsx")
        df_areas.to_excel(caminho_excel, index=False)
        logging.info(f"Quadro de áreas salvo em: {caminho_excel}")