import pdfplumber
import re


def extract_pdf(file):
    """
    Extrai informações de uma Nota Fiscal de Serviços Eletrônica (NFS-e) em formato PDF.

    Args:
        file: O caminho para o arquivo PDF.

    Returns:
        Um dicionário contendo as informações extraídas.
    """

    info = {
        "emissor": None,
        "remetente": None,
        'numero': None,
        'valor': None
    }

    try:
        with pdfplumber.open(file) as nf:
            if not nf.pages:
                print("Aviso: O PDF não contém páginas.")
                return info
            
            page = nf.pages[0]
            text = page.extract_text(x_tolerance=2)

            if not text:
                print("Aviso: Não foi possível extrair texto da página.")
                return info

            padrao_cnpj = re.compile(r'(\d{2}[.\s]?\d{3}[.\s]?\d{3}/\d{4}-\d{2})')
            cnpjs_encontrados = padrao_cnpj.findall(text)
            
            if cnpjs_encontrados:
                info['emissor'] = cnpjs_encontrados[0]
                if len(cnpjs_encontrados) > 1:
                    info['remetente'] = cnpjs_encontrados[1]

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
                    alts = ['Número / Série', 'Número NFS-e', "Nro. Fatura", 'Número da NFS-e', 'Número da Nota', 'Numero da NFS-e:', 'Número/Série RP']
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
                re.compile(r'Valor :?\s+R\$\s*([\d.,]+)')
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
            
            return info

    except FileNotFoundError:
        print(f"Erro: O arquivo não foi encontrado em '{file}'")
        return info
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        return info