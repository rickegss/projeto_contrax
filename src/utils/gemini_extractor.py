import google.generativeai as genai
import streamlit as st
import json

API_KEY = st.secrets["gemini_api"]["API_KEY"]
genai.configure(api_key=API_KEY)

def process_invoice(uploaded_file):

    modelos = ["gemini-2.0-flash-lite", "gemini-2.5-flash-lite"]
    
    prompt = """
    Analise este documento fiscal e extraia estritamente em JSON:
    
    1. "numero_doc" (string): O número oficial da Nota Fiscal (NFS-e).
       - REGRA DE OURO: Se houver "RPS" e "Número da Nota", O RPS É O PROVISÓRIO (LIXO). Pegue a Nota Definitiva.
       - CASO COMO DE BARUERI/INGRAM: O número da nota é curto (ex: 116321) e o RPS é longo (ex: 000120343). ESCOLHA O CURTO.
       - Ignore rótulos "Fatura" ou "Pedido" se houver "Nota Fiscal".

    2. "valor_doc" (float): O valor líquido final a ser pago.
       - Se houver descontos ou retenções de impostos, pegue o valor final (Líquido).
       - Converta para float (ponto decimal).

    > Desconsidere zeros a esquerda no número do documento, caso seja do tipo 'NÚMERO / SÉRIE', retorne somente o número

    Retorne apenas: {"numero_doc": "...", "valor_doc": 0.00}
    """

    uploaded_file.seek(0)
    file_bytes = uploaded_file.getvalue()
    
    last_error = ""

    for nome_modelo in modelos:
        try:
            model = genai.GenerativeModel(
                nome_modelo,
                generation_config={"response_mime_type": "application/json"}
            )
            
            response = model.generate_content(
                [
                    {"mime_type": "application/pdf", "data": file_bytes},
                    prompt
                ]
            )
            
            return json.loads(response.text)
            
        except Exception as e:
            last_error = str(e)
            continue
            
    return {"error": f"Falha na API Gemini: {last_error}", "numero_doc": "", "valor_doc": 0.0}