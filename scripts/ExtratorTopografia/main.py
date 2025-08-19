import os
import logging
from converter_dwg import dwg_para_dxf, carregar_config
from extrair_dados_dxf import coletar_linhas_texto, extrair_campos, processar_quadro_areas, salvar_resultados
from extrair_tabelas import extrair_tabelas_por_layer

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')

def executar_fluxo():
    """
    Executa o fluxo completo: converte todos os DWGs, extrai dados gerais
    e extrai tabelas específicas de cada um.
    """
    try:
        config = carregar_config()
    except FileNotFoundError:
        logging.error("Arquivo 'config.json' não encontrado. Crie um e configure os caminhos.")
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
        caminho_completo_dwg = os.path.join(pasta_dwg, nome_arquivo_dwg)
        nome_base = os.path.splitext(nome_arquivo_dwg)[0]
        logging.info(f"--- Iniciando processamento de: {nome_arquivo_dwg} ---")

        try:
            # 1️⃣ Converter DWG -> DXF
            dxf_path = dwg_para_dxf(
                caminho_completo_dwg,
                config["pasta_saida_dados"],
                config["caminho_odafc"]
            )

            # 2️⃣ Extrair dados gerais do DXF
            linhas = coletar_linhas_texto(dxf_path)
            dados_extraidos = extrair_campos(linhas)
            df_areas = processar_quadro_areas(dados_extraidos.get("quadro_areas", []))
            salvar_resultados(dados_extraidos, df_areas, nome_base, config["pasta_saida_final"])

            # 3️⃣ Extrair tabelas topográficas do DXF (CHAMADA CORRIGIDA)
            extrair_tabelas_por_layer(
                dxf_path, 
                config["pasta_saida_final"],
                # --- Parâmetros de Agrupamento Geral ---
                dist_max=150.0,
                
                # --- Parâmetros para Divisão VERTICAL (Y) ---
                tolerancia_y=2.5,
                multiplicador_gap_y=4.0,
                
                # --- Parâmetros para Divisão HORIZONTAL (X) ---
                tolerancia_x=10.0,
                multiplicador_gap_x=5.0  # <<-- AJUSTE AQUI (aumentado de 2.0 para 5.0)
            )
            logging.info("Tabelas extraídas e salvas com sucesso.")

        except FileNotFoundError as e:
            logging.error(f"Erro de arquivo não encontrado para '{nome_arquivo_dwg}': {e}")
        except RuntimeError as e:
            logging.error(f"Erro durante a execução para '{nome_arquivo_dwg}': {e}")
        except Exception as e:
            logging.error(f"Ocorreu um erro inesperado ao processar '{nome_arquivo_dwg}': {e}")

    logging.info("--- Processo finalizado para todos os arquivos. ---")

if __name__ == "__main__":
    executar_fluxo()