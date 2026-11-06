import os
import zipfile

def make_demo_files():
    os.makedirs('media/demo_docs', exist_ok=True)
    
    # 1. Text
    with open('media/demo_docs/sample.txt', 'w') as f:
        f.write('This is a demo text document attached to the correspondence.')
    
    # 2. DOCX (needs minimum structure to be valid)
    with zipfile.ZipFile('media/demo_docs/sample.docx', 'w') as z:
        z.writestr('word/document.xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>This is a valid DOCX created for demo purposes!</w:t></w:r></w:p></w:body></w:document>')
        z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        
make_demo_files()
