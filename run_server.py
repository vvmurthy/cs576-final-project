from flask import Flask, redirect, url_for, request
app = Flask(__name__)
from analyze_scenes import make_data_file

"""
@app.route('/setup',methods = ['POST'])
def post_call():
    if request.method == 'POST':
        base = request.form['base']
        num = request.form['num']
        make_data_file(base, num)
    return "Success"
"""
for num in ["1", "2", "3"]:
    base = "dataset-00" + num + "-00" + num + "/dataset"
    if num != "1":
        base = "dataset-00" + num + "-00" + num + "/dataset" + num 
    make_data_file(base, num)
