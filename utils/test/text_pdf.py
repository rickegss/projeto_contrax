import pdfplumber

with pdfplumber.open(r'C:\Users\ricardo.gomes\Desktop\Python VS\projeto_contratos\data\NF_tests\U.pdf') as nf:
    page = nf.pages[0]
    text = page.extract_text(x_tolerance=2)
    print(text)