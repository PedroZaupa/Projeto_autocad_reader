import os
import logging
from converter_dwg import dwg_para_dxf, carregar_config
from extrair_dados_dxf import coletar_linhas_texto, extrair_campos, processar_quadro_areas, salvar_resultados

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def executar_fluxo():
    config = carregar_config()

    # 1️⃣ Converter DWG -> DXF
    dwg_entrada = config["pasta_dwg_entrada"]
    arquivos_dwg = [f for f in os.listdir(dwg_entrada) if f.lower().endswith(".dwg")]

    if not arquivos_dwg:
        logging.error("Nenhum DWG encontrado.")
        return

    dxf_path = dwg_para_dxf(
        os.path.join(dwg_entrada, arquivos_dwg[0]),
        config["pasta_saida_dados"],
        config["caminho_odafc"]
    )

    # 2️⃣ Extrair dados do DXF
    linhas = coletar_linhas_texto(dxf_path)
    dados = extrair_campos(linhas)
    df_areas = processar_quadro_areas(dados["quadro_areas"])
    salvar_resultados(dados, df_areas, os.path.splitext(os.path.basename(dxf_path))[0], config["pasta_saida_final"])

    logging.info("Processo completo! Dados salvos com sucesso.")

if __name__ == "__main__":
    executar_fluxo()
