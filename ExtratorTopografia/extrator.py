import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re
import os
import pandas as pd
from collections import namedtuple

# Configurar pytesseract caso esteja em Windows (informe o caminho do executável se necessário)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Evitar erro por imagens grandes
Image.MAX_IMAGE_PIXELS = None

Tabela = namedtuple("Tabela", ["titulo", "linhas"])

def extrair_imagens_das_paginas(pdf_path, pasta_saida="imagens"):
    os.makedirs(pasta_saida, exist_ok=True)
    doc = fitz.open(pdf_path)
    imagens = []
    for i, page in enumerate(doc):
        # Obter o retângulo da página para garantir captura completa
        rect = page.rect
        # Aumentar a resolução para melhor OCR e evitar cortes
        zoom = 3  # 300% zoom
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_path = os.path.join(pasta_saida, f"pagina_{i+1}.png")
        pix.save(img_path)
        imagens.append(img_path)
    return imagens

def detectar_tabelas_com_ocr(imagem_path):
    imagem = Image.open(imagem_path)
    texto = pytesseract.image_to_string(imagem, lang='por')
    blocos = texto.split("TABELA DE AZIMUTES")
    tabelas = []
    for bloco in blocos[1:]:  # ignora o que vem antes da primeira tabela
        linhas = bloco.strip().splitlines()
        linhas_validas = [l for l in linhas if re.search(r'V\d+\s+V\d+', l)]
        if linhas_validas:
            titulo = "TABELA DE AZIMUTES" + bloco.splitlines()[0]
            tabelas.append(Tabela(titulo=titulo, linhas=linhas_validas))
    return tabelas

def processar_pdf(pdf_path):
    imagens = extrair_imagens_das_paginas(pdf_path)
    todas_tabelas = []
    for img_path in imagens:
        tabelas = detectar_tabelas_com_ocr(img_path)
        todas_tabelas.extend(tabelas)
    return todas_tabelas

def exportar_para_excel(tabelas, arquivo_saida="tabelas_extraidas.xlsx"):
    writer = pd.ExcelWriter(arquivo_saida, engine='openpyxl')
    alguma_tabela_exportada = False
    for i, tabela in enumerate(tabelas):
        dados = []
        for linha in tabela.linhas:
            colunas = re.split(r'\s{2,}', linha.strip())
            dados.append(colunas)
        df = pd.DataFrame(dados)
        if not df.empty:
            df.to_excel(writer, index=False, header=False, sheet_name=f"Tabela_{i+1}")
            alguma_tabela_exportada = True

    if alguma_tabela_exportada:
        writer.close()
        print(f"Tabelas exportadas para {arquivo_saida}")
    else:
        print("Nenhuma tabela válida encontrada para exportar.")

# Exemplo de uso:
if __name__ == "__main__":
    tabelas = processar_pdf("Projeto Urbanistico - Lote 02-03-04 - 04-08-25.pdf")
    exportar_para_excel(tabelas)
