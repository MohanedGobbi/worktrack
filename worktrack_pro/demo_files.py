import os
def make_demo_files():
    os.makedirs('media/demo_docs', exist_ok=True)
    
    with open('media/demo_docs/sample_doc.txt', 'w') as f:
        f.write('This is a demo text document attached to the correspondence.')
    
    # Generate pdf
    os.system('echo "This is a demo PDF snippet" | pdftk - output media/demo_docs/sample_doc.pdf')
    
make_demo_files()
