import os
import logging
# Imports absolutos a partir da raiz do pacote 'extrator'
from extrator.utils import carregar_config, limpar_arquivos_antigos
from extrator.core.conversor import dwg_para_dxf
from extrator.core.extrator_dados import coletar_linhas_texto, extrair_campos, processar_quadro_areas, salvar_resultados
from extrator.core.extrator_tabelas import extrair_tabelas_por_layer

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')

def executar_fluxo():
    """
    Executa o fluxo completo: limpa, converte, extrai dados e tabelas.
    """
    try:
        config = carregar_config()
    except FileNotFoundError as e:
        logging.error(e)
        return

    pasta_dwg = config.get("pasta_dwg_entrada")
    if not pasta_dwg or not os.path.isdir(pasta_dwg):
        logging.error(f"A 'pasta_dwg_entrada' ({pasta_dwg}) é inválida ou não foi configurada no config.json.")
        return

    arquivos_dwg = [f for f in os.listdir(pasta_dwg) if f.lower().endswith(".dwg")]
    if not arquivos_dwg:
        logging.warning("Nenhum arquivo DWG encontrado na pasta de entrada.")
        return

    logging.info(f"Encontrados {len(arquivos_dwg)} arquivos DWG para processar.")

    for nome_arquivo_dwg in arquivos_dwg:
        nome_base = os.path.splitext(nome_arquivo_dwg)[0]
        logging.info(f"--- Iniciando processamento de: {nome_arquivo_dwg} ---")
        
        limpar_arquivos_antigos(nome_base, config)

        try:
            caminho_dwg = os.path.join(pasta_dwg, nome_arquivo_dwg)
            dxf_path = dwg_para_dxf(
                caminho_dwg,
                config["pasta_saida_dados"],
                config["caminho_odafc"]
            )

            linhas = coletar_linhas_texto(dxf_path)
            dados_extraidos = extrair_campos(linhas)
            df_areas = processar_quadro_areas(dados_extraidos.get("quadro_areas", []))
            salvar_resultados(dados_extraidos, df_areas, nome_base, config["pasta_saida_final"])

            extrair_tabelas_por_layer(
                dxf_path, 
                config["pasta_saida_final"],
                config["pasta_saida_json"],
                dist_max=150.0,
                tolerancia_y=2.5,
                multiplicador_gap_y=4.0,
                tolerancia_x=10.0,
                multiplicador_gap_x=5.0
            )
            
        except Exception as e:
            logging.error(f"Ocorreu um erro inesperado ao processar '{nome_arquivo_dwg}': {e}", exc_info=True)

    logging.info("--- Processo finalizado para todos os arquivos. ---")

if __name__ == "__main__":
    executar_fluxo()