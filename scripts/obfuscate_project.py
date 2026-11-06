#!/usr/bin/env python3
"""
WorkTrack Pro - Production Build & Code Obfuscation Engine (CNRST)
Target Directory: PROD_CNRST

Obfuscates:
- Python files (*.py): Bytecode compilation + Zlib compression + Base64 exec wrapper
- HTML / Django Templates (*.html): Strips comments, minifies layout, obfuscates inline scripts/styles, encodes safe text blocks
- JavaScript files (*.js): Strips comments, minifies code, obfuscates via UTF-8 Base64 execution wrapper
- CSS files (*.css): Strips comments and minifies CSS rules
"""

import os
import re
import sys
import shutil
import base64
import zlib
import marshal

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_DIR = os.path.join(PROJECT_DIR, "PROD_CNRST")

EXCLUDE_DIRS = {
    "PROD_CNRST",
    ".venv",
    ".venv_trans",
    "venv",
    ".git",
    ".vscode",
    ".idea",
    "backup",
    "logs",
    "staticfiles",
    "node_modules",
    "__pycache__",
    ".translation_cache",
    "tmp",
}

EXCLUDE_FILES = {
    ".DS_Store",
    ".server.pid",
    "cookies.txt",
    "docker_up.log",
    "test_out.txt",
    "test_output.txt",
    "test_worker_out.txt",
    "test_worker_out2.txt",
    "tmp_raw_home.html",
    "tmp_translations_error.html",
}

EXCLUDE_EXTENSIONS = {
    ".pyc", ".pyo", ".sqlite3-journal", ".sqlite3-wal", ".sqlite3-shm", ".tar.gz", ".zip"
}


def obfuscate_python_code(source_code, rel_path="<string>"):
    """
    Obfuscates Python source code by compiling it into bytecode,
    compressing with zlib, encoding with Base64, and wrapping in a self-executing payload.
    """
    if not source_code.strip():
        return source_code

    # Extract shebang if present
    shebang = ""
    lines = source_code.splitlines(True)
    if lines and lines[0].startswith("#!"):
        shebang = lines[0]
        source_code = "".join(lines[1:])

    try:
        code_obj = compile(source_code, rel_path, 'exec')
        marshalled = marshal.dumps(code_obj)
        compressed = zlib.compress(marshalled, level=9)
        b64_payload = base64.b64encode(compressed).decode('ascii')

        obfuscated = (
            f"{shebang}"
            f"# WorkTrack Pro Obfuscated Build (CNRST)\n"
            f"import base64, marshal, zlib\n"
            f"exec(marshal.loads(zlib.decompress(base64.b64decode({repr(b64_payload)}))))\n"
        )
        return obfuscated
    except Exception as e:
        print(f"  [!] Warning: Failed to obfuscate python file '{rel_path}': {e}")
        return source_code


def obfuscate_js_code(js_code):
    """
    Obfuscates JavaScript code by stripping comments, minifying whitespace,
    and wrapping in a Base64 decodeURIComponent execution wrapper.
    """
    if not js_code.strip():
        return js_code

    # Remove single-line comments (preserving URLs like http://)
    cleaned = re.sub(r'(?<!:)\/\/.*?\n', '\n', js_code)
    # Remove multi-line comments
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)

    # Minify lines
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    minified = " ".join(lines)

    if not minified:
        return js_code

    # UTF-8 safe Base64 encoding
    encoded = base64.b64encode(minified.encode('utf-8')).decode('ascii')
    obfuscated = f"eval(decodeURIComponent(escape(atob('{encoded}'))));"
    return obfuscated


def obfuscate_css_code(css_code):
    """
    Minifies and obfuscates CSS code by removing comments and unnecessary spaces.
    """
    if not css_code.strip():
        return css_code

    # Remove comments
    cleaned = re.sub(r'/\*.*?\*/', '', css_code, flags=re.DOTALL)
    # Collapse whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\s*([\{\}\:\;\,\>])\s*', r'\1', cleaned)
    return cleaned.strip()


def obfuscate_html_template(html_code):
    """
    Obfuscates HTML and Django Templates by removing Django/HTML comments,
    minifying HTML markup, obfuscating embedded scripts and styles, and encoding text blocks.
    Preserves all Django template tags ({% ... %} and {{ ... }}).
    """
    if not html_code.strip():
        return html_code

    # 1. Remove Django comments {# ... #}
    html_code = re.sub(r'\{#.*?#\}', '', html_code, flags=re.DOTALL)
    # 2. Remove Django comment blocks {% comment %}...{% endcomment %}
    html_code = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', html_code, flags=re.DOTALL)
    # 3. Remove HTML comments <!-- ... -->
    html_code = re.sub(r'<!--.*?-->', '', html_code, flags=re.DOTALL)

    # Tokenize HTML template code into Django tags, HTML tags, scripts, styles, and text
    # Pattern matches Django tags {% ... %} or {{ ... }}, script tags, style tags, HTML tags
    pattern = re.compile(
        r'(\{%[sS]*?%\}|\{\{[\s\S]*?\}\}|<script[\s\S]*?>[\s\S]*?</script>|<style[\s\S]*?>[\s\S]*?</style>|<[^>]+>)',
        re.IGNORECASE
    )

    parts = pattern.split(html_code)
    result = []

    for part in parts:
        if not part:
            continue
        if part.startswith('{%') or part.startswith('{{'):
            # Preserve Django template tags verbatim
            result.append(part)
        elif part.lower().startswith('<script'):
            # Handle inline script tag
            script_match = re.match(r'(<script[\s\S]*?>)([\s\S]*?)(</script>)', part, re.IGNORECASE)
            if script_match:
                open_tag, script_body, close_tag = script_match.groups()
                obf_body = obfuscate_js_code(script_body)
                result.append(f"{open_tag}{obf_body}{close_tag}")
            else:
                result.append(part)
        elif part.lower().startswith('<style'):
            # Handle inline style tag
            style_match = re.match(r'(<style[\s\S]*?>)([\s\S]*?)(</style>)', part, re.IGNORECASE)
            if style_match:
                open_tag, style_body, close_tag = style_match.groups()
                obf_body = obfuscate_css_code(style_body)
                result.append(f"{open_tag}{obf_body}{close_tag}")
            else:
                result.append(part)
        elif part.startswith('<') and part.endswith('>'):
            # Minify HTML tag spaces inside tag
            tag_min = re.sub(r'\s+', ' ', part)
            result.append(tag_min)
        else:
            # Plain text content outside tags: convert alphabetic text into HTML hex entities
            text_lines = part.splitlines()
            obf_lines = []
            for line in text_lines:
                if not line.strip():
                    obf_lines.append(line)
                    continue
                # Hex entity encode characters in safe plain text (preserving spaces)
                encoded_chars = []
                for char in line:
                    if char.isalnum():
                        encoded_chars.append(f"&#x{ord(char):x};")
                    else:
                        encoded_chars.append(char)
                obf_lines.append("".join(encoded_chars))
            result.append("\n".join(obf_lines))

    # Minify overall layout lines
    minified_template = "".join(result)
    return minified_template


def process_file(src_path, dst_path, rel_path):
    """
    Copies file from src_path to dst_path, applying appropriate obfuscation based on extension.
    """
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    ext = os.path.splitext(src_path)[1].lower()
    filename = os.path.basename(src_path)

    if filename in EXCLUDE_FILES or ext in EXCLUDE_EXTENSIONS:
        return

    try:
        if ext == ".py":
            with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            obfuscated = obfuscate_python_code(content, rel_path=rel_path)
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(obfuscated)
            # Copy executable permissions if source had them
            if os.access(src_path, os.X_OK):
                os.chmod(dst_path, 0o755)

        elif ext == ".html":
            with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            obfuscated = obfuscate_html_template(content)
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(obfuscated)

        elif ext == ".js":
            with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            obfuscated = obfuscate_js_code(content)
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(obfuscated)

        elif ext == ".css":
            with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            obfuscated = obfuscate_css_code(content)
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(obfuscated)

        else:
            # Copy non-code files (images, fonts, binary, json, etc.) directly
            shutil.copy2(src_path, dst_path)

    except Exception as e:
        print(f"  [!] Error processing {rel_path}: {e}")
        # Fallback to direct copy
        shutil.copy2(src_path, dst_path)


def generate_production_package():
    """
    Main entry point for generating the PROD_CNRST obfuscated project copy.
    """
    print(f"\n=======================================================")
    print(f"🚀 WorkTrack Pro - Generating Obfuscated Production Copy")
    print(f"   Source : {PROJECT_DIR}")
    print(f"   Target : {TARGET_DIR}")
    print(f"=======================================================\n")

    if os.path.exists(TARGET_DIR):
        print(f"ℹ Cleaning previous '{os.path.basename(TARGET_DIR)}' folder...")
        shutil.rmtree(TARGET_DIR)

    os.makedirs(TARGET_DIR, exist_ok=True)

    py_count = 0
    html_count = 0
    js_count = 0
    css_count = 0
    other_count = 0

    for root, dirs, files in os.walk(PROJECT_DIR):
        # Prune excluded directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

        rel_root = os.path.relpath(root, PROJECT_DIR)
        if rel_root == ".":
            rel_root = ""

        for file in files:
            if file in EXCLUDE_FILES:
                continue
            ext = os.path.splitext(file)[1].lower()
            if ext in EXCLUDE_EXTENSIONS:
                continue

            src_file_path = os.path.join(root, file)
            rel_file_path = os.path.join(rel_root, file) if rel_root else file
            dst_file_path = os.path.join(TARGET_DIR, rel_file_path)

            process_file(src_file_path, dst_file_path, rel_file_path)

            if ext == ".py":
                py_count += 1
            elif ext == ".html":
                html_count += 1
            elif ext == ".js":
                js_count += 1
            elif ext == ".css":
                css_count += 1
            else:
                other_count += 1

    # Ensure SQLite snapshot if db.sqlite3 exists in main project
    db_src = os.path.join(PROJECT_DIR, "db.sqlite3")
    db_dst = os.path.join(TARGET_DIR, "db.sqlite3")
    if os.path.exists(db_src) and not os.path.exists(db_dst):
        print("ℹ Copying live SQLite database snapshot to PROD_CNRST...")
        shutil.copy2(db_src, db_dst)

    print("\n=======================================================")
    print("✓ Obfuscated Production Build Generated Successfully!")
    print(f"  📁 Output Directory : {TARGET_DIR}")
    print(f"  🐍 Obfuscated Python (.py)    : {py_count} files")
    print(f"  📄 Obfuscated HTML Templates  : {html_count} files")
    print(f"  ⚡ Obfuscated JavaScript (.js) : {js_count} files")
    print(f"  🎨 Obfuscated CSS (.css)        : {css_count} files")
    print(f"  📦 Other Assets Copied        : {other_count} files")
    print("=======================================================\n")


if __name__ == "__main__":
    generate_production_package()
