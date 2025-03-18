import re
import cv2
import numpy as np
from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import os
import base64
from io import BytesIO
import requests

OCR_API_KEY = "K82862475188957"
OCR_URL = "https://api.ocr.space/parse/image"

app = Flask(__name__)

@app.route('/extract_text', methods=['POST'])
def extract_text():
    data = request.get_json()
    if 'image' not in data:
        return jsonify({"error": "No image data found"}), 400

    try:
        # Decode base64 image
        image_data = base64.b64decode(data['image'])
        
        # Send image to OCR.space API
        response = requests.post(
            OCR_URL,
            files={"image": ("image.png", image_data)},
            data={
                "apikey": OCR_API_KEY,
                "language": "eng",
                "isOverlayRequired": False
            },
        )

        result = response.json()
        
        # Extract text from OCR.space response
        if result["OCRExitCode"] == 1:
            extracted_text = result["ParsedResults"][0]["ParsedText"]
            print(extracted_text)  # Debugging

            # Pattern matching
            name_match = re.search(name_pattern, extracted_text)
            dob_match = re.search(dob_pattern, extracted_text)
            address_match = re.search(address_pattern, extracted_text)
            id_match = re.search(id_pattern, extracted_text)
            match = re.search(nationality_sex_birthday_pattern, extracted_text)

            id_corrected = re.sub(r"\b0(\d{2})\b", r"D\1", id_match.group(0)) if id_match else None

            response_data = {
                "name": name_match.group(0) if name_match else None,
                "address": address_match.group(0) if address_match else None,
                "id_number": id_corrected,
                "nationality": match.group(1) if match else None,
                "sex": match.group(2) if match else None,
                "birthday": match.group(3) if match else None,
            }

            return jsonify(response_data)

        else:
            return jsonify({"error": "OCR failed", "message": result.get("ErrorMessage", "Unknown error")}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
