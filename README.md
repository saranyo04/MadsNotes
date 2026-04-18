
# Mad's Chinese

A desktop tool to convert Chinese text and PDFs into clean, readable study notes, optimized for browser extensions like Zhongwen.

---

Mad's Chinese turns messy Chinese input into structured, editable notes and generates a clean HTML page for laptop-based study.

It is a **local-first preprocessing tool**, not a dictionary.

## Features

- Paste Chinese text
- Upload or drag-and-drop selectable PDFs
- Automatic text extraction from PDFs
- Structured formatting for:
  - headings
  - lists
  - labels
  - paragraphs
- Built-in editor for manual correction
- Clean HTML output
- Opens in browser for Zhongwen hover lookup

## CLI Support

Open a PDF directly with the app:

```bash
madschinese.exe "C:\path\to\file.pdf"
````

Or during development:

```bash
python main.py "file.pdf"
```

## Setup

### Development

1. Install Python 3.11.9
2. Create and activate a virtual environment
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the app:

```bash
python main.py
```

### Build the .exe

1. Make sure dependencies are installed
2. Build the executable:

```bash
pyinstaller madschinese.spec
```

3. Find the app in:

```text
dist/
```

4. Open `madschinese.exe`

## Notes

* Works fully offline
* No accounts or cloud storage
* Uses browser extensions like Zhongwen for word lookup

## Author

Built as a personal tool for Chinese language study.