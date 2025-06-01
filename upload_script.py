import os
import requests
import logging
import json
from tqdm import tqdm

# CONFIG
PDF_DIR = "/path/to/your/pdf/directory"
ENDPOINT = "http://localhost:8000/create_knowledge_base"
PROGRESS_FILE = "upload_progress.json"

# Setup logging to file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    filename="upload_script.log",  # Log file name
    filemode="a"                   # Append mode, creates file if not exists
)

# Load or initialize progress
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r") as f:
        progress = json.load(f)
else:
    progress = {}

# Gather all PDF files
pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]

for pdf in tqdm(pdf_files, desc="Uploading PDFs"):
    if progress.get(pdf) == "uploaded":
        logging.info(f"Skipping already uploaded: {pdf}")
        continue

    file_path = os.path.join(PDF_DIR, pdf)
    try:
        with open(file_path, "rb") as f:
            files = [("files", (pdf, f, "application/pdf"))]
            response = requests.post(ENDPOINT, files=files)
        if response.status_code == 200:
            logging.info(f"Uploaded: {pdf}")
            progress[pdf] = "uploaded"
        else:
            logging.error(
                f"Failed to upload {pdf}: {response.status_code} "
                f"{response.text}"
            )
            progress[pdf] = f"error: {response.status_code}"
    except Exception as e:
        logging.error(f"Exception uploading {pdf}: {e}")
        progress[pdf] = f"exception: {str(e)}"

    # Save progress after each file
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

logging.info("Upload process complete.") 