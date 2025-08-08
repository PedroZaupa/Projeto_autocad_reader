import fitz  # PyMuPDF
import pytesseract
from pytesseract import Output
from PIL import Image
import io
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import re
import os

# Configuração Tesseract (ajuste o caminho se necessário)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
lang = "por"

pdf_path = "Projeto Urbanistico - Lote 02-03-04 - 04-08-25.pdf"

# Criar pasta de saída
os.makedirs("resultados", exist_ok=True)

def ocr_pdf(pdf_path):
    """Faz OCR em todas as páginas do PDF"""
    doc = fitz.open(pdf_path)
    texto_total = ""
    paginas = []
    for page_num, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        ocr_text = pytesseract.image_to_string(img, lang=lang)
        texto_total += f"\n--- Página {page_num} ---\n{ocr_text}"
        paginas.append(ocr_text)
    return texto_total, paginas

def extrair_quadro_areas(texto):
    """Extrai o Quadro de Áreas"""
    padrao = re.compile(r"(Área total[\s\S]+?)(?=\n\n|\Z)", re.IGNORECASE)
    match = padrao.search(texto)
    if match:
        linhas = [l.strip() for l in match.group(1).splitlines() if l.strip()]
        return linhas
    return []

def extrair_quadras_vias(texto):
    """Extrai lista de quadras e vias"""
    padrao = re.compile(r"(Quadra\s+\d+[\s\S]+?)(?=\n\n|\Z)", re.IGNORECASE)
    return padrao.findall(texto)

def extrair_tabelas_coordenadas(paginas):
    """Procura tabelas de azimutes/distâncias/coordenadas"""
    tabelas = []
    for texto in paginas:
        if "Vértices" in texto or "Azimute" in texto:
            linhas = [l for l in texto.splitlines() if l.strip()]
            tabelas.append(linhas)
    return tabelas

def salvar_excel(quadro_areas, quadras, tabelas_coord):
    writer = pd.ExcelWriter("resultados/dados_extraidos.xlsx", engine="openpyxl")
    
    if quadro_areas:
        df_areas = pd.DataFrame(quadro_areas)
        df_areas.to_excel(writer, sheet_name="Quadro_Areas", index=False, header=False)
    
    if quadras:
        df_quadras = pd.DataFrame(quadras)
        df_quadras.to_excel(writer, sheet_name="Quadras_Vias", index=False, header=False)
    
    for i, tabela in enumerate(tabelas_coord, start=1):
        df = pd.DataFrame([linha.split() for linha in tabela])
        df.to_excel(writer, sheet_name=f"Tabela_{i}", index=False, header=False)
    
    writer.close()

def salvar_pdf_tabelas(tabelas_coord):
    doc = SimpleDocTemplate("resultados/tabelas_formatadas.pdf", pagesize=A4)
    elementos = []
    styles = getSampleStyleSheet()
    
    for i, tabela in enumerate(tabelas_coord, start=1):
        elementos.append(Paragraph(f"Tabela {i}", styles["Heading2"]))
        dados = [linha.split() for linha in tabela]
        table = Table(dados)
        estilo = TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 7),
        ])
        table.setStyle(estilo)
        elementos.append(table)
    
    doc.build(elementos)

if __name__ == "__main__":
    texto_total, paginas_texto = ocr_pdf(pdf_path)
    
    quadro_areas = extrair_quadro_areas(texto_total)
    quadras = extrair_quadras_vias(texto_total)
    tabelas_coord = extrair_tabelas_coordenadas(paginas_texto)
    
    salvar_excel(quadro_areas, quadras, tabelas_coord)
    salvar_pdf_tabelas(tabelas_coord)
    
    print("Extração concluída! Arquivos gerados em 'resultados/'")
