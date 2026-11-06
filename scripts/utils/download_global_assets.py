import os
import re
import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}

STATIC_DIR = "/home/pc-2026-1/Desktop/worktrack_pro_full_20260326_210548/static"
VENDOR_FONTS = os.path.join(STATIC_DIR, "vendor", "fonts")
VENDOR_LEAFLET = os.path.join(STATIC_DIR, "vendor", "leaflet")
IMAGES_LEAFLET = os.path.join(VENDOR_LEAFLET, "images")

os.makedirs(VENDOR_FONTS, exist_ok=True)
os.makedirs(IMAGES_LEAFLET, exist_ok=True)

def download_file(url, target_path):
    if not os.path.exists(target_path):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, context=ctx) as response, open(target_path, 'wb') as out_file:
                out_file.write(response.read())
            print(f"Downloaded: {url} -> {target_path}")
        except Exception as e:
            print(f"Failed to download {url}: {e}")

def process_fonts(css_url, output_css_name):
    req = urllib.request.Request(css_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            css_content = response.read().decode('utf-8')
    except Exception as e:
        print(f"Failed to download CSS {css_url}: {e}")
        return

    urls = re.findall(r'url\((https://[^)]+)\)', css_content)
    
    for i, url in enumerate(urls):
        filename = url.split('/')[-1]
        if '?' in filename:
            filename = filename.split('?')[0]
        if not filename.endswith('.woff2'):
            filename = f"corefont_{output_css_name.replace('.css', '')}_{i}.woff2"
            
        local_font_path = os.path.join(VENDOR_FONTS, filename)
        download_file(url, local_font_path)
        
        css_content = css_content.replace(url, f"./{filename}")
        css_content = css_content.replace(f'"{url}"', f'"./{filename}"')
        css_content = css_content.replace(f"'{url}'", f"'./{filename}'")

    out_css_path = os.path.join(VENDOR_FONTS, output_css_name)
    with open(out_css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)

if __name__ == '__main__':
    print("Downloading Core Django Fonts...")
    # Comprehensive font list from audit
    font_families = [
        "Inter:wght@300;400;500;600;700;800;900",
        "Plus+Jakarta+Sans:wght@300;400;500;600;700",
        "Space+Mono:ital,wght@0,400;0,700;1,400;1,700",
        "Manrope:wght@400;700;800",
        "Space+Grotesk:wght@300;400;500;600;700",
        "Outfit:wght@300;400;500;600;700;800;900",
        "Roboto:wght@300;400;500;700;900"
    ]
    fonts_url = f"https://fonts.googleapis.com/css2?family={'&family='.join(font_families)}&display=swap"
    process_fonts(fonts_url, "local_fonts.css")

    # Material Symbols
    print("Downloading Material Symbols...")
    process_fonts("https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap", "material_symbols.css")

    print("Downloading Tailwind CSS (v3 Standalone)...")
    os.makedirs(os.path.join(STATIC_DIR, "vendor", "tailwind"), exist_ok=True)
    download_file("https://cdn.tailwindcss.com", os.path.join(STATIC_DIR, "vendor", "tailwind", "tailwind.min.js"))

    print("Downloading Utility Libraries...")
    os.makedirs(os.path.join(STATIC_DIR, "vendor", "sortablejs"), exist_ok=True)
    download_file("https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js", os.path.join(STATIC_DIR, "vendor", "sortablejs", "sortable.min.js"))

    os.makedirs(os.path.join(STATIC_DIR, "vendor", "mammoth"), exist_ok=True)
    download_file("https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.4.21/mammoth.browser.min.js", os.path.join(STATIC_DIR, "vendor", "mammoth", "mammoth.min.js"))

    os.makedirs(os.path.join(STATIC_DIR, "vendor", "xlsx"), exist_ok=True)
    download_file("https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js", os.path.join(STATIC_DIR, "vendor", "xlsx", "xlsx.full.min.js"))

    print("Downloading Leaflet 1.9.4 Core...")
    download_file("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js", os.path.join(VENDOR_LEAFLET, "leaflet.js"))
    download_file("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css", os.path.join(VENDOR_LEAFLET, "leaflet.css"))

    print("Downloading Leaflet Images...")
    images = ['layers.png', 'layers-2x.png', 'marker-icon.png', 'marker-icon-2x.png', 'marker-shadow.png']
    for img in images:
        download_file(f"https://unpkg.com/leaflet@1.9.4/dist/images/{img}", os.path.join(IMAGES_LEAFLET, img))
        
    print("System Offline Scraper Complete!")
