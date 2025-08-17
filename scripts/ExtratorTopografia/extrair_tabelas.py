import os
import logging
import ezdxf
import pandas as pd

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def extrair_tabelas_dxf(dxf_path: str, pasta_saida: str):
    """
    Extrai todas as tabelas (layouts com nome 'tabela') de um DXF.
    Mantém a ordem original das entidades e salva em Excel/CSV.
    """
    if not os.path.exists(dxf_path):
        raise FileNotFoundError(f"Arquivo DXF não encontrado: {dxf_path}")

    try:
        doc = ezdxf.readfile(dxf_path)
    except Exception as e:
        raise RuntimeError(f"Erro ao abrir DXF: {e}")

    # 🔹 Vamos procurar por entidades MTEXT e TEXT dentro de layouts com 'tabela' no nome
    tabelas_extraidas = []
    for layout in doc.layouts:
        if "tabela" in layout.name.lower():
            logging.info(f"Extraindo tabela do layout: {layout.name}")
            linhas = []
            for entity in layout.query("TEXT MTEXT"):
                try:
                    texto = entity.plain_text() if entity.dxftype() == "MTEXT" else entity.dxf.text
                    if texto.strip():
                        linhas.append(texto.strip())
                except Exception as e:
                    logging.warning(f"Erro ao ler entidade em {layout.name}: {e}")

            if linhas:
                tabelas_extraidas.append((layout.name, linhas))

    if not tabelas_extraidas:
        logging.warning("Nenhuma tabela encontrada nos layouts.")
        return

    # Criar pasta de saída
    pasta_tabelas = os.path.join(pasta_saida, "tabelas")
    os.makedirs(pasta_tabelas, exist_ok=True)

    # Salvar cada tabela encontrada
    for idx, (nome_layout, linhas) in enumerate(tabelas_extraidas, start=1):
        df = pd.DataFrame({"Linhas": linhas})
        nome_base = f"tabela_{idx}_{nome_layout.replace(' ', '_')}"
        caminho_csv = os.path.join(pasta_tabelas, f"{nome_base}.csv")
        caminho_xlsx = os.path.join(pasta_tabelas, f"{nome_base}.xlsx")

        df.to_csv(caminho_csv, index=False, encoding="utf-8-sig")
        df.to_excel(caminho_xlsx, index=False, engine="openpyxl")
        logging.info(f"Tabela salva em: {caminho_csv} e {caminho_xlsx}")

    logging.info("✅ Extração de tabelas concluída com sucesso!")
