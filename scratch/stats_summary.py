from pathlib import Path

base = Path("D:/sovereign_gotham_data")
folders = ["crest_batch", "nsa", "army", "fbi"]

print("==========================================================================")
print("       SOVEREIGN GOTHAM // MULTI-AGENCY INTELLIGENCE DATA LAKE")
print("==========================================================================")

grand_chars = 0
grand_bytes = 0
grand_files = 0

for folder in folders:
    fpath = base / folder
    if not fpath.exists():
        continue
    txt_files = list(fpath.glob("*.txt"))
    all_files = list(fpath.glob("*.*"))
    chars = sum(len(f.read_text(encoding="utf-8", errors="ignore")) for f in txt_files)
    b_size = sum(f.stat().st_size for f in all_files)
    grand_chars += chars
    grand_bytes += b_size
    grand_files += len(all_files)
    print(f"[{folder.upper():12}] Records: {len(all_files):4} | Text Characters: {chars:10,} | Size: {b_size / (1024*1024):6.2f} MB")

print("--------------------------------------------------------------------------")
print(f"GRAND TOTAL RECORDS:    {grand_files} Intelligence Files")
print(f"GRAND TOTAL CHARACTERS: {grand_chars:,} Characters")
print(f"GRAND TOTAL DISK SIZE:  {grand_bytes / (1024*1024):.2f} MB")
print("==========================================================================")
