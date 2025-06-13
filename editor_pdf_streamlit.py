import streamlit as st
import PyPDF2
import pdfplumber
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdf2docx import Converter
from io import BytesIO
import tempfile
import os

st.set_page_config(page_title="Editor de PDF", layout="centered")
st.title("🛠️ Editor de PDF Completo")

menu = st.sidebar.button("Escolha uma função:", [
    "Extrair páginas",
    "Mesclar PDFs",
    "Dividir PDF",
    "Rotacionar páginas",
    "Adicionar marca d'água",
    "Inserir páginas de outro PDF",
    "Extrair texto",
    "Editar metadados",
    "Converter para Word"
])

def salvar_pdf(writer):
    buffer = BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    return buffer

def criar_marca_dagua(texto):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica", 40)
    can.setFillAlpha(0.3)
    can.drawCentredString(300, 500, texto)
    can.save()
    packet.seek(0)
    return PyPDF2.PdfReader(packet)

if menu == "Extrair páginas":
    st.header("📄 Extrair páginas")
    pdf = st.file_uploader("Selecione o PDF", type="pdf")
    pags = st.text_input("Páginas a extrair (ex: 0,2,4)", placeholder="Use índice a partir do 0")

    if pdf and pags:
        reader = PyPDF2.PdfReader(pdf)
        writer = PyPDF2.PdfWriter()
        indices = [int(p.strip()) for p in pags.split(",")]
        for i in indices:
            writer.add_page(reader.pages[i])
        st.download_button("📥 Baixar PDF extraído", salvar_pdf(writer), file_name="extraido.pdf")

elif menu == "Mesclar PDFs":
    st.header("📎 Mesclar PDFs")
    arquivos = st.file_uploader("Selecione dois ou mais PDFs", type="pdf", accept_multiple_files=True)

    if arquivos and len(arquivos) >= 2:
        writer = PyPDF2.PdfWriter()
        for arquivo in arquivos:
            reader = PyPDF2.PdfReader(arquivo)
            for page in reader.pages:
                writer.add_page(page)
        st.download_button("📥 Baixar PDF mesclado", salvar_pdf(writer), file_name="mesclado.pdf")

elif menu == "Dividir PDF":
    st.header("✂️ Dividir PDF")
    pdf = st.file_uploader("Selecione o PDF", type="pdf")

    if pdf:
        reader = PyPDF2.PdfReader(pdf)
        for i, page in enumerate(reader.pages):
            writer = PyPDF2.PdfWriter()
            writer.add_page(page)
            st.download_button(f"📥 Página {i}", salvar_pdf(writer), file_name=f"pagina_{i}.pdf")

elif menu == "Rotacionar páginas":
    st.header("🔄 Rotacionar página")
    pdf = st.file_uploader("Selecione o PDF", type="pdf")
    pagina = st.number_input("Número da página (0 = primeira)", min_value=0, step=1)
    graus = st.selectbox("Rotação", [90, 180, 270])

    if pdf:
        reader = PyPDF2.PdfReader(pdf)
        writer = PyPDF2.PdfWriter()
        for i, page in enumerate(reader.pages):
            if i == pagina:
                page.rotate(graus)
            writer.add_page(page)
        st.download_button("📥 Baixar PDF rotacionado", salvar_pdf(writer), file_name="rotacionado.pdf")

elif menu == "Adicionar marca d'água":
    st.header("💧 Marca d'água")
    pdf = st.file_uploader("PDF de entrada", type="pdf")
    texto = st.text_input("Texto da marca d'água")

    if pdf and texto:
        reader = PyPDF2.PdfReader(pdf)
        writer = PyPDF2.PdfWriter()
        marca = criar_marca_dagua(texto)

        for i, page in enumerate(reader.pages):
            page.merge_page(marca.pages[0])
            writer.add_page(page)
        st.download_button("📥 Baixar PDF com marca d'água", salvar_pdf(writer), file_name="marca_dagua.pdf")

elif menu == "Inserir páginas de outro PDF":
    st.header("📑 Inserir páginas")
    pdf1 = st.file_uploader("PDF base", type="pdf", key="base")
    pdf2 = st.file_uploader("PDF a ser inserido", type="pdf", key="inserir")
    posicao = st.number_input("Posição onde inserir (0 = início)", min_value=0, step=1)

    if pdf1 and pdf2:
        r1 = PyPDF2.PdfReader(pdf1)
        r2 = PyPDF2.PdfReader(pdf2)
        writer = PyPDF2.PdfWriter()

        for i, page in enumerate(r1.pages):
            if i == posicao:
                for p in r2.pages:
                    writer.add_page(p)
            writer.add_page(page)

        st.download_button("📥 Baixar PDF final", salvar_pdf(writer), file_name="inserido.pdf")

elif menu == "Extrair texto":
    st.header("📝 Extrair texto")
    pdf = st.file_uploader("PDF para extrair texto", type="pdf")

    if pdf:
        with pdfplumber.open(pdf) as p:
            texto = "\n".join([page.extract_text() or '' for page in p.pages])
        st.text_area("Texto extraído", texto, height=300)
        st.download_button("📥 Baixar texto", texto, file_name="texto_extraido.txt")

elif menu == "Editar metadados":
    st.header("🧾 Editar metadados")
    pdf = st.file_uploader("PDF original", type="pdf")
    titulo = st.text_input("Título")
    autor = st.text_input("Autor")

    if pdf and (titulo or autor):
        reader = PyPDF2.PdfReader(pdf)
        writer = PyPDF2.PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        metadata = reader.metadata or {}
        if titulo:
            metadata["/Title"] = titulo
        if autor:
            metadata["/Author"] = autor
        writer.add_metadata(metadata)
        st.download_button("📥 Baixar PDF com metadados", salvar_pdf(writer), file_name="metadados.pdf")

elif menu == "Converter para Word":
    st.header("📄 Converter PDF para Word (.docx)")
    pdf = st.file_uploader("Selecione o PDF", type="pdf")

    if pdf:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(pdf.read())
            temp_pdf_path = temp_pdf.name

        output_docx = temp_pdf_path.replace(".pdf", ".docx")
        try:
            cv = Converter(temp_pdf_path)
            cv.convert(output_docx, start=0, end=None)
            cv.close()

            with open(output_docx, "rb") as f:
                st.download_button("📥 Baixar Word", f.read(), file_name="convertido.docx")
        finally:
            os.remove(temp_pdf_path)
            if os.path.exists(output_docx):
                os.remove(output_docx)
