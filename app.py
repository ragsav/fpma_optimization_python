from flask import Flask

import atexit

# v2.x version - see https://stackoverflow.com/a/38501429/135978
# for the 3.x version
from firebase_admin import credentials, firestore, initialize_app
from apscheduler.scheduler import Scheduler

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

from stock_list_optimize import *
from flask_cors import CORS, cross_origin

app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


request_queue=[]


cred = credentials.Certificate('fcma_key.json')
default_app = initialize_app(cred)
db = firestore.client()
# todo_ref = db.collection('todos')


cron = Scheduler(daemon=True)
cron.start()


def optimize_queue(request_queue):

	try:

		request = request_queue.pop(0)
		print(request)
		uid = request['uid']
		symbols_list = request['symbols_list']
		start_date = request['start']
		end_date = request['end']
		gen = request['gen']
		iterations = request['iterations']
		p = request['p_size']
		start = datetime(start_date[0], start_date[1], start_date[2])
		end = datetime(end_date[0], end_date[1], end_date[2])

		print(end)
		df_data = get_data(symbols_list,start,end)
		print("->starting GA for user {}".format(uid))
		gp = GA(df_data,symbols_list,gen)
		gp.sort(key=lambda x: x.f, reverse=True)

		ret_raw = get_ret(df_data,symbols_list)
		std_raw = get_std(df_data,symbols_list)
		recommendation_list = gp[0].w.tolist()

		# print(ret_raw,std_raw,recommendation_list,symbols_list)
		for i in range(len(recommendation_list)):
			recommendation_list[i] = "{},{},{},{}".format(symbols_list[i],recommendation_list[i],ret_raw[i],std_raw[i])
		# print(ret_raw,std_raw,recommendation_list,symbols_list)

		db.collection('users').document(uid).update({'recommendation_list': recommendation_list})

	except Exception as e:
		print(e)

    



@cron.interval_schedule(seconds=10)
def job_function():
    optimize_queue(request_queue)



@app.route('/')
def hello_world():
    return 'Hello World!'

@cross_origin()
@app.route('/api/optimise', methods=['POST'])
def optimise():

    request2 = {}
    try:

    	print(request.json)


    	request2['uid'] = request.json.get('uid')
    	request2['symbols_list'] = request.json.get('symbols_list')
    	request2['start'] = request.json.get('start')
    	request2['end'] = request.json.get('end')
    	request2['gen'] = request.json.get('gen')
    	request2['iterations'] = request.json.get('iterations')
    	request2['p_size'] = request.json.get('p_size')
    	global request_queue
    	request_queue.append(request2)
    	print("--> request queued")
    	return jsonify("success"), 200

    except Exception as e:
        return f"An Error Occured: {e}"

    return jsonify(result)




if __name__ == '__main__':
    app.run()