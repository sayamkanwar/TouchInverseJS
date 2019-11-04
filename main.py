import tensorflow as tf
import json
import base64
import re
import string
import random
from io import BytesIO
from PIL import Image
from flask import Flask, request, render_template
from flask_cors import CORS, cross_origin
import operator
import os
import cv2

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/',  methods=['GET', 'POST'])
@cross_origin()
def main():
    if request.method == "POST":
        b64img=request.form['base64image']
        x_value=request.form['x_val']
        y_value=request.form['y_val']
        w_value=request.form['w_val']
        h_value=request.form['h_val']
        b64img += "=" * ((4 - len(b64img) % 4) % 4)
        starter = b64img.find(',')
        image_data = b64img[starter+1:]
        im = Image.open(BytesIO(base64.b64decode(image_data)))
        rgb_im = im.convert('RGB')
        filename = './snapshots/'+random_gen()+'.jpg'
        rgb_im.save(filename)
        img = cv2.imread(filename)
        deltax = 60
        deltay = 150
        crop_img = img[int(float(y_value))-deltay:int(float(y_value))+int(float(h_value))+deltay, int(float(x_value))-deltax:int(float(x_value))+int(float(w_value))+deltax]
        new_fname = filename+'_cropped.jpg'
        cv2.imwrite(new_fname, crop_img)
        os.remove(filename)  
        image_path = new_fname

        image_data = tf.gfile.FastGFile(image_path, 'rb').read()
        label_lines = [line.rstrip() for line in tf.gfile.GFile("./classifier_model_labels.txt")]

        with tf.gfile.FastGFile("./classifier_model.pb", 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            _ = tf.import_graph_def(graph_def, name='')

        confidence_scores={}
        os.remove(image_path)    

        with tf.Session() as sess:
            softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
            predictions = sess.run(softmax_tensor, {'DecodeJpeg/contents:0': image_data})

            top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
            for node_id in top_k:
                human_string = label_lines[node_id]
                score = predictions[0][node_id]
                confidence_scores[human_string]=score

        max_index = max(confidence_scores.iteritems(), key=operator.itemgetter(1))[0]
        print(confidence_scores)
        print(max_index)
        
        return max_index

def random_gen(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))