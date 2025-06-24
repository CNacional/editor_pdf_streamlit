import streamlit as st
import base64
import io
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdf2docx import Converter
import os

st.set_page_config(page_title="Editor de PDF", layout="wide")
st.title("🛠️ Editor de PDF Online")

menu = st.sidebar.radio("Escolha uma função:", [
    "Visualizar PDF",
    "Extrair páginas",
    "Mesclar PDFs",
    "Dividir PDF",
    "Rotacionar páginas",
    "Adicionar marca d'água",
    "Inserir páginas de outro PDF",
    "Extrair texto",
    "Editar metadados",
    "Converter para Word",
    "Adicionar numeração",
    "Remover numeração"
])

uploaded_file = st.file_uploader("📎 Envie um arquivo PDF", type="pdf")

# Utilitário para baixar arquivos PDF gerados
def download_button(writer, filename):
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📥 Baixar PDF processado</a>'
    st.markdown(href, unsafe_allow_html=True)

# Visualizador embutido
def visualizar_pdf(uploaded_file):
    if uploaded_file:
        base64_pdf = base64.b64encode(uploaded_file.read()).decode('utf-8')
        pdf_display = f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>
        """
        st.components.v1.html(pdf_display, height=1000)

# Adiciona número de páginas com reportlab
def adicionar_numeracao(uploaded_file):
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            numero = f"{i + 1}"
            can.setFont("Helvetica", 10)
            can.drawCentredString(300, 15, numero)
            can.save()
            packet.seek(0)
            overlay = PdfReader(packet)
            page.merge_page(overlay.pages[0])
            writer.add_page(page)
        download_button(writer, "com_numeracao.pdf")

# Remove visualmente numeração cortando o rodapé
def remover_rodape(uploaded_file):
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        writer = PdfWriter()
        for page in reader.pages:
            page.mediabox.lower_left = (0, 40)
            writer.add_page(page)
        download_button(writer, "sem_numeracao.pdf")

# Extrair páginas específicas
def extrair_paginas(uploaded_file):
    paginas = st.text_input("Digite as páginas a extrair (ex: 1,3,5)")
    if uploaded_file and paginas:
        reader = PdfReader(uploaded_file)
        writer = PdfWriter()
        indices = [int(p.strip()) - 1 for p in paginas.split(',') if p.strip().isdigit()]
        for i in indices:
            if 0 <= i < len(reader.pages):
                writer.add_page(reader.pages[i])
        download_button(writer, "paginas_extraidas.pdf")

# Mesclar dois PDFs
def mesclar_pdfs():
    pdf1 = st.file_uploader("Primeiro PDF", type="pdf", key="mesclar1")
    pdf2 = st.file_uploader("Segundo PDF", type="pdf", key="mesclar2")
    if pdf1 and pdf2:
        writer = PdfWriter()
        for f in [pdf1, pdf2]:
            reader = PdfReader(f)
            for page in reader.pages:
                writer.add_page(page)
        download_button(writer, "pdf_mesclado.pdf")

# Dividir PDF em páginas separadas
def dividir_pdf(uploaded_file):
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            st.write(f"Página {i + 1}")
            download_button(writer, f"pagina_{i+1}.pdf")

# Rotacionar páginas

def rotacionar_paginas(uploaded_file):
    angulo = st.selectbox("Escolha o ângulo de rotação:", [90, 180, 270])
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        writer = PdfWriter()
        for page in reader.pages:
            page.rotate(angulo)
            writer.add_page(page)
        download_button(writer, f"rotacionado_{angulo}.pdf")

# Adicionar marca d'água

def adicionar_marcadagua(uploaded_file):
    texto = st.text_input("Texto da marca d'água")
    if uploaded_file and texto:
        reader = PdfReader(uploaded_file)
        writer = PdfWriter()
        for page in reader.pages:
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.setFont("Helvetica", 20)
            can.setFillGray(0.5, 0.5)
            can.drawString(100, 500, texto)
            can.save()
            packet.seek(0)
            overlay = PdfReader(packet)
            page.merge_page(overlay.pages[0])
            writer.add_page(page)
        download_button(writer, "com_marcadagua.pdf")

# Inserir páginas de outro PDF

def inserir_paginas(uploaded_file):
    pdf_extra = st.file_uploader("PDF com páginas para inserir", type="pdf")
    posicao = st.number_input("Posição para inserir", min_value=0, step=1)
    if uploaded_file and pdf_extra:
        reader1 = PdfReader(uploaded_file)
        reader2 = PdfReader(pdf_extra)
        writer = PdfWriter()
        for i in range(posicao):
            writer.add_page(reader1.pages[i])
        for page in reader2.pages:
            writer.add_page(page)
        for i in range(posicao, len(reader1.pages)):
            writer.add_page(reader1.pages[i])
        download_button(writer, "pdf_com_insercao.pdf")

# Extrair texto

def extrair_texto(uploaded_file):
    if uploaded_file:
        with pdfplumber.open(uploaded_file) as pdf:
            texto = "\n".join(page.extract_text() or '' for page in pdf.pages)
        st.text_area("Texto extraído:", value=texto, height=400)

# Editar metadados

def editar_metadados(uploaded_file):
    titulo = st.text_input("Novo título")
    autor = st.text_input("Novo autor")
    assunto = st.text_input("Novo assunto")
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.add_metadata({"/Title": titulo, "/Author": autor, "/Subject": assunto})
        download_button(writer, "com_metadados.pdf")

# Converter para Word

def converter_para_word(uploaded_file):
    if uploaded_file:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.read())
        docx_path = "convertido.docx"
        cv = Converter("temp.pdf")
        cv.convert(docx_path, start=0, end=None)
        cv.close()
        with open(docx_path, "rb") as f:
            st.download_button("📄 Baixar DOCX", f, file_name=docx_path)
        os.remove("temp.pdf")
        os.remove(docx_path)

# Execução das funções com base no menu
if menu == "Visualizar PDF":
    visualizar_pdf(uploaded_file)
elif menu == "Extrair páginas":
    extrair_paginas(uploaded_file)
elif menu == "Mesclar PDFs":
    mesclar_pdfs()
elif menu == "Dividir PDF":
    dividir_pdf(uploaded_file)
elif menu == "Rotacionar páginas":
    rotacionar_paginas(uploaded_file)
elif menu == "Adicionar marca d'água":
    adicionar_marcadagua(uploaded_file)
elif menu == "Inserir páginas de outro PDF":
    inserir_paginas(uploaded_file)
elif menu == "Extrair texto":
    extrair_texto(uploaded_file)
elif menu == "Editar metadados":
    editar_metadados(uploaded_file)
elif menu == "Converter para Word":
    converter_para_word(uploaded_file)
elif menu == "Adicionar numeração":
    adicionar_numeracao(uploaded_file)
elif menu == "Remover numeração":
    remover_rodape(uploaded_file)
