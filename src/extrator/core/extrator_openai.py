# scripts/ExtratorTopografia/extrator_resumo_principal.py

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
from dotenv import load_dotenv
from openai import OpenAI

# --- CONFIGURAÇÃO DO TESSERACT ---
# Tenta detectar automaticamente onde está instalado
possiveis_caminhos = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
]
for caminho in possiveis_caminhos:
    if os.path.exists(caminho):
        pytesseract.pytesseract.tesseract_cmd = caminho
        break

# --- CONFIGURAÇÃO OPENAI ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- FUNÇÃO PARA LER TEXTO DO PDF VIA OCR ---
def extrair_texto_pdf(pdf_path):
    pdf = fitz.open(pdf_path)
    texto_total = ""

    for page_num in range(len(pdf)):
        pix = pdf[page_num].get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes()))
        texto = pytesseract.image_to_string(img, lang="por")
        texto_total += texto + "\n"

    return texto_total

# --- FUNÇÃO PARA CHAMAR O GPT E EXTRAIR APENAS OS DADOS PRINCIPAIS ---
def gerar_resumo_principal(pdf_path):
    texto_pdf = extrair_texto_pdf(pdf_path)

    prompt = f"""
    Você é um especialista em análise de projetos urbanísticos.
    A partir do texto abaixo, extraia apenas as seguintes informações:
    
    1. Empreendimento
    2. Local
    3. Proprietário
    4. Responsável técnico
    5. Processo (número e descrição)
    6. Quadro de áreas (com m² e % se existir)
    7. Geometria e coordenadas (todas as legendas e valores exatamente como aparecem no PDF, 
       incluindo latitude, longitude, datum, coordenadas N/E, altitudes, origem topográfica, 
       altitude ortométrica média do plano, fator de escala, convergência meridiana)
    8. Zoneamento
    9. ART/RRT (número, tipo e conselho, se houver)

    Mantenha os valores exatamente como no PDF.
    Organize o resultado em formato de lista com títulos claros.

    Texto do PDF:
    {texto_pdf}
    """

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é um especialista em extração de dados de projetos urbanísticos."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return resposta.choices[0].message.content

# --- EXECUÇÃO ---
if __name__ == "__main__":
    pdf_path = "data/pdfs/Projeto Urbanistico - Lote 02-03-04 - 04-08-25.pdf"
    resultado = gerar_resumo_principal(pdf_path)

    # Salva também em arquivo de texto para consulta posterior
    os.makedirs("output/text", exist_ok=True)
    with open("output/text/resumo_principal.txt", "w", encoding="utf-8") as f:
        f.write(resultado)

    print("\n=== RESUMO PRINCIPAL EXTRAÍDO ===\n")
    print(resultado)
    print("\nArquivo salvo em: output/text/resumo_principal.txt")
