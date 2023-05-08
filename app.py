import os
import io
import json
import sys
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request, redirect, url_for
from flask import Flask, render_template, request, make_response
from googletrans import Translator


from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes, VisualFeatureTypes

credential = json.load(open('credential.json'))
API_KEY = credential['API_KEY']
ENDPOINT = credential['ENDPOINT']

cv_client = ComputerVisionClient(ENDPOINT, CognitiveServicesCredentials(API_KEY))

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_image():
    file = request.files['image']
    if not file:
        return "No image file selected!"
    
    # Save the uploaded image file to disk
    image_path = os.path.join('uploads', file.filename)
    file.save(image_path)

    response = cv_client.read_in_stream(open(image_path, 'rb'), Language='en', raw=True)
    operationLocation=response.headers['Operation-Location']
    operation_id = operationLocation.split('/')[-1]
    time.sleep(5)
    result = cv_client.get_read_result(operation_id)

    if result.status == OperationStatusCodes.succeeded:
        read_results = result.analyze_result.read_results

        extracted_text = ""
        for analyzed_result in read_results:
            for line in analyzed_result.lines:
                extracted_text += line.text + "\n"

        return render_template('index.html', extracted_text=extracted_text)
    else:
        return "Failed to extract text from the image."
@app.route('/download', methods=['POST'])
def download_text():
    text = request.form['text']
    response = make_response(text)
    response.headers['Content-Disposition'] = 'attachment; filename=extracted_text.txt'
    response.headers['Content-type'] = 'text/plain'
    return response

@app.route('/translate', methods=['POST'])
def translate():
	text = request.form['text']
	language = request.form['language']
	translator = Translator()
	translated = translator.translate(text, dest=language)
	return render_template('index.html', translated_text=translated.text)







if __name__ == '__main__':
    app.run(debug=True)