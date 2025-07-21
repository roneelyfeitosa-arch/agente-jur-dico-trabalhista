
import streamlit as st
import fitz  # PyMuPDF
import openai
import os
import pandas as pd
import json
import re
from docx import Document

openai.api_key = st.secrets["openai_api_key"]

st.set_page_config(page_title="Agente Jurídico Trabalhista", layout="wide")
st.image("logo.png", width=200)
st.title("🤖 Agente Jurídico Trabalhista - RF Group")

uploaded_file = st.file_uploader("📎 Envie a petição inicial (PDF)", type="pdf")
uploaded_reuniao = st.file_uploader("🗣️ Resumo da reunião (opcional)", type=["pdf", "txt"])

# Funções utilitárias
def extract_text_from_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def load_enunciados():
    try:
        with open("dados/enunciados_trt7.txt", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

def load_jurisprudencias():
    try:
        with open("dados/ojs_tst.json", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def load_precedentes():
    try:
        with open("dados/precedentes_tst.json", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def load_teses():
    try:
        return pd.read_excel("dados/teses.xlsx")
    except:
        return pd.DataFrame()

def build_prompt(peticao, reuniao, enunciados, jurisprudencias, precedentes, teses):
    bloco_juris = "\n".join([f"{j['tipo']} {j['numero']}: {j['resumo']} (Link: {j['link']})" for j in jurisprudencias])
    bloco_prec = "\n".join([f"Tese {p['numero']}: {p['resumo']} (Link: {p['link']})" for p in precedentes])
    bloco_teses = "\n".join([f"- {row['Pedido']}: {row['Linha de Defesa Padrão']}" for _, row in teses.iterrows()])
    return f'''
Você é um especialista jurídico. Analise o conteúdo abaixo e gere um relatório completo para defesa trabalhista empresarial contendo:

1. Nome do reclamante
2. Nome da empresa
3. Número do processo
4. Nome do advogado do reclamante
5. Resumo e detalhamento dos fatos alegados na petição inicial
6. Espelho dos cálculos apresentados
7. Relação de documentos anexados pela parte autora
8. Análise da convenção coletiva aplicável por cláusula vs pedidos
9. Jurisprudência correlata com base no TRT7, TST e precedentes
10. Risco estimado por pedido
11. Checklist de documentos a solicitar do cliente
12. Perguntas estratégicas a fazer ao cliente
13. Sugestões de defesa com base em teses padrões

📄 Petição inicial:
{peticao}

📌 Reunião com o cliente:
{reuniao if reuniao else 'Não enviada'}

📚 Enunciados TRT-7:
{enunciados}

📖 Jurisprudência:
{bloco_juris}

📌 Precedentes:
{bloco_prec}

📍 Teses padrão:
{bloco_teses}
'''

def gerar_docx(texto):
    doc = Document()
    for linha in texto.split("\n"):
        doc.add_paragraph(linha)
    path = "/mnt/data/relatorio_final.docx"
    doc.save(path)
    return path

def gerar_pdf(texto):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=11)
    for linha in texto.split("\n"):
        pdf.multi_cell(0, 10, linha)
    path = "/mnt/data/relatorio_final.pdf"
    pdf.output(path)
    return path

# Execução principal
if uploaded_file:
    with st.spinner("🧠 Lendo petição e gerando relatório..."):
        texto_peticao = extract_text_from_pdf(uploaded_file)
        texto_reuniao = extract_text_from_pdf(uploaded_reuniao) if uploaded_reuniao else ""
        enunciados = load_enunciados()
        jurisprudencias = load_jurisprudencias()
        precedentes = load_precedentes()
        teses = load_teses()
        prompt = build_prompt(texto_peticao, texto_reuniao, enunciados, jurisprudencias, precedentes, teses)
        resposta = openai.ChatCompletion.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
        output = resposta.choices[0].message.content
        docx_path = gerar_docx(output)
        pdf_path = gerar_pdf(output)

        st.success("✅ Relatório gerado!")
        st.download_button("📄 Baixar Word", open(docx_path, "rb"), file_name="relatorio_final.docx")
        st.download_button("📑 Baixar PDF", open(pdf_path, "rb"), file_name="relatorio_final.pdf")
        st.text_area("🧾 Conteúdo do Relatório", output, height=600)
