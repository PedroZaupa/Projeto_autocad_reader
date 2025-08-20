import os
import json
import logging

def carregar_config():
    """Carrega o arquivo de configuração config.json da raiz do projeto."""
    # O caminho é relativo à pasta de trabalho atual
    config_path = os.path.join(os.getcwd(), "config.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Arquivo de configuração não encontrado. Certifique-se de que 'config.json' está na pasta raiz do projeto e que você está executando o script a partir dela.")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def limpar_texto_autocad(texto: str) -> str:
    """Traduz os códigos de controle de texto do AutoCAD para caracteres UTF-8."""
    if texto is None:
        return ""
    # Mapeamento dos principais códigos de controle
    codigos = {
        "%%D": "°",  # Graus
        "%%P": "±",  # Mais/Menos
        "%%C": "ø"   # Diâmetro
    }
    for codigo, simbolo in codigos.items():
        texto = texto.replace(codigo, simbolo)
    return texto

def limpar_arquivos_antigos(nome_base: str, config: dict):
    """Verifica e apaga os arquivos de saída de uma execução anterior."""
    logging.info(f"Verificando e limpando arquivos antigos para: {nome_base}...")
    
    pastas_e_arquivos = {
        config.get("pasta_saida_final"): [
            f"{nome_base}_resumo.json",
            f"{nome_base}_quadro_areas.xlsx"
        ],
        os.path.join(config.get("pasta_saida_final"), "tabelas_extraidas"): [
            f"{nome_base}_tabelas_finais.xlsx"
        ],
        config.get("pasta_saida_json"): [
            f"{nome_base}_tabelas_finais.json"
        ]
    }

    for pasta, arquivos in pastas_e_arquivos.items():
        if not pasta: continue
        for arquivo in arquivos:
            caminho_arquivo = os.path.join(pasta, arquivo)
            if os.path.exists(caminho_arquivo):
                try:
                    os.remove(caminho_arquivo)
                    logging.info(f"Arquivo antigo removido: {caminho_arquivo}")
                except OSError as e:
                    logging.error(f"Erro ao remover o arquivo {caminho_arquivo}: {e}")