import pdfplumber
import streamlit as st
import re

@st.cache_data
def extract_pdf(file):
    """Extrai informações de uma Nota Fiscal de Serviços Eletrônica (NFS-e) em PDF."""

    info = {
        "numero": None,
        "valor": None
    }

    try:
        with pdfplumber.open(file) as nf:
            if not nf.pages:
                print("Aviso: PDF sem páginas")
                return info

            page = nf.pages[0] if len(nf.pages) == 1 else nf.pages[1]
            text = page.extract_text(x_tolerance=2)
            line = text.split('\n')

            if not text:
                print("Aviso: Não foi possível extrair texto")
                return info

            if 'Prefeitura de Joinville' in text:
                for i, linha in enumerate(line):
                    if 'Número / Série' in linha:
                        if i + 1 < len(line):
                            next = line[i + 1].strip()
                            info['numero'] = int(re.search(r'(\d+)\s*/\s*([^\d\s]+)', next).group(1))
                
                match_val = re.search(r"VALOR TOTAL DO SERVIÇO:\s*R\$\s*([\d\.]+,\d{2})", text)
                if match_val:
                    info['valor'] = float(match_val.group(1).replace('.', '').replace(',', '.'))

            elif 'PREFEITURA DE SÃO JOSÉ DOS CAMPOS' in text:
                for i, linha in enumerate(line):
                    if 'Data e Hora de Emissão da NFS-e Competência da NFS-e Número / Série Código de Verificação' in linha:
                        if i + 1 < len(line):
                            linha_seguinte = line[i + 1].strip()
                            partes = linha_seguinte.split(' ')
                            if len(partes) > 4:
                                info['numero'] = int(partes[3])
                    
                    if 'VALOR TOTAL DA NOTA' in linha:
                        if i + 2 < len(line):
                            linha_valor = line[i + 2].strip()
                            match_val = linha_valor.split(' ')[-1]
                            match_val = match_val.replace('.', '').replace(',', '.')
                            info['valor'] = float(match_val)

            elif text.startswith('NFS-e - NOTA FISCAL DE SERVIÇOS ELETRÔNICA - RPS '):
                for i,linha in enumerate(line):
                    if 'NÚMERO DA NOTA' in linha:
                        if i + 1 < len(line):
                            linha_seguinte = line[i + 1].strip()
                            partes = linha_seguinte.split(' ')
                            if len(partes) > 1:
                                info['numero'] = int(partes[-1].removeprefix("2025"))
                    

                match_val = re.search(r"VALOR DOS SERVIÇOS:\s*R\$ ([\d\.]+,\d{2})", text)
                if match_val:
                    valor_str = match_val.group(1)   
                    valor_str = valor_str.replace('.', '')  
                    valor_str = valor_str.replace(',', '.')  
                    info['valor'] = float(valor_str) 

            elif 'PREFEITURA MUNICIPAL DE FLORIANÓPOLIS' in text:
                for i, linha in enumerate(line):
                    if 'Número da NFS-e' in linha:
                        if i + 1 < len(line):
                            linha_seguinte = line[i + 1]
                            match_num = linha_seguinte.split()
                            if len(match_num) > 1:
                                info['numero'] = int(match_num[-1])  

                match_val = re.search(r"VALOR TOTAL DO SERVIÇO\s*R\$ ([\d\.]+(?:[,.]\d{2})?)", text)
                if match_val:
                    valor_str = match_val.group(1)   
                    valor_str = valor_str.replace('.', ',')  
                    valor_str = valor_str.replace(',', '.')  
                    info['valor'] = float(valor_str) 
        
            elif 'MUNICÍPIO DE GOIANESIA' in text:
                info['numero'] = int(re.search(r'Nº\s*(\d+)', text).group(1))
                info['valor'] = re.search(r"Valor da nota\s*R\$ ([\d\.]+(?:[,.]\d{2})?)",text, flags=re.IGNORECASE).group(1)
                info['valor'] = float(info['valor'].replace('.', '').replace(',', '.'))

            elif text.startswith('FATURA DE LOCAÇÃO Nº'):
                info['numero'] = int(re.search(r'Nº\s*(\d+)', text).group(1))
                for i, linha in enumerate(line):
                    if 'Valor Total' in linha:
                        if i + 1 < len(line):
                            linha_seguinte = line[i + 1].strip()
                            valor_match = re.search(r'R\$ ([\d\.]+(?:[,.]\d{2})?)', linha_seguinte)
                            if valor_match:
                                valor_str = valor_match.group(1).replace('.', '').replace(',', '.')
                                info['valor'] = float(valor_str)
                        break

            elif text.startswith('Prefeitura de Goiânia'):
                info['numero'] = int(re.search(r'Número da Nota\s*(\d+)', text).group(1))
                for i,linha in enumerate(line):
                    if 'Valor da Nota' in linha:
                        if i + 1 < len(line):
                            linha_seguinte = line[i + 1].strip()    
                            info['valor'] = float(linha_seguinte.split()[-1].replace('.', '').replace(',', '.'))

            elif text.startswith('NFS-e - NOTA FISCAL DE SERVIÇOS ELETRÔNICA'):
                numero_match = re.search(r'Nº:\s*2025/?(\d+)', text)
                if numero_match:
                    info['numero'] = int(numero_match.group(1))

                valor_match = re.search(r'Valor dos serviços:\s*R\$ ([\d.,]+)', text)
                if valor_match:
                    valor_str = valor_match.group(1).replace('.', '').replace(',', '.')
                    info['valor'] = float(valor_str)

            elif 'Governo do Distrito Federal' in text:
                for i,linha in enumerate(line):
                    if 'Número da Nota Fiscal' in linha:
                        if i + 1 < len(line):
                            linha_seguinte = line[i + 1].strip()
                            info['numero'] = int(linha_seguinte.split()[-1])
                            break

                match_val = re.search(r"Vl\.\s+Líquido\s+da\s+Nota\s+Fiscal.*R\$\s+([\d.,]+)", text, re.DOTALL)
                    
                if match_val:
                        valor_str = match_val.group(1)
                        valor_str = valor_str.replace('.', '').replace(',', '.')
                        info['valor'] = float(valor_str)

            elif (line[0].startswith('PREFEITURA MUNICIPAL DE')) and ('ARACAJU' in line[1]):
                for i,linha in enumerate(line):
                    if 'Número da NFS-e Competência da NFS-e Data e Hora da emissão da NFS-e' in linha:
                        if i + 1 < len(line):
                            linha_seguinte = line[i + 1].strip()
                            info['numero'] = int(linha_seguinte.split()[0])
                    
                    if 'Valor Líquido da NFS-e' in linha:
                        if i + 1 < len(line):
                            linha_seguinte = line[i + 1].strip()
                            info['valor'] = linha_seguinte.split()[-1]
                            info['valor'] = float(info['valor'].replace('.', '').replace(',', '.'))

            elif 'PREFEITURA MUNICIPAL DE ARACAJU' in text:
                for i,linha in enumerate(line):
                    if 'Valor Total da Nota (R$)' in linha:
                        if i + 1 < len(line):
                            linha_seguinte = line[i + 1].strip()
                            info['valor'] = linha_seguinte.split()[-1]
                            info['valor'] = float(info['valor'].replace('.', '').replace(',', '.'))

            elif 'Telecomunicação | Modelo ' in text:
                for i, linha in enumerate(line):
                   if 'Duplicatas' in linha:
                       if i + 1 < len(line):
                           linha_seguinte = line[i + 1].strip()
                
                           info['numero'] = int(re.search(r'Numero:?\s*(\d+)', linha_seguinte).group(1))

                           info['valor'] = re.search(r'Valor\s*:\s*R\$\s*([\d.,]+)', linha_seguinte).group(1)
                           info['valor'] = info['valor'].replace('.', '').replace(',', '.')
                           info['valor'] = float(info['valor'])

            elif 'PREFEITURA MUNICIPAL DE' in text and 'GOIÂNIA / GO Data e Hora de Emissão' in text:
                for i,linha in enumerate(line):
                    if 'Número NFS-e' in linha:
                        if i + 2 < len(line):
                            linha_2seguinte = line[i + 2].strip()
                            info['numero'] = int(linha_2seguinte)

                    if 'VALOR TOTAL DA NFS-e' in linha:
                        info['valor'] = linha.strip().split()[-1]
                        info['valor'] = info['valor'].replace('.', '').replace(',', '.')
                        info['valor'] = float(info['valor'])

            elif 'DANFPS-E' in text:
                info['numero'] = int(re.search(r'Numero\s*:\s*(\d+)', text).group(1))
                
                for i,linha in enumerate(line):
                    if 'Valor Total dos Serviços' in linha:
                        if i + 1 < len(line):
                            linha_seguinte = line[i + 1].strip()            
                            info['valor'] = linha_seguinte.split()[-1]
                            info['valor'] = info['valor'].replace('.', '').replace(',', '.')
                            info['valor'] = float(info['valor'])

            elif 'OS PRODUTOS CONSTANTES DA NOTA FISCAL INDICADA AO LADO' in text \
            or 'OS PRODUTOS E/OU SERVIÇOS CONSTANTES DA NOTA FISCAL ELETRÔNICA INDICADA AO LADO NF-e' in text \
                or 'OS PRODUTOS E/OU SERVIÇOS CONSTANTES DA NOTA FISCAL ELETRÔNICA INDICADA NF-e' in text \
                    or 'OS PRODUTOS E/OU SERVIÇOS CONSTANTES DA NOTA FISCAL NF-e' in text \
                        or 'OS PRODUTOS / SERVIÇOS CONSTANTES DA NOTA FISCAL INDICADO AO LADO NF-e' in text:
                info['numero'] = int(re.search(r'Nº.?\s*([\d.]+)', text).group(1).replace('.', ''))

                for i,linha in enumerate(line):
                    if 'VALOR TOTAL DA NOTA' in linha or 'V ALOR TOTAL DA NOTA' in linha:
                        if i + 1 < len(line):
                            linha_seguinte = line[i + 1].strip()
                            info['valor'] = linha_seguinte.split()[-1]  
                            info['valor'] = float(info['valor'].replace('.', '').replace(',', '.'))
                        if not info['valor']:
                            if 'VALOR TOTAL DOS PRODUTOS' in linha:
                                if i + 1 < len(line):
                                    linha_seguinte = line[i + 1].strip()
                                    info['valor'] = linha_seguinte.split()[-1]  
                                    info['valor'] = float(info['valor'].replace('.', '').replace(',', '.'))

            elif 'PREFEITURA MUNICIPAL DE BARUERI' in text:
                for i,linha in enumerate(line):
                  if 'Número da Nota Série da Nota' in linha:
                        if i + 1 < len(line):
                            prox = line[i + 1].strip()
                            num_match = re.search(r'\d{5,}', prox)  # número com pelo menos 5 dígitos
                            if num_match:
                                info['numero'] = int(num_match.group())
                                continue 

                        if i + 2 < len(line):
                            prox2 = line[i + 2].strip()
                            num_match = re.search(r'\d{5,}', prox2)
                            if num_match:
                                info['numero'] = int(num_match.group())

                match_valor = re.search(r'VALOR TOTAL DA NOTA\s*R?\$?\s*([\d.]+,\d{2})', text)
                if match_valor:
                    valor_str = match_valor.group(1)
                    info['valor'] = float(valor_str.replace('.', '').replace(',', '.'))

            elif text.startswith('RECIBO PROVISÓRIO DE SERVIÇOS - RPS'):
                for i, linha in enumerate(line):
                    if 'Número/Série RP' in linha:
                        if i + 1 < len(line):
                            prox = line[i + 1].strip()
                            tokens = prox.split()[::-1]  
                            for t in tokens:
                                if t.isdigit():
                                    info['numero'] = int(t)
                                    break

                match_valor = re.search(r'VALOR TOTAL DO SERVIÇO\s*R?\$?\s*([\d.]+,\d{2})', text)
                if match_valor:
                    valor_str = match_valor.group(1)
                    info['valor'] = float(valor_str.replace('.', '').replace(',', '.'))

            elif text.startswith('Prefeitura Municipal Campinas'):
                for i, linha in enumerate(line):
                    if 'Competência Número / Série Verificação' in linha:
                        if i + 1 < len(line):
                            prox = line[i + 1].strip()
                            tokens = prox.split()[::-1] 
                            for t in tokens:
                                if t.isdigit():
                                    info['numero'] = int(t)
                                    break

                match_valor = re.search(r'VALOR\s+LIQUIDO\s+A\s+PAGAR:\s*R?\$?\s*([\d.]+,\d{2})', text)
                if match_valor:
                    valor_str = match_valor.group(1)
                    info['valor'] = float(valor_str.replace('.', '').replace(',', '.'))

    except:
        pass
                                                                                                    
    return info