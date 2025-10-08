import pytesseract
from PIL import Image  # For opening the image

# Path to your Tesseract executable (if not in PATH; adjust as needed)
# pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'  # Example for Mac; comment out if not needed

# Load the image
image_path = '/Users/arielsanroj/Downloads/test1.jpg'  # Image from Downloads folder
img = Image.open(image_path)

# Run OCR
try:
    text = pytesseract.image_to_string(img)
    print("Extracted Text:")
    print(text)
except Exception as e:
    print(f"Error during OCR: {e}")