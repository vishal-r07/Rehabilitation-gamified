import fitz
doc = fitz.open(r'c:\Users\visha\Downloads\game\ARIESv2 0_Datasheet_v2 .pdf')
with open(r'c:\Users\visha\Downloads\game\pdf_content.txt', 'w', encoding='utf-8') as f:
    for page in doc:
        f.write(page.get_text())
