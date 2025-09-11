import pdfplumber

with pdfplumber.open(r'c:\Users\ricardo.gomes\H.Egidio Group\hcompany - Tecnologia\5-CONTRATO ASSINADO\01-NOTA_FISCAL\2025\09-25\INTEGRATTO-071 NF_1969 - 16.09.25.pdf') as nf:
    page = nf.pages[0]
    text = page.extract_text(x_tolerance=2)
    print(text)