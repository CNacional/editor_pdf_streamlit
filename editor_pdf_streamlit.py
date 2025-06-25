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
    "Remover numeração",
    "Remover baseado em texto"
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
            
        download_button(writer, "com_numeracao.pdf")

# Remove visualmente numeração cortando o rodapé
def remover_rodape(uploaded_file):
    largura = st.number_input("Largura da faixa branca (px)", min_value=100, max_value=800, value=600)
    altura = st.number_input("Altura da faixa branca (px)", min_value=10, max_value=200, value=40)
    y_base = st.number_input("Distância do rodapé até o topo da faixa (px)", min_value=0, max_value=300, value=0)
    cor = st.color_picker("Cor da faixa branca", value="#FFFFFF")
    paginas = st.text_input("Páginas a aplicar (ex: 1,3,5 ou deixe vazio para todas)")

    cor_rgb = tuple(int(cor.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))

    if uploaded_file:
        reader = PdfReader(uploaded_file)
        writer = PdfWriter()

        total_paginas = len(reader.pages)
        indices_aplicar = list(range(total_paginas))
        if paginas:
            indices_aplicar = [int(p.strip()) - 1 for p in paginas.split(',') if p.strip().isdigit() and 0 <= int(p.strip()) - 1 < total_paginas]

        st.subheader("Pré-visualização (primeira página aplicável):")
        if indices_aplicar:
            page_index = indices_aplicar[0]
            original_page = reader.pages[page_index]
            preview_writer = PdfWriter()

            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.setFillColorRGB(*cor_rgb)
            can.rect(x=0, y=y_base, width=largura, height=altura, fill=1, stroke=0)
            can.save()
            packet.seek(0)
            overlay = PdfReader(packet)
            preview_page = original_page
            preview_page.merge_page(overlay.pages[0])
            preview_writer.add_page(preview_page)

            preview_output = io.BytesIO()
            preview_writer.write(preview_output)
            preview_output.seek(0)
            b64_preview = base64.b64encode(preview_output.read()).decode('utf-8')
            pdf_display = f"""
            <iframe src="data:application/pdf;base64,{b64_preview}" width="700" height="1000" type="application/pdf"></iframe>
            """
            st.components.v1.html(pdf_display, height=1000)

        if st.button("Aplicar remoção de numeração"):
            for i, page in enumerate(reader.pages):
                if i in indices_aplicar:
                    packet = io.BytesIO()
                    can = canvas.Canvas(packet, pagesize=letter)
                    can.setFillColorRGB(*cor_rgb)
                    can.setLineWidth(0)
                    can.rect(x=0, y=y_base, width=largura, height=altura, fill=1, stroke=0)
                    can.save()
                    packet.seek(0)
                    overlay = PdfReader(packet)
                    page.merge_page(overlay.pages[0])
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

# Remover numeração baseada em texto

def remover_numeracao_baseado_texto(uploaded_file):
    limite_rodape = st.number_input("Limite do rodapé (px)", min_value=10, max_value=300, value=50)
    termos_comuns = st.text_input("Palavras a ignorar (separadas por vírgula)", value="pág,página")
    termos_lista = [t.strip().lower() for t in termos_comuns.split(',') if t.strip()]

    if uploaded_file:
        reader = PdfReader(uploaded_file)
        writer = PdfWriter()
        mascaras = []

        with pdfplumber.open(uploaded_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                words = page.extract_words()
                for w in words:
                    txt = w['text'].lower()
                    if any(p in txt for p in termos_lista) or txt.isdigit():
                        if float(w['bottom']) < limite_rodape:
                            mascaras.append((page_num, float(w['x0']), float(w['top']), float(w['x1']), float(w['bottom'])))

        if mascaras:
            st.success(f"{len(mascaras)} marca(s) de número identificada(s) para remoção.")

            # Pré-visualização da primeira página com remoção
            primeira_pagina = mascaras[0][0] if mascaras else 0
            page = reader.pages[primeira_pagina]
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            for m in mascaras:
                if m[0] == primeira_pagina:
                    x0, y_top, x1, y_bot = m[1], m[2], m[3], m[4]
                    can.setFillColorRGB(1, 1, 1)
                    can.setLineWidth(0)
                    can.rect(x0, y_bot, x1 - x0, y_top - y_bot, fill=1, stroke=0)
            can.save()
            packet.seek(0)
            overlay = PdfReader(packet)
            preview = page
            preview.merge_page(overlay.pages[0])

            preview_writer = PdfWriter()
            preview_writer.add_page(preview)
            preview_output = io.BytesIO()
            preview_writer.write(preview_output)
            preview_output.seek(0)
            b64_preview = base64.b64encode(preview_output.read()).decode('utf-8')
            st.subheader("Pré-visualização da primeira página com remoção:")
            st.components.v1.html(f"""
                <iframe src="data:application/pdf;base64,{b64_preview}" width="700" height="1000" type="application/pdf"></iframe>
            """, height=1000)

        if st.button("Aplicar remoção de numeração detectada"):
            for i, page in enumerate(reader.pages):
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                for m in mascaras:
                    if m[0] == i:
                        x0, y_top, x1, y_bot = m[1], m[2], m[3], m[4]
                        can.setFillColorRGB(1, 1, 1)
                        can.setLineWidth(0)
                        can.rect(x0, y_bot, x1 - x0, y_top - y_bot, fill=1, stroke=0)
                

            download_button(writer, "removido_texto.pdf")

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
elif menu == "Remover baseado em texto":
    remover_numeracao_baseado_texto(uploaded_file)
