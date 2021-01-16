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
# Initialize Flask app


# start = datetime(2016, 9, 1)
# end = datetime(2017, 3, 7)
p_size = 10
# app = flask.Flask(__name__)
# app.config["DEBUG"] = True
# df_data = []
# symbols_list = []
# g = 30
# Create some test data for our catalog in the form of a list of dictionaries.





def get_data(symbols_list,start,end):
    print("->collecting data")
    symbols = []
    for ticker in symbols_list:
        r = web.DataReader(ticker, 'yahoo', start, end)
        # add a symbol column
        r['Symbol'] = ticker
        symbols.append(r)
    df = pd.concat(symbols)
    df = df.reset_index()
    # print(df)
    df = df[['Date', 'Close', 'Symbol']]
    df_data = df.pivot('Date', 'Symbol', 'Close').reset_index()
    # print("->got symbols data")
    return df_data


def get_std(df_data,symbols_list):
    # print("inside std")
    sd = []
    # print(symbols_list)
    for ticker in symbols_list:

        sd.append(df_data[ticker].pct_change().std())
        # print(ticker, " = ", df_data[ticker].pct_change().std())
    return sd


def get_X(df_data,symbols_list):
    stack_x = []
    stack_ret = []
    mean = []
    for ticker in symbols_list:
        t_data = df_data[ticker].pct_change()
        stack_ret.append(t_data)
        t_data_mean = t_data.sum()/len(t_data)
        mean.append(t_data_mean)
        t_data = t_data - t_data_mean
        stack_x.append(t_data)
    R = pd.DataFrame(np.column_stack(stack_ret), columns=symbols_list)
    X = pd.DataFrame(np.column_stack(stack_x), columns=symbols_list)
    X = X.iloc[1:]
    return X


def get_covariance_mat(X):
    l = len(X)
    x = np.array(X)
    x_t = x.transpose()
    return np.dot(x_t, x)/l


def get_correlation_mat(df_data,symbols_list,X):
    std = get_std(df_data,symbols_list)
    std_m = []
    for i in range(len(std)):
        temp = []
        for j in range(len(std)):
            temp.append(std[i]*std[j])
        std_m.append(temp)

    x = np.array(X)
    corr_mat = x
    for i in range(len(std)):
        for j in range(len(std)):
            corr_mat[i][j] = X[i][j]/std_m[i][j]
            if i == j:
                corr_mat[i][j] = 1
    return corr_mat


def get_weighted_std(df_data,symbols_list,W):
    std = get_std(df_data,symbols_list)
    std_w = std
    for i in range(len(W)):
        std_w[i] = W[i]*std[i]
    return std_w


def portfolio_var(df_data,symbols_list,W):
    # print("inside port-var")
    std = get_std(df_data,symbols_list)
    # print("std = ", std)
    covariance_mat = get_covariance_mat(get_X(df_data,symbols_list))
    # print("covar = ", covariance_mat)
    corr_df = np.array(get_correlation_mat(df_data,symbols_list,covariance_mat))
    # print("corr = ", corr_df)
    std_w = np.array(get_weighted_std(df_data,symbols_list,W))
    std_w_t = std_w.transpose()
    port_var = np.dot(np.dot(std_w_t, corr_df), std_w)
    # print("port_var = ", port_var)
    return port_var


def get_weighted_ret(df_data,symbols_list,W):
    ret = []
    ret_w = []
    for ticker in symbols_list:
        r = df_data[ticker].pct_change().mean()
        ret.append(r)
    for i in range(len(ret)):
        ret_w.append(ret[i]*W[i])
    return ret_w


class Chromosome:
    def normalise_weights(self):
        # print("normalizing....")
        n_W = np.asarray(self.w, dtype=np.float64, order='C')
        s = n_W.sum()
        for i in range(len(self.w)):
            n_W[i] = n_W[i]/s
        self.w = n_W

    def mutate_self(self,df_data,symbols_list):
        w = self.w
        a = 0
        b = 0
        print("-->before mutation",self.w," and old f = ",self.f)
        while(a == b):
            a = random.randint(0, len(w)-1)
            b = random.randint(0, len(w)-1)
            dna = w[a]
            w[a] = w[b]
            w[b] = dna
        self.w = w
        self.fitness_for_max_ret(df_data,symbols_list)
        self.var(df_data,symbols_list)
        print("-->after mutation",self.w," and new f = ",self.f)

    def fitness_for_max_ret(self,df_data,symbols_list):
        # print("fitting.....")
        self.f = np.array(get_weighted_ret(df_data,symbols_list,self.w)).sum()*252

#     def firness_for_min_var(self):
#         self.f = math.sqrt(portfolio_var(corr,std,self.w)*252)

#     def ret(self):
#         self.f = np.array(get_weighted_ret(df_data,self.w,symbols_list)).sum()*252

    def var(self,df_data,symbols_list):
        # print("var-ing.....")
        self.v = math.sqrt(portfolio_var(df_data,symbols_list,self.w)*252)

    def __init__(self,df_data,symbols_list):
        self.w = random.sample(range(5, 100), len(symbols_list))
        self.normalise_weights()
        self.f = 0
        self.fitness_for_max_ret(df_data,symbols_list)
        self.v = 0
        self.var(df_data,symbols_list)


def init_population(df_data,symbols_list):
    print("->initializing population")
    population = []
    for i in range(p_size):

        p = Chromosome(df_data,symbols_list)
        p.normalise_weights()
        p.fitness_for_max_ret(df_data,symbols_list)
        p.var(df_data,symbols_list)
        print(i, "th child = ", p.w, "fitness = ", p.f)
        population.append(p)
    return population


def mutate(population,df_data,symbols_list):
    print("\nMutating......")
    for i in range(len(population)):
        population[i].mutate_self(df_data,symbols_list)

    return population


def mating(population,df_data,symbols_list):
    print("\nMatting.......")
    n_population = population
    l = len(population)
    if(l % 2 == 1):
        l = l-1
    for i in range(l):
        child = []
        if(i % 2 == 0):
            for j in range(len(symbols_list)):
                if(j % 2 == 0):
                    child.append(population[i].w[j])
                else:
                    child.append(population[i+1].w[j])

            c = Chromosome(df_data,symbols_list)
            c.w = child
            c.normalise_weights()
            print("child of ",i,"->",population[i].w,"and",i+1,"->",population[i+1].w," = ",c.w)
            c.mutate_self(df_data,symbols_list)
            c.fitness_for_max_ret(df_data,symbols_list)
            c.var(df_data,symbols_list)
            n_population.append(c)
    return n_population


def tournament_selection(population):
    print("\nSelection........")
    n_population = []
    for i in range(5):
        participants = random.sample(population, 5)
        print(">>>>>>>>-----participants are....")
        for p in participants:
            print("f = ", p.f, " and w = ", p.w)

        participants.sort(key=lambda x: x.f, reverse=True)
        print("--> winner no.", i, " = ",
              participants[0].w, " f =", participants[0].f)
        print(">>>>>>>>-----Remaining populations are....")
        for p in population:
            print("f = ", p.f, " and w = ", p.w)

        n_population.append(participants[0])
        population.remove(participants[0])

    population.sort(key=lambda x: x.f, reverse=True)

    for i in range(p_size-5):
        n_population.append(population[i])

    return n_population


def GA(df_data,symbols_list,g):
    gp = []
    print("starting GA>>>>>>")
    population = init_population(df_data,symbols_list)
    for i in range(g):

        print("generation = ", i)

        population = mating(population,df_data,symbols_list)
        print("Population after mating and mutation is......")
        population.sort(key=lambda x: x.f, reverse=True)
        for p in population:
            print("f = ", p.f, " and w = ", p.w)
        random.shuffle(population)
        population = tournament_selection(population)
        population.sort(key=lambda x: x.f, reverse=True)
        print("Population after selection is......")
        for p in population:
            print("f = ", p.f, " and w = ", p.w)
        print("best = ", population[0].f, " risk = ", population[0].v)
        population[0].var(df_data,symbols_list)
        gp.append(population[0])
        random.shuffle(population)

    return gp


# @app.route('/api/optimise', methods=['POST'])
# def optimise():

#     result = []
#     try:
#         print("->started server")
#         # global symbols_list
#         symbols_list = request.json.get('symbols_list')
#         # global df_data
        
#         start_date = request.json.get('start')
#         end_date = request.json.get('end')
#         gen = request.json.get('gen')
#         iterations = request.json.get('iterations')
#         p = request.json.get('p_size')
#         # global start
#         start = datetime(start_date[0], start_date[1], start_date[2])
#         # global end
#         end = datetime(end_date[0], end_date[1], end_date[2])
#         # global p_size
#         # p_size = p
#         # global g
#         # g = gen
#         df_data = get_data(symbols_list,start,end)
#         print("->df_data = ", df_data)
#         print("->symbols_list = ", symbols_list)

#         print("->starting GA")
#         gp = GA(df_data,symbols_list,gen)
#         gp.sort(key=lambda x: x.f, reverse=True)

#         return jsonify(gp[0].w.tolist()), 200
#     except Exception as e:
#         return f"An Error Occured: {e}"

#     return jsonify(result)


# app.run()

# request body format
# {
#   "symbols_list":["ALKEM.NS","CIPLA.NS","IDEA.NS","PVR.NS","WONDERLA.NS"],
#   "gen":50,
#   "iterations":5,
#   "start":[2016,9,1],
#   "end":[2017,3,7],
#   "p_size":10
# }
