"""
Information: tests the api provided by web service
"""

# imports
import base64
from io import BytesIO
from PIL import Image
import requests
import json

# Get image and convert to base 64
buffered = BytesIO()
image = Image.open((input("Filename: ")))
image.save(buffered, format="JPEG")
img_str = base64.b64encode(buffered.getvalue())

# prepare headers for html POST request
headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

# clean b64 img string 
img_str = str(img_str).replace("b'",'')
img_str = str(img_str).replace("'",'')

# get estimation
class_estimation = requests.post("https://recycling-classifier-test.herokuapp.com/api/classify_base", json={"base64": img_str}, headers=headers).json()

# output estimation
print("The class of this image is estimated to be " + class_estimation['class'] + ".")