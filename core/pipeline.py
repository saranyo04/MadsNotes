from pathlib import Path
from utils.html_generator import generate_html
from utils.file_manager import create_job

def process_text(text):
    job_path = create_job()

    output_path = job_path / "output" / "study.html"

    generate_html(text, output_path)

    return str(output_path)