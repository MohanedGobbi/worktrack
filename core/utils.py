import os
import re
import unicodedata

def sanitize_filename(filename):
    """
    Sanitize and repair uploaded file names automatically:
    - Preserves file extension.
    - Strips dangerous characters and path traversal symbols.
    - Replaces spaces and invalid symbols with clean underscores.
    - Preserves human readability and handles Arabic/Unicode safely.
    - Limits total base length to 100 characters to prevent path length errors.
    """
    if not filename:
        return "unnamed_file"

    # Extract base filename and extension
    clean_path = os.path.basename(str(filename))
    base, ext = os.path.splitext(clean_path)
    ext = ext.lower()

    # Normalize unicode (NFKC)
    base = unicodedata.normalize('NFKC', base)

    # Remove dangerous characters (/ \ : * ? " < > | % # & { } $ ! @ + = ~ ` ' etc)
    base = re.sub(r'[\\/*?:"<>|%#&{}$!@+=~`\'\s]+', '_', base)

    # Collapse consecutive underscores
    base = re.sub(r'__+', '_', base)
    base = base.strip('._-')

    # Fallback if base name becomes empty
    if not base:
        base = "attachment"

    # Truncate long base names
    if len(base) > 100:
        base = base[:100]

    return f"{base}{ext}"
