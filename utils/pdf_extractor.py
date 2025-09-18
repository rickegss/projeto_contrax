import pdfplumber
import streamlit as st
import re

def _formatar_valor(valor_str):
    """Converte uma string de valor monetário para float."""
    if not valor_str:
        return None
    try:
        # Lida com formatos como "1.234,56" e "1,234.56"
        valor_limpo = valor_str.strip()
        if ',' in valor_limpo and '.' in valor_limpo:
            if valor_limpo.rfind('.') > valor_limpo.rfind(','):
                # Formato americano: 1,234.56 -> remove vírgulas
                valor_limpo = valor_limpo.replace(',', '')
            else:
                # Formato brasileiro: 1.234,56 -> remove pontos, troca vírgula
                valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
        else:
            # Formato 1234,56
            valor_limpo = valor_limpo.replace(',', '.')
            
        return float(valor_limpo)
    except (ValueError, TypeError):
        return None

# --- PARSERS ESPECÍFICOS PARA CADA LAYOUT ---

def _parse_joinville(text, lines):
    if 'Prefeitura de Joinville' not in text:
        return None
    info = {"numero": None, "valor": None}
    for i, linha in enumerate(lines):
        if 'Número / Série' in linha and i + 1 < len(lines):
            match = re.search(r'(\d+)\s*/', lines[i + 1])
            if match:
                info['numero'] = int(match.group(1))
    match_val = re.search(r"VALOR TOTAL DO SERVIÇO:\s*R\$\s*([\d.,]+)", text)
    if match_val:
        info['valor'] = _formatar_valor(match_val.group(1))
    return info if all(info.values()) else None

def _parse_sao_jose_campos(text, lines):
    if 'PREFEITURA DE SÃO JOSÉ DOS CAMPOS' not in text:
        return None
    info = {"numero": None, "valor": None}
    for i, linha in enumerate(lines):
        if 'Número / Série' in linha and i + 1 < len(lines):
            partes = lines[i + 1].strip().split()
            if len(partes) > 3:
                info['numero'] = int(partes[3])
        if 'VALOR TOTAL DA NOTA' in linha and i + 2 < len(lines):
            valor_str = lines[i + 2].strip().split()[-1]
            info['valor'] = _formatar_valor(valor_str)
    return info if all(info.values()) else None

def _parse_rps_generico(text, lines):
    if not text.startswith('NFS-e - NOTA FISCAL DE SERVIÇOS ELETRÔNICA - RPS '):
        return None
    info = {"numero": None, "valor": None}
    for i, linha in enumerate(lines):
        if 'NÚMERO DA NOTA' in linha and i + 1 < len(lines):
            partes = lines[i + 1].strip().split()
            if len(partes) > 1:
                info['numero'] = int(partes[-1].removeprefix("2025"))
    match_val = re.search(r"VALOR DOS SERVIÇOS:\s*R\$ ([\d.,]+)", text)
    if match_val:
        info['valor'] = _formatar_valor(match_val.group(1))
    return info if all(info.values()) else None

def _parse_florianopolis(text, lines):
    if 'PREFEITURA MUNICIPAL DE FLORIANÓPOLIS' not in text:
        return None
    info = {"numero": None, "valor": None}
    for i, linha in enumerate(lines):
        if 'Número da NFS-e' in linha and i + 1 < len(lines):
            match_num = lines[i + 1].split()
            if len(match_num) > 1:
                info['numero'] = int(match_num[-1])
    match_val = re.search(r"VALOR TOTAL DO SERVIÇO\s*R\$ ([\d.,]+)", text)
    if match_val:
        info['valor'] = _formatar_valor(match_val.group(1))
    return info if all(info.values()) else None

def _parse_goianesia(text, lines):
    if 'MUNICÍPIO DE GOIANESIA' not in text:
        return None
    info = {"numero": None, "valor": None}
    match_num = re.search(r'Nº\s*(\d+)', text)
    if match_num:
        info['numero'] = int(match_num.group(1))
    match_val = re.search(r"Valor da nota\s*R\$ ([\d.,]+)", text, flags=re.IGNORECASE)
    if match_val:
        info['valor'] = _formatar_valor(match_val.group(1))
    return info if all(info.values()) else None
    
def _parse_fatura_locacao(text, lines):
    if not text.startswith('FATURA DE LOCAÇÃO Nº'):
        return None
    info = {"numero": None, "valor": None}
    match_num = re.search(r'Nº\s*(\d+)', text)
    if match_num:
        info['numero'] = int(match_num.group(1))
    for i, linha in enumerate(lines):
        if 'Valor Total' in linha and i + 1 < len(lines):
            match_val = re.search(r'R\$ ([\d.,]+)', lines[i+1])
            if match_val:
                info['valor'] = _formatar_valor(match_val.group(1))
                break
    return info if all(info.values()) else None

def _parse_danfse_documento_auxiliar(text, lines):
    if 'DANFPS-E' not in text:
        return None
    info = {"numero": None, "valor": None}
    match_num = re.search(r'Numero\s*:\s*(\d+)', text)
    if match_num:
        info['numero'] = int(match_num.group(1))
    for i, linha in enumerate(lines):
        if 'Valor Total dos Serviços' in linha and i + 1 < len(lines):
            valor_str = lines[i + 1].strip().split()[-1]
            info['valor'] = _formatar_valor(valor_str)
            break
    return info if all(info.values()) else None
    
def _parse_danfe_generico(text, lines):
    keywords = [
        'OS PRODUTOS CONSTANTES DA NOTA FISCAL INDICADA AO LADO',
        'OS PRODUTOS E/OU SERVIÇOS CONSTANTES DA NOTA FISCAL ELETRÔNICA INDICADA AO LADO NF-e',
        'OS PRODUTOS E/OU SERVIÇOS CONSTANTES DA NOTA FISCAL ELETRÔNICA INDICADA NF-e',
        'OS PRODUTOS E/OU SERVIÇOS CONSTANTES DA NOTA FISCAL NF-e',
        'OS PRODUTOS / SERVIÇOS CONSTANTES DA NOTA FISCAL INDICADO AO LADO NF-e'
    ]
    if not any(kw in text for kw in keywords):
        return None
    info = {"numero": None, "valor": None}
    match_num = re.search(r'Nº\.?\s*([\d.]+)', text)
    if match_num:
        info['numero'] = int(match_num.group(1).replace('.', ''))
    for i, linha in enumerate(lines):
        if 'VALOR TOTAL DA NOTA' in linha or 'V ALOR TOTAL DA NOTA' in linha and i + 1 < len(lines):
            valor_str = lines[i + 1].strip().split()[-1]
            info['valor'] = _formatar_valor(valor_str)
            break
    return info if all(info.values()) else None

def _parse_goiania(text, lines):
    if 'GOIÂNIA / GO Data e Hora de Emissão' not in text:
        return None
    
    info = {"numero": None, "valor": None}
    
    for i, linha in enumerate(lines):   
        if 'Número NFS-e' in linha and i + 1 < len(lines):
            match_num = re.search(r'(\d+)', lines[i + 2])
            if match_num:
                info['numero'] = int(match_num.group(1))
                break   
    
    match_val = re.search(r'VALOR TOTAL DA NFS-e = R$\s*([\d.,]+)', text)
    if match_val:
        info['valor'] = _formatar_valor(match_val.group(1))

    return info if all(info.values()) else None
        
    
def _parse_fallback(text, lines):
    """Fallback genérico para tentar encontrar número e valor."""
    padroes_numero = [
        re.compile(r'Número NFS-e\s+(\d+)', re.IGNORECASE),
        re.compile(r'NOTA FISCAL DE SERVIÇOS DE TELECOMUNICAÇÕES Nº\s*[\n]?+(\d+)', re.IGNORECASE),
        re.compile(r'Número NFS-e\s*\n\s*([\d.,]+)', re.IGNORECASE),
        re.compile(r'Número da NFS-e\s*\n\s*([\d.,]+)', re.IGNORECASE),
        re.compile(r'Número da NFS-e\s+(\d+)', re.IGNORECASE),
        re.compile(r'Número / Série[^\n]*\n.*?(\d+)\s*/\s*E', re.IGNORECASE),
        re.compile(r'Número/Série RPS?.*?(\d+)\s*/', re.DOTALL | re.IGNORECASE),
        re.compile(r'Número da Nota\s+Série da Nota\s*\n(?:.*\s)?(\d+)', re.MULTILINE | re.IGNORECASE),
        re.compile(r'Número da Nota\s+(\d+)', re.IGNORECASE),
        re.compile(r'Número da Nota\s*[:\n]?\s*(\d+)', re.IGNORECASE),
        re.compile(r'Nro\.? Fatura\s+(\d+)', re.IGNORECASE),
        re.compile(r'N[º°o]\.?\s+(\d+)', re.IGNORECASE)
    ]

    info = {"numero": None, "valor": None}
    
    for padrao in padroes_numero:
        match_numero = padrao.search(text)
        if match_numero:
            numero_catch = match_numero.group(1).strip()
            
            contexto_match = match_numero.group(0)

            if not any(keyword in contexto_match for keyword in ["Rua", "Avenida", "Av", "Travessa", "R.", 'Praça', 'CEP', 'Centro']):
                info['numero'] = numero_catch
                break 

    if info['numero'] is None:
        linhas = text.split('\n')
        for i, linha in enumerate(linhas):
            alts = ['Número / Série', 'Número NFS-e', "Nro. Fatura", 'Número da NFS-e', 'Número da Nota', 'Numero da NFS-e:', 'Número/Série RP', 'Fatura de Locação :']
            for alt in alts:
                if alt in linha and info['numero'] is None: 
                    if i + 1 < len(linhas):
                        match = re.search(r'^\s*(\d+)\s*$', linhas[i + 1]) 
                        if match:
                            info['numero'] = match.group(1)
                            break
                    if info['numero'] is None and i + 2 < len(linhas):
                        match = re.search(r'^\s*(\d+)\s*$', linhas[i + 2]) 
                        if match:
                            info['numero'] = match.group(1)
                            break
            if info['numero'] is not None:
                break

    padroes_valor = [
        re.compile(r'VALOR TOTAL DA NOTA\s*\n\s*R?\$\s*([\d.,]+)', re.IGNORECASE),
        re.compile(r'Valor total da NFSe Campinas \(R\$\)[^\n]*\n\s*([\d.,]+)', re.IGNORECASE),
        re.compile(r'VALOR TOTAL DO SERVIÇO:?\s+R\$\s*([\d.,]+)', re.IGNORECASE),
        re.compile(r'VALOR DO IPI\s+VALOR TOTAL DA NOTA.*?R?\$\s*([\d.,]+)\s+R?\$\s*([\d.,]+)', re.DOTALL | re.IGNORECASE),
        re.compile(r'\(=?\)Valor da Nota\s*R\$\s*([\d.,]+)', re.IGNORECASE),
        re.compile(r'VALOR TOTAL:?\s*R\$\s*([\d.,]+)', re.IGNORECASE),
        re.compile(r'VALOR TOTAL DA NOTA\s+(?:R\$\s*)?([\d.,]+)', re.IGNORECASE),
        re.compile(r'VALOR TOTAL DOS PRODUTOS\s+(?:R\$\s*)?([\d.,]+)', re.IGNORECASE),
        re.compile(r'VALOR TOTAL DA NFS-e\s*=\s*R\$\s*([\d.,]+)', re.IGNORECASE),
        re.compile(r'VALOR LIQUIDO A PAGAR\s+(?:R\$\s*)?([\d.,]+)', re.IGNORECASE),
        re.compile(r'TOTAL A PAGAR\s+(?:R\$\s*)?([\d.,]+)', re.IGNORECASE),
        re.compile(r'Valor da Franquia Faturada: R\S\s*([\d.,]+)', re.IGNORECASE),
        re.compile(r'Total da Fatura\s+(?:R\$\s*)?([\d.,]+)', re.IGNORECASE),
        re.compile(r'Valor :?\s+R\$\s*([\d.,]+)', re.IGNORECASE)
    ]

    for padrao in padroes_valor:
        match_valor = padrao.search(text)
        if match_valor:
            valor_str = match_valor.group(match_valor.lastindex)
            
            try:
                valor_limpo = valor_str.replace('.', '').replace(',', '.')
                info['valor'] = float(valor_limpo)
                break
            except (ValueError, AttributeError):
                continue

    # Retorna apenas se encontrou algo, mesmo que parcial
    return info if any(info.values()) else None

# --- FUNÇÃO PRINCIPAL ---

@st.cache_data
def extract_pdf(file):
    """Extrai informações de um PDF fiscal tentando múltiplos parsers em ordem."""
    
    # Lista de parsers a serem tentados, do mais específico para o mais genérico
    parsers = [
        _parse_joinville,
        _parse_sao_jose_campos,
        _parse_rps_generico,
        _parse_florianopolis,
        _parse_goiania,
        _parse_goianesia,
        _parse_fatura_locacao,
        _parse_danfse_documento_auxiliar,
        _parse_danfe_generico
    ]

    info = {"numero": '', "valor": ''}

    try:
        with pdfplumber.open(file) as pdf:
            if not pdf.pages:
                st.warning("PDF sem páginas.")
                return info

            # Tenta a página 1 para notas de uma página, e a página 2 para DANFEs com canhoto
            page_index = 0 if len(pdf.pages) == 1 else 1
            if len(pdf.pages) > page_index:
                 page_text = pdf.pages[page_index].extract_text(x_tolerance=2) or ""
            else: # Fallback para a primeira página se a segunda não existir
                 page_text = pdf.pages[0].extract_text(x_tolerance=2) or ""
                 
            page_lines = page_text.split('\n')

            # Itera sobre os parsers e para no primeiro que retornar um resultado
            for parser in parsers:
                result = parser(page_text, page_lines)
                if result and result.get("numero") and result.get("valor"):
                    return result
                elif result: # Atualiza info com resultados parciais
                    info.update({k: v for k, v in result.items() if v is not None})
            
            # Se nenhum parser específico funcionou, tenta o fallback
            if not all(info.values()):
                 fallback_result = _parse_fallback(page_text, page_lines)
                 if fallback_result:
                     info.update({k: v for k, v in fallback_result.items() if v is not None})

            return info

    except Exception as e:
        st.warning(f"Ocorreu um erro ao processar o PDF: {e}")
        return info