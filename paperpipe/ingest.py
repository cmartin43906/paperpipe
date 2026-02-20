from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import shutil # for high level file operations

# just want the slugify function
from slugify import slugify

LIBRARY_DIR = Path("data/library")


@dataclass
class IngestResult:
    copied: int = 0
    moved: int = 0
    skipped_duplicate: int = 0
    rejected_non_pdf: int = 0
    failed: int = 0

# makes duplicate checking O(1)
def sha256_file(path: Path) -> str:
    """Compute SHA-256 for duplicate detection."""
    h = hashlib.sha256() # generate hash object that creates hash as you feed it data
    with path.open("rb") as f: # open as binary
        for chunk in iter(lambda: f.read(1024 * 1024), b""): 
            # process in chunks, read 1MB at a time until end
            # .read returns empty bytes when finished, that is EOF
            # iter(fn, stop value)
            h.update(chunk) # put these bytes into running calc
    # finalize the hash and return hex string
    return h.hexdigest()

# typer uses annotation to create Path obj
def is_pdf(path: Path) -> bool:
    """Simple PDF gate: extension check."""
    return path.is_file() and path.suffix.lower() == ".pdf"

# input normalizer
# can accept either a single file path or a directory path
# returns a list of file paths
# not recursive, only goes down one level
# fns are a bunch of thin wrappers around syscalls
def list_files(input_path: Path) -> list[Path]:
    """If file → [file]. If directory → list of immediate files."""
    if input_path.is_file():
        return [input_path] # wrap it in a list, bc later code will loop
    if input_path.is_dir():
        # interdir gives directory's immediate contents
        return [p for p in input_path.iterdir() if p.is_file()]
    return [] # path doesn't exist or is weird

# normalize the filenames
# stem is from Path and is the filename without the extension
# slugify does the normalization, spaces to hyphens
# max 80 chars
# placeholder for later naming strategy that will use metadata
# doesn't guarantee uniqueness
def safe_pdf_name(src: Path) -> str:
    """Make a safe filename based on the source stem."""
    # or paper just in case slugify returns empty string
    base = slugify(src.stem)[:80] or "paper"
    # force pdf extension
    return f"{base}.pdf"

# * forces arguments after it to be passed by keyword instead of position
# move = False means unless you say otherwise files are copied instead of moved
def intake(input_path: Path, *, move: bool = False) -> IngestResult:
    """
    Ingest a PDF file or a directory of files into data/library/.

    - Reject non-PDFs
    - Skip duplicates (SHA-256 match against existing library PDFs)
    - Copy by default; move if move=True
    """

    # make sure data/library exists before we try to put stuff there
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    # allows CLI to print summary at end
    result = IngestResult()

    candidates = list_files(input_path)
    # input validation
    if not candidates:
        print(f"[ERROR] No such file or directory: {input_path}")
        result.failed += 1
        return result

    # Hash existing library PDFs for duplicate detection.
    existing_hashes: set[str] = set()
    for existing in LIBRARY_DIR.glob("*.pdf"):
        try:
            existing_hashes.add(sha256_file(existing))
        except Exception as e:
            print(f"[WARN] Could not hash existing library file {existing.name}: {e}")

    for src in candidates:
        # We do per file error handling, because one bad file shouldn't stop the rest.
        try:

            # reject bad filetypes
            if not is_pdf(src):
                print(f"[REJECT] {src.name} (not a PDF)")
                result.rejected_non_pdf += 1
                continue

            # reject duplicates
            src_hash = sha256_file(src)
            if src_hash in existing_hashes:
                print(f"[SKIP] {src.name} (duplicate)")
                result.skipped_duplicate += 1
                continue

            dest_name = safe_pdf_name(src)
            # Path uses / as op overloading to join filenames
            dest = LIBRARY_DIR / dest_name

            # Avoid overwriting if the name collides by adding hash prefix.
            if dest.exists():
                dest = LIBRARY_DIR / f"{dest.stem}-{src_hash[:8]}{dest.suffix}"

            # move or copy based on caller direction
            # don't have to convert to strings, but cleaner
            if move:
                shutil.move(str(src), str(dest))
                print(f"[MOVE] {src.name} -> {dest}")
                result.moved += 1
            else:
                # copy2 preserves metadata
                shutil.copy2(str(src), str(dest))
                print(f"[COPY] {src.name} -> {dest}")
                result.copied += 1

            # update the duplicate test
            existing_hashes.add(src_hash)

        # If anything unexpected happens with this file, record and continue.
        except Exception as e:
            print(f"[FAIL] {src.name}: {e}")
            result.failed += 1

    return result