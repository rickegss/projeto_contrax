import pdfplumber
import re

pdf_path = r'C:\Users\ricardo.gomes\Downloads\pdf_teste8.pdf'

info = {
    "cnpj": None,
    'numero': None,
    'valor': None,
}

try:
    with pdfplumber.open(pdf_path) as nf:
        page = nf.pages[0]
        text = page.extract_text(x_tolerance=2)

        match_cnpj = re.search(r'(\d{2}[.\s]?\d{3}[.\s]?\d{3}/\d{4}-\d{2})', text)
        if match_cnpj:
            info['cnpj'] = match_cnpj.group(1)

        padroes_numero = [
            re.compile(r'Número/Série RP.*?(\d+)\s*/', re.DOTALL | re.IGNORECASE),
            re.compile(r'Número da Nota\s+Série da Nota\s*\n(?:.*\s)?(\d+)', re.MULTILINE | re.IGNORECASE),
            re.compile(r'Número da Nota\s*[:\n]?\s*(\d+)', re.IGNORECASE),
            re.compile(r'N[º°o]\.?\s+(\d+)', re.IGNORECASE),
            re.compile(r'N[º°]\.\s+(\d+)', re.IGNORECASE),
            re.compile(r'Número / Série\s*(\d+)', re.IGNORECASE),
        ]
        
        for padrao in padroes_numero:
            match_numero = padrao.search(text)
            if match_numero:
                info['numero'] = match_numero.group(1).strip()
                break
        
        linhas = text.split('\n')
        for i, linha in enumerate(linhas):
            if 'VALOR DO FRETE' in linha and 'VALOR TOTAL DA NOTA' in linha:
                if i + 1 < len(linhas):
                    linha_valores = linhas[i + 1]
                    valores = linha_valores.strip().split(' ')
                    if valores:
                        valor_str = valores[-1]
                        try:
                            info['valor'] = float(valor_str.replace('.', '').replace(',', '.'))
                            break
                        except ValueError:
                            continue
        
        if info['valor'] is None:
            padroes_valor = [
                re.compile(r'VALOR TOTAL DO SERVIÇO:?\s+R\$\s*([\d.,]+)', re.IGNORECASE),
                re.compile(r'VALOR DO IPI\s+VALOR TOTAL DA NOTA.*?([\d.,]+)\s+([\d.,]+)', re.DOTALL | re.IGNORECASE),
                re.compile(r'\(=?\)Valor da Nota\s*R\$\s*([\d.,]+)', re.IGNORECASE),
                re.compile(r'VALOR TOTAL:?\s*R\$\s*([\d.,]+)', re.IGNORECASE),
                re.compile(r'VALOR TOTAL DA NOTA\s+(?:R\$\s*)?([\d.,]+)', re.IGNORECASE),
                re.compile(r'VALOR TOTAL DOS PRODUTOS\s+(?:R\$\s*)?([\d.,]+)', re.IGNORECASE),
                re.compile(r'VALOR TOTAL DA NFS-e\s*=\s*R\$\s*([\d.,]+)', re.IGNORECASE),
            ]

            for padrao in padroes_valor:
                match_valor = padrao.search(text)
                if match_valor:
                    if padrao.groups == 2:
                        valor_str = match_valor.group(2)
                    else:
                        valor_str = match_valor.group(1)
                    
                    try:
                        info['valor'] = float(valor_str.replace('.', '').replace(',', '.'))
                        break
                    except ValueError:
                        continue

        print(f"Resultado para '{pdf_path}':")
        print(info)
    
except FileNotFoundError:
    print(f"Erro: O arquivo não foi encontrado em '{pdf_path}'")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")