# Local BECU OCR

The existing original PDFs and pypdf cache remain unchanged. OCR uses local Tesseract.js 7.0.0 (English) and pypdfium2 rendering at 216 DPI. No report is uploaded. On first use, Tesseract downloads its English language model; subsequent cached use is local.

Selected pages: 2023 pages 6, 8, 69-74; 2024 pages 7, 8, 10, 100-107. Of these 19 pages, only nine financial-table pages (2023 69-72; 2024 100-104) have visually reviewed searchable text. The other raw OCR pages remain excluded. This is targeted table recovery, not OCR coverage of every BECU page.

ocr-raw/ retains raw recognized text and confidence. ocr-pages.jsonl retains reviewed text and 119 contextual row passages; ocr-review-audit.json records character corrections and normalization. Every row repeats the relevant section, column years and printed units. Source SHA-256 and physical page are retained. Only reviewed=true records enter retrieval. Confidence alone does not authorize ingestion.

Reproduce from the project root:

1. Install pypdfium2 and an external local Node dependency tesseract.js@7.0.0. Set TESSERACT_JS_MODULE to its module directory if it is not on the Node resolution path.
2. python scripts/render_becu_ocr.py
3. node scripts/run_becu_ocr.cjs
4. Compare raw text with rendered physical pages. scripts/apply_reviewed_becu_ocr.py replays the specific recorded corrections for these source PDFs, then builds contextual passages. It is not a general automatic table validator. Verify source hashes and inspect any newly acquired or different scans before applying reviewed status.
5. python run.py index
6. python scripts/evaluate_after_ocr.py

Evaluation v3 changes A21/A22 to source evidence after physical-page verification, before scoring. The other question text, filters, labels, chunking settings, models, seed and ranking settings remain unchanged. Previous results remain in evaluation/expanded/post-table-fix/. The OCR run uses 34 evidence questions and four negatives; a fair before-after comparison rescored saved pre-OCR retrieved passages under the same v3 labels.
