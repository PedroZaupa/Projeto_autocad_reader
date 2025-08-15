import os
import subprocess
import logging
import json

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def carregar_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def dwg_para_dxf(dwg_path, pasta_saida, odafc_exec):
    os.makedirs(pasta_saida, exist_ok=True)

    nome_base = os.path.splitext(os.path.basename(dwg_path))[0]
    caminho_dxf_final = os.path.join(pasta_saida, f"{nome_base}.dxf")

    comando = [
        odafc_exec,
        os.path.dirname(dwg_path),
        pasta_saida,
        "ACAD2018",
        "DXF",
        "0",  # Não recursivo
        "1",  # Auditar
        "*.dwg"
    ]

    logging.info(f"Convertendo DWG para DXF: {dwg_path}")
    result = subprocess.run(comando, cwd=os.path.dirname(odafc_exec), capture_output=True, text=True)

    if result.returncode != 0:
        logging.error(f"Erro na conversão:\n{result.stderr}")
        raise RuntimeError("Falha na conversão DWG -> DXF")

    if not os.path.exists(caminho_dxf_final):
        raise FileNotFoundError(f"DXF não encontrado em: {caminho_dxf_final}")

    logging.info(f"DXF gerado: {caminho_dxf_final}")
    return caminho_dxf_final

if __name__ == "__main__":
    config = carregar_config()
    dwg_entrada = config["pasta_dwg_entrada"]
    arquivos_dwg = [f for f in os.listdir(dwg_entrada) if f.lower().endswith(".dwg")]

    if not arquivos_dwg:
        logging.error("Nenhum DWG encontrado.")
    else:
        dxf_path = dwg_para_dxf(
            os.path.join(dwg_entrada, arquivos_dwg[0]),
            config["pasta_saida_dados"],
            config["caminho_odafc"]
        )
        logging.info(f"Conversão concluída: {dxf_path}")
