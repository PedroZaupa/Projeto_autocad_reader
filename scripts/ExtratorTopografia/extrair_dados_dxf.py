import os
import re
import json
import logging
import ezdxf
import pandas as pd

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def carregar_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def coletar_linhas_texto(dxf_path):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    linhas = []
    for entity in msp.query("TEXT MTEXT"):
        texto = entity.plain_text().replace("¶", "\n") if entity.dxftype() == "MTEXT" else entity.dxf.text
        linhas.extend([t.strip() for t in texto.splitlines() if t.strip()])
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
    for chave, lista in padroes.items():
        regex = re.compile("|".join(lista), re.IGNORECASE)
        dados[chave] = [ln for ln in linhas if regex.search(ln)]
    return dados

def processar_quadro_areas(linhas_quadro):
    dados = []
    regex_valor = re.compile(r"^(.*?)\s*[.\s]*([\d.,]+)\s*m²?$", re.IGNORECASE)
    for linha in linhas_quadro:
        match = regex_valor.search(linha)
        if match:
            desc = match.group(1).strip().replace(":", "")
            val = float(match.group(2).replace(".", "").replace(",", "."))
            dados.append({"Descrição": desc, "Área (m²)": val})
    return pd.DataFrame(dados)

def salvar_resultados(dados, df_areas, base_nome, pasta_saida):
    os.makedirs(pasta_saida, exist_ok=True)

    with open(os.path.join(pasta_saida, f"{base_nome}_resumo.json"), "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    if not df_areas.empty:
        df_areas.to_excel(os.path.join(pasta_saida, f"{base_nome}_quadro_areas.xlsx"), index=False)

if __name__ == "__main__":
    config = carregar_config()
    pasta_dxfs = config["pasta_saida_dados"]
    arquivos_dxf = [f for f in os.listdir(pasta_dxfs) if f.lower().endswith(".dxf")]

    if not arquivos_dxf:
        logging.error("Nenhum DXF encontrado.")
    else:
        dxf_path = os.path.join(pasta_dxfs, arquivos_dxf[0])
        linhas = coletar_linhas_texto(dxf_path)
        dados = extrair_campos(linhas)
        df_areas = processar_quadro_areas(dados["quadro_areas"])
        salvar_resultados(dados, df_areas, os.path.splitext(os.path.basename(dxf_path))[0], config["pasta_saida_final"])
        logging.info("Extração concluída!")
