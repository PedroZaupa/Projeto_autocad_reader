import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
import pandas as pd
import pytesseract
import os

# Detectar instalação do Tesseract automaticamente em Windows
possiveis_caminhos = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
]

for caminho in possiveis_caminhos:
    if os.path.exists(caminho):
        pytesseract.pytesseract.tesseract_cmd = caminho
        print(f"✅ Tesseract configurado automaticamente: {caminho}")
        break
else:
    print("⚠ Tesseract não encontrado. Por favor, instale em https://github.com/UB-Mannheim/tesseract/wiki e tente novamente.")

# Aqui continua o resto do seu código de extração de tabelas


# Configuração
pdf_path = "data/pdfs/Projeto Urbanistico - Lote 02-03-04 - 04-08-25.pdf"
output_dir = "output/csv"
os.makedirs(output_dir, exist_ok=True)

# Abrir PDF
pdf = fitz.open(pdf_path)

quadro_areas_data = []
azimutes_coords_data = []

for page_num in range(len(pdf)):
    page = pdf[page_num]
    pix = page.get_pixmap(dpi=300)
    img = Image.open(io.BytesIO(pix.tobytes()))

    # Aplicar OCR
    texto = pytesseract.image_to_string(img, lang='por')

    linhas = texto.splitlines()

    # Coletar quadro de áreas e pracinhas/institucionais/faixas
    for linha in linhas:
        if any(chave in linha.upper() for chave in ["ÁREA", "PRAÇA", "INSTITUCIONAL", "FAIXA"]):
            quadro_areas_data.append([linha])

    # Coletar tabelas de azimutes/coordenadas
    capturando = False
    tabela_temp = []
    for linha in linhas:
        if linha.strip().upper().startswith("TABELA"):
            if tabela_temp:
                azimutes_coords_data.extend(tabela_temp)
                tabela_temp = []
            capturando = True
            tabela_temp.append(linha)
        elif capturando:
            if linha.strip() == "":
                capturando = False
                azimutes_coords_data.extend(tabela_temp)
                tabela_temp = []
            else:
                tabela_temp.append(linha)
    if tabela_temp:
        azimutes_coords_data.extend(tabela_temp)

# Salvar quadro de áreas
if quadro_areas_data:
    df_areas = pd.DataFrame(quadro_areas_data, columns=["Descrição"])
    df_areas.to_csv(os.path.join(output_dir, "quadro_areas.csv"), index=False, encoding="utf-8-sig")

# Salvar tabelas de azimutes/coordenadas
if azimutes_coords_data:
    df_azimutes = pd.DataFrame(azimutes_coords_data, columns=["Dados"])
    df_azimutes.to_csv(os.path.join(output_dir, "tabelas_azimutes_coordenadas.csv"), index=False, encoding="utf-8-sig")

print("✅ Extração concluída. Arquivos salvos em", output_dir)
