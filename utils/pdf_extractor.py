import pdfplumber
import re

def extract_pdf(file):

    info = {
        "cnpj": None,
        'numero': None,
        'valor': None,
    }

    try:
        with pdfplumber.open(file) as nf:
            page = nf.pages[0]
            text = page.extract_text(x_tolerance=2)

            match_cnpj = re.search(r'(\d{2}[.\s]?\d{3}[.\s]?\d{3}/\d{4}-\d{2})', text)
            if match_cnpj:
                info['cnpj'] = match_cnpj.group(1)

            linhas = text.split('\n')
            for i, linha in enumerate(linhas):
                if ('Número / Série' in linha) != ('Número NFS-e' in linha):
                    if i + 1 < len(linhas):
                        linhas[i + 1].strip() 
                        match = re.search(r'\d+', linhas[i + 1])
                        if match:
                            info['numero'] = match.group()
                        break

            padroes_numero = [
                re.compile(r'Número NFS-e\s+(\d+)'),
                re.compile(r'Número / Série[^\n]*\n.*?(\d+)\s*/\s*E', re.IGNORECASE),
                re.compile(r'Número/Série RPS?.*?(\d+)\s*/', re.DOTALL | re.IGNORECASE),
                re.compile(r'Número da Nota\s+Série da Nota\s*\n(?:.*\s)?(\d+)', re.MULTILINE | re.IGNORECASE),
                re.compile(r'Número da Nota\s*[:\n]?\s*(\d+)', re.IGNORECASE),
                re.compile(r'N[º°o]\.?\s+(\d+)', re.IGNORECASE),
                re.compile(r'N[º°]\.\s+(\d+)', re.IGNORECASE),
            ]
            
            if info['numero'] == None:
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
                    # Padrão correto que busca o "Valor total da NFSe" na linha seguinte da tabela
                    re.compile(r'Valor total da NFSe Campinas \(R\$\)[^\n]*\n\s*([\d.,]+)', re.IGNORECASE),
                    re.compile(r'VALOR TOTAL DO SERVIÇO:?\s+R\$\s*([\d.,]+)', re.IGNORECASE),
                    re.compile(r'VALOR DO IPI\s+VALOR TOTAL DA NOTA.*?([\d.,]+)\s+([\d.,]+)', re.DOTALL | re.IGNORECASE),
                    re.compile(r'\(=?\)Valor da Nota\s*R\$\s*([\d.,]+)', re.IGNORECASE),
                    re.compile(r'VALOR TOTAL:?\s*R\$\s*([\d.,]+)', re.IGNORECASE),
                    re.compile(r'VALOR TOTAL DA NOTA\s+(?:R\$\s*)?([\d.,]+)', re.IGNORECASE),
                    re.compile(r'VALOR TOTAL DOS PRODUTOS\s+(?:R\$\s*)?([\d.,]+)', re.IGNORECASE),
                    re.compile(r'VALOR TOTAL DA NFS-e\s*=\s*R\$\s*([\d.,]+)', re.IGNORECASE),
                    re.compile(r'VALOR LIQUIDO A PAGAR\s+(?:R\$\s*)?([\d.,]+)', re.IGNORECASE)
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
            return info

    except FileNotFoundError:
        print(f"Erro: O arquivo não foi encontrado em '{file}'")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")