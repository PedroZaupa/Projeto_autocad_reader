import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def dwg_para_dxf(dwg_path, pasta_saida, odafc_exec):
    """Converte um único arquivo DWG para o formato DXF."""
    os.makedirs(pasta_saida, exist_ok=True)
    nome_base = os.path.splitext(os.path.basename(dwg_path))[0]
    caminho_dxf_final = os.path.join(pasta_saida, f"{nome_base}.dxf")
    odafc_exec_path = os.path.normpath(odafc_exec)
    dwg_dir = os.path.normpath(os.path.dirname(dwg_path))
    pasta_saida_norm = os.path.normpath(pasta_saida)
    nome_arquivo_dwg = os.path.basename(dwg_path)

    comando = [
        odafc_exec_path, dwg_dir, pasta_saida_norm,
        "ACAD2018", "DXF", "0", "1", nome_arquivo_dwg
    ]

    logging.info(f"Convertendo DWG para DXF: {dwg_path}")
    result = subprocess.run(comando, cwd=os.path.dirname(odafc_exec_path), capture_output=True, text=True, encoding='latin-1')

    if result.returncode != 0:
        logging.error(f"Erro na conversão (código {result.returncode}):\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        raise RuntimeError("Falha na conversão DWG -> DXF")

    if not os.path.exists(caminho_dxf_final):
        raise FileNotFoundError(f"Arquivo DXF esperado não foi encontrado em: {caminho_dxf_final}")

    logging.info(f"DXF gerado: {caminho_dxf_final}")
    return caminho_dxf_final