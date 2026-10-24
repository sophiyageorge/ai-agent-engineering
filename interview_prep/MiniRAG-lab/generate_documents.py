
from pathlib import Path
import random

BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "data" / "documents"

random.seed(42)

source_files = sorted(SOURCE_DIR.glob("*.txt"))

if not source_files:
    raise RuntimeError("No source documents found.")

source_documents = [
    (path.stem, path.read_text(encoding="utf-8").strip())
    for path in source_files
]

for target_count in [20, 200, 1000]:
    output_dir = BASE_DIR / "data" / f"dataset_{target_count}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Clean generated files from previous runs.
    for old_file in output_dir.glob("*.txt"):
        old_file.unlink()

    for i in range(target_count):
        source_name, source_text = source_documents[
            i % len(source_documents)
        ]

        text = (
            f"Document ID: {i:05d}\n"
            f"Topic: {source_name}\n"
            f"Dataset record: {i}\n\n"
            f"{source_text}"
        )

        # Add a deterministic variation so the records
        # are not byte-for-byte identical.
        variation = (i * 17) % 101

        text += (
            f"\n\nAdditional reference: {variation}. "
            f"This record belongs to dataset {target_count}."
        )

        path = output_dir / f"document_{i:05d}.txt"
        path.write_text(text, encoding="utf-8")

    print(f"Created {target_count} documents in {output_dir}")
