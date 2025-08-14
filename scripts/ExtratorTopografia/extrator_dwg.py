import os
import re
import json
import glob
import logging
from typing import List, Dict, Any

import ezdxf
from ezdxf.addons import odafc
import pandas as pd

# Configuração do logging para exibir mensagens informativas
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def carregar_configuracao(path: str = "config.json") -> Dict[str, Any]:
    """Carrega as configurações a partir de um arquivo JSON."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Define o caminho do ODA File Converter no ambiente
            os.environ["ODAFILECONVERTER"] = config["caminho_odafc"]
            return config
    except FileNotFoundError:
        logging.error(f"Erro: Arquivo de configuração '{path}' não encontrado.")
        raise
    except KeyError as e:
        logging.error(f"Erro: Chave de configuração ausente no JSON: {e}")
        raise

def localizar_dwg(pasta_raiz: str) -> str:
    """Localiza o arquivo DWG mais relevante na pasta especificada."""
    padrao = os.path.join(pasta_raiz, "**", "*.dwg")
    arquivos = glob.glob(padrao, recursive=True)
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo DWG encontrado em: {pasta_raiz}")

    preferencias = ["Lote 02-03-04", "Lote 02/03/04", "02-03-04"]
    preferidos = [p for p in arquivos if any(term.lower() in os.path.basename(p).lower() for term in preferencias)]
    
    if preferidos:
        preferidos.sort(key=os.path.getmtime, reverse=True)
        logging.info(f"Arquivo DWG preferencial encontrado: {os.path.basename(preferidos[0])}")
        return preferidos[0]

    arquivos.sort(key=os.path.getmtime, reverse=True)
    logging.info(f"Nenhum DWG preferencial. Usando o mais recente: {os.path.basename(arquivos[0])}")
    return arquivos[0]

def dwg_para_dxf(dwg_path: str, pasta_saida: str) -> str:
    """Converte um arquivo DWG para DXF usando o ODA File Converter."""
    os.makedirs(pasta_saida, exist_ok=True)
    base_nome = os.path.splitext(os.path.basename(dwg_path))[0]
    caminho_dxf = os.path.join(pasta_saida, f"{base_nome}.dxf")

    try:
        doc = odafc.readfile(dwg_path)
        doc.saveas(caminho_dxf)
        return caminho_dxf
    except Exception as e:
        logging.error(f"Falha ao converter DWG para DXF. Verifique se o ODAFileConverter está configurado corretamente. Erro: {e}")
        raise

def coletar_linhas_texto(dxf_path: str) -> List[str]:
    """Lê um arquivo DXF e coleta todas as entidades de texto (TEXT e MTEXT)."""
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
    except IOError:
        logging.error(f"Não foi possível abrir o arquivo DXF: {dxf_path}")
        return []

    linhas: List[str] = []
    
    # Extrai TEXT
    for entity in msp.query("TEXT"):
        try:
            if entity.dxf.text:
                linhas.extend(str(entity.dxf.text).splitlines())
        except AttributeError:
            logging.warning(f"Entidade TEXT sem atributo 'text' encontrada.")

    # Extrai MTEXT
    for entity in msp.query("MTEXT"):
        try:
            texto = entity.plain_text().replace("¶", "\n")
            if texto:
                linhas.extend(texto.splitlines())
        except AttributeError:
             logging.warning(f"Entidade MTEXT sem método 'plain_text' encontrada.")

    return [ln.strip() for ln in linhas if ln and ln.strip()]

def extrair_campos(linhas: List[str]) -> Dict[str, List[str]]:
    """Filtra as linhas de texto com base em padrões regex para extrair informações."""
    padroes = {
        "metadados": [r"\bLOTE\b", r"GLEBA", r"LONDRINA", r"PARANÁ", r"\bCNPJ\b", r"\bCPF\b", r"\bCAU\b", r"\bCREA\b", r"\bPROCESSO\b", r"\bSEI\b", r"\bESCALA\b", r"\bREVIS(ÃO|AO)\b", r"\bDWG\b", r"PROJETO URBANISTICO", r"URBAN[IÍ]STICO"],
        "geodesia": [r"\bDATUM\b", r"SIRGAS", r"\bUTM\b", r"\bM\d{2}\b", r"MERIDIANO", r"CONVERG[ÊE]NCIA", r"FATOR DE ESCALA", r"\bLATITUDE\b", r"\bLONGITUDE\b", r"\bN\s*=\s*", r"\bE\s*=\s*", r"ALTITUDE", r"ELIPSOIDAL", r"ORTOM[ÉE]TRICA", r"OG MAPGEO", r"ORIGEM TOPOGR[ÁA]FICA"],
        "quadro_areas": [r"ÁREA.*TERRENO", r"ÁREA DE PRESERVA", r"ÁREA LOTE[ÁA]VEL", r"ÁREA DE QUADRAS", r"SISTEMA VI[ÁA]RIO", r"ÁREA[S ]+INSTITUCIONAIS?", r"ÁREA P[ÚU]BLICA N[ÃA]O EDIFIC[ÁA]VEL", r"FAIXA.*COPEL"],
        "zoneamento": [r"\bZONA(MENTO)?\b", r"\bZR\d\b", r"\bZM\b", r"ZONA DE USO", r"ZONA RESIDENCIAL"],
        "art_rrt": [r"\bART\b", r"\bRRT\b", r"\bCREA\b", r"\bCAU\b", r"\bn[ºo]\b", r"\bn°\b", r"\bnº\b"]
    }
    
    dados_extraidos = {}
    linhas_unicas = sorted(list(set(linhas)), key=linhas.index) # Remove duplicadas mantendo a ordem

    for chave, lista_padroes in padroes.items():
        regex_compilado = re.compile("|".join(lista_padroes), re.IGNORECASE)
        dados_extraidos[chave] = [ln for ln in linhas_unicas if regex_compilado.search(ln)]
        
    return dados_extraidos

def processar_quadro_areas_para_planilha(linhas_quadro: List[str]) -> pd.DataFrame:
    """Processa as linhas do quadro de áreas para extrair descrição e valor."""
    dados_tabelados = []
    # Regex para capturar: (Qualquer texto no início) ... (um número com . e ,) ... (opcionalmente m² no final)
    regex_valor = re.compile(r"^(.*?)\s*[.\s]*([\d.,]+)\s*m²?$", re.IGNORECASE)

    for linha in linhas_quadro:
        match = regex_valor.search(linha)
        if match:
            descricao = match.group(1).strip().replace(":", "").replace("-", "").strip()
            valor_str = match.group(2).replace('.', '').replace(',', '.')
            try:
                valor_num = float(valor_str)
                dados_tabelados.append({"Descrição": descricao, "Área (m²)": valor_num})
            except ValueError:
                logging.warning(f"Não foi possível converter o valor '{valor_str}' da linha: '{linha}'")

    if not dados_tabelados:
        logging.warning("Nenhum dado estruturado pôde ser extraído do Quadro de Áreas para a planilha.")
        return pd.DataFrame()

    return pd.DataFrame(dados_tabelados)


def salvar_saidas(dados: Dict[str, List[str]], df_areas: pd.DataFrame, base_nome: str, pasta_saida: str):
    """Salva os dados extraídos em arquivos de texto, JSON e Excel."""
    os.makedirs(os.path.join(pasta_saida, "text"), exist_ok=True)
    os.makedirs(os.path.join(pasta_saida, "json"), exist_ok=True)
    os.makedirs(os.path.join(pasta_saida, "planilhas"), exist_ok=True)

    # 1. Salvar TXT
    caminho_txt = os.path.join(pasta_saida, "text", f"{base_nome}_resumo.txt")
    with open(caminho_txt, "w", encoding="utf-8") as f:
        for chave, lista_linhas in dados.items():
            f.write(f"# {chave.replace('_', ' ').title()}\n")
            for linha in lista_linhas:
                f.write(linha + "\n")
            f.write("\n")
    logging.info(f"Resumo em TXT salvo em: {caminho_txt}")

    # 2. Salvar JSON
    caminho_json = os.path.join(pasta_saida, "json", f"{base_nome}_resumo.json")
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    logging.info(f"Resumo em JSON salvo em: {caminho_json}")
    
    # 3. Salvar Planilha Excel
    if not df_areas.empty:
        caminho_excel = os.path.join(pasta_saida, "planilhas", f"{base_nome}_quadro_areas.xlsx")
        df_areas.to_excel(caminho_excel, index=False, engine='openpyxl')
        logging.info(f"Planilha do Quadro de Áreas salva em: {caminho_excel}")


def main():
    """Função principal que orquestra a execução do script."""
    try:
        config = carregar_configuracao()
        
        # 1. Localizar DWG
        dwg_encontrado = localizar_dwg(config["pasta_dwg_entrada"])
        
        # 2. Converter para DXF
        caminho_dxf = dwg_para_dxf(dwg_encontrado, config["pasta_saida_dados"])
        logging.info(f"Arquivo DXF gerado em: {caminho_dxf}")

        # 3. Coletar textos
        linhas = coletar_linhas_texto(caminho_dxf)
        logging.info(f"Total de linhas de texto coletadas: {len(linhas)}")

        # 4. Extrair campos de interesse
        dados_brutos = extrair_campos(linhas)
        
        # 5. Processar quadro de áreas para planilha
        df_areas = processar_quadro_areas_para_planilha(dados_brutos["quadro_areas"])

        # 6. Salvar todas as saídas
        base_nome = os.path.splitext(os.path.basename(caminho_dxf))[0]
        salvar_saidas(dados_brutos, df_areas, base_nome, config["pasta_saida_final"])
        
        logging.info("Processo concluído com sucesso!")

    except Exception as e:
        logging.error(f"Ocorreu um erro fatal: {e}")

if __name__ == "__main__":
    main()