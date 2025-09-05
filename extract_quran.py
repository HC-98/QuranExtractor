import sys
import re
import json
import subprocess
from pdf2image import convert_from_path
import pytesseract

# Usage: python3 extract_quran.py quran-dutch.pdf

if len(sys.argv) < 2:
    print("Usage: python3 extract_quran.py quran-dutch.pdf")
    sys.exit(1)

pdf_path = sys.argv[1]

print(f"Processing PDF: {pdf_path}")

# --- Helper: get total page count ---
def get_page_count(pdf_path):
    out = subprocess.check_output(["pdfinfo", pdf_path]).decode("utf-8")
    m = re.search(r"Pages:\s+(\d+)", out)
    return int(m.group(1))

total_pages = get_page_count(pdf_path)
print(f"Found {total_pages} pages")

data = {}
current_surah = 1
ayahs = {}

# Save raw OCR to log for inspection
raw_log = open("ocr-log.txt", "w", encoding="utf-8")

for i in range(1, total_pages + 1):
    print(f"OCR page {i}/{total_pages}...")
    pages = convert_from_path(pdf_path, dpi=300, first_page=i, last_page=i)
    page = pages[0]

    # OCR in Dutch
    text = pytesseract.image_to_string(page, lang="nld")

    raw_log.write(f"\n--- PAGE {i} ---\n{text}\n")

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Match lines like "1 In de naam van Allah..."
        match = re.match(r"^(\d+)\s+(.*)", line)
        if match:
            ayah_num, ayah_text = match.groups()
            ayah_num = int(ayah_num)

            # Detect new surah: if ayah resets to 1 and we already collected verses
            if ayah_num == 1 and ayahs:
                data[str(current_surah)] = ayahs
                current_surah += 1
                ayahs = {}

            ayahs[ayah_num] = ayah_text

# Save the last surah
if ayahs:
    data[str(current_surah)] = ayahs

raw_log.close()

# Write output JSON
out_file = "quran-dutch.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Done! Saved {out_file}")
print("📝 Also saved raw OCR text to ocr-log.txt for checking.")
