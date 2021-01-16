from flask import Flask



import flask
from flask import request, jsonify
from flask import Response, json, request, jsonify, Flask
import math
import random
import numpy as np
import pandas as pd
# used to grab the stock prices, with yahoo
import pandas_datareader as web
import math
from datetime import datetime
# to visualize the results
import matplotlib.pyplot as plt
import seaborn


app = Flask(__name__)

from stock_list_optimize import *







@app.route('/')
def hello_world():
    return 'Hello World!'







@app.route('/api/optimise', methods=['POST'])
def optimise():

    result = []
    try:
        print("->started server")
        # global symbols_list
        symbols_list = request.json.get('symbols_list')
        # global df_data
        
        start_date = request.json.get('start')
        end_date = request.json.get('end')
        gen = request.json.get('gen')
        iterations = request.json.get('iterations')
        p = request.json.get('p_size')
        # global start
        start = datetime(start_date[0], start_date[1], start_date[2])
        # global end
        end = datetime(end_date[0], end_date[1], end_date[2])
        # global p_size
        # p_size = p
        # global g
        # g = gen
        df_data = get_data(symbols_list,start,end)
        print("->df_data = ", df_data)
        print("->symbols_list = ", symbols_list)

        print("->starting GA")
        gp = GA(df_data,symbols_list,gen)
        gp.sort(key=lambda x: x.f, reverse=True)

        return jsonify(gp[0].w.tolist()), 200
    except Exception as e:
        return f"An Error Occured: {e}"

    return jsonify(result)




if __name__ == '__main__':
    app.run()