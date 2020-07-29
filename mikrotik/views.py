from django.shortcuts import render
import routeros_api
from routeros import login
# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from django.forms.utils import ErrorList
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .models import *
from .forms import *
from sklearn.metrics import mean_squared_error, mean_absolute_error
import logging, io, csv, math
import numpy as np
import pandas as pd
import time, json
import paramiko
import routeros_api
import time
from getpass import getpass


def set_config(request):
    profile_result=profile.objects.all()
    queue_result=child.objects.all()
    if request.method == 'POST':
        conform = ConfigForm(request.POST)
        print(request.POST)
        if conform.is_valid(): 
            conform.save()
            #print(request.POST)
            msg     = "Value saved."
            success = True
            context = {
                'msg': msg,
                'success': success,
                'conform': conform
            }   
            return render(request, "value.html", context)
        else:
            msg = 'Form is not valid'
            print(msg)    
    else:
        print("haha")
        conform = ConfigForm() 

    return render(request, "value.html", {"conform": conform, 'profile_result': profile_result,'queue_result': queue_result})

def mean_absolute_percentage_error(y_true, y_pred): 
  y_true, y_pred = np.array(y_true), np.array(y_pred)
  return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

def set_forecast(request):
    data = dataset.objects.all()
    prompt = {
        'setdata': 'Dataset of the CSV should be ddate, dopen, dhigh, dlow, dclose, dvplume, dopenint',
        'setdatas': data
    }
    if "GET" == request.method:
        return render(request, "forecasting.html", prompt)
       # if not GET, then proceed
    csv_file = request.FILES["csvfile"]
    if not csv_file.name.endswith('.csv'):
        messages.error(request,'File is not CSV type')
        return HttpResponseRedirect(reverse('set_forecast'))
    if csv_file.multiple_chunks():
        messages.error(request,"Uploaded file is too big (%.2f MB)." % (csv_file.size/(1000*1000),))
        return HttpResponseRedirect(reverse('set_forecast'))
    foreform = ForecastForm(request.POST, request.FILES)
    file_data = pd.read_csv(csv_file, sep=',', header=0).fillna(0)
    train_data, test_data = file_data[0:int(len(file_data)*0.9)], file_data[int(len(file_data)*0.9):]
    #print(test_data['Open'])
    
    start = time.time()
    test_dataa=test_data['Open'].values
    A=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
    const=0
    P_init=[[10**-7,0,0,0],[0,10**-7,0,0],[0,0,10**-7,0],[0,0,0,10**-7]]
    R=[[10**-7,0,0,0],[0,10**-7,0,0],[0,0,10**-7,0],[0,0,0,10**-7]]
    Q=[[10**-7,0,0,0],[0,10**-7,0,0],[0,0,10**-7,0],[0,0,0,10**-7]]
    KF=[]
    update=[]
    KF.append(test_dataa[0])
    KF.append(test_dataa[1])
    KF.append(test_dataa[2])
    KF.append(test_dataa[4])
    for i in range(4,len(test_dataa)-4):
        x_init=[[test_dataa[i-4]],[test_dataa[i-3]],[test_dataa[i-2]],[test_dataa[i-1]]]
        #prediction
        #print(i)
        prediction=np.dot(A,x_init)+const
        #print(x_min[1])
        P_min=np.dot(np.dot(A,P_init),A)+Q
        KF.append(prediction[3].tolist()[0])
        #measurement update
        y_min=prediction[3]
        #print(y_min)
        P_y_min=P_min+R
        K_gain=np.dot(P_min,np.linalg.inv(P_y_min))[3][3]
        #print(K_gain)
        x_init=prediction-K_gain*(y_min-test_dataa[i])
        update.append(x_init)
        #x_init=np.array([])
        #print(x_init)
        P_init=P_min-K_gain*P_min

    # mse = mean_squared_error(KF, test_dataa[0:len(test_dataa)-4])
    # print('MSE: '+str(mse))
    # mae = mean_absolute_error(KF, test_dataa[0:len(test_dataa)-4])
    # print('MAE: '+str(mae))
    # rmse = math.sqrt(mean_squared_error(KF, test_dataa[0:len(test_dataa)-4]))
    # print('RMSE: '+str(rmse))
    mape = mean_absolute_percentage_error(KF, test_dataa[0:len(test_dataa)-4])
    print('MAPE: '+str(mape))

    end = time.time()
    elapsed = end - start
    print("Time elapsed:" +str(elapsed)+" s")

    threshold = sum(KF)/len(KF)
    print(threshold)

    Forecast = forecast.objects.create(
        fmape="{:.2f}".format(mape),
        fthreshold="{:.2f}".format(threshold),
        felapsed="{:.3f}".format(elapsed)
    )
    forecasted = forecast.objects.last()

    context={
        'forecasted':forecasted,
        'foreform':ForecastForm()
    }
    return render(request, "forecasting.html", context)
    

def set_control(request):
    tog, created = toogle.objects.get_or_create(id=1)
    if "GET" == request.method:
        return render(request, "control.html", {'tog': tog})
    elif "POST" == request.method:
        tog = toogle.objects.get(id=request.POST['id'])
        tog.is_working = request.POST['isworking'] == 'true'
        tog.save()

        # taking configuration value
        con = configuration.objects.last()
        ipaddr = con.orouter.ipadd
        ports = con.orouter.portapi
        user = con.orouter.username
        passw = con.orouter.password
        parent = con.oqueue.dedicated
        id_queue = con.oqueue.id
        thres = con.othreshold
        maxup = con.omaxlimitup
        maxdown = con.omaxlimitdown
        minup = con.ominlimitup
        mindown = con.ominlimitdown
        medup = con.omedlimitup
        meddown = con.omedlimitdown

        # connecting to router 
        connection = routeros_api.RouterOsApiPool(ipaddr, username=user, password=passw, port=ports, plaintext_login=True)
        api = connection.get_api()
        # multithreading 
        while tog.is_working == True:
            tog = toogle.objects.get(id=1)
            get_throughput(api,thres,id_queue,maxup,maxdown,minup,mindown,medup, meddown)
        connection.disconnect()
    return HttpResponse('success')

def get_throughput(hulk, limit, ids, upmax, downmax, upmin, downmin, upmed, downmed):
    #getting throughput value
    test = hulk.get_binary_resource('/').call('interface/monitor-traffic', {'interface': b'ether2','once':b'true'})
    getrx = test[0]['rx-bits-per-second']
    gettx = test[0]['tx-bits-per-second']
    convrx = float(getrx.decode("utf-8"))/1000
    convtx = float(gettx.decode("utf-8"))/1000    
    print("Tx = ",convtx," kb")
    print("Rx = ",convrx," kb")
    
    #comparing value
    simple = hulk.get_resource("/queue/simple")
    if convrx <= (0.5*limit):
        time.sleep(2)   # giving spare time to make sure
        if convrx <= (0.5*limit):
            simple.set(id=str(ids), max_limit="{}/{}".format(upmax,downmax))
            print("Max limit become "+downmax)
        else :
            return convrx
    elif convrx <= limit:
        time.sleep(2)
        if convrx <= limit:
            simple.set(id=str(ids), max_limit="{}/{}".format(upmed,downmed))
            print("Max limit become "+downmed)
        else :
            return convrx
    else :
        time.sleep(2)
        if convrx > limit:
            simple.set(id=str(ids), max_limit="{}/{}".format(upmin,downmin))
            print("Max limit become "+downmin)
        else :
            return convrx
    time.sleep(5)
# def set_value(request):
#     if request.method == 'POST':
#         form = SetValue(request.POST)
#         if form.is_valid():
#             forms = request.POST
#             print(request.POST)
#             disprof = forms['showprofile']
#             disqueue = forms['showqueue']
#             uploads = forms['upload']
#             downloads = forms['download']
#             try:
#                 if disprof == profile.objects.get(id=1).name:
#                     n = 1
#                     m = 1
#                     if disqueue == child.objects.get(id=1).cname:
#                         o = 1
#                     else :
#                         o = 2
#                 else :
#                     n = 2
#                     m = 2
#                     o = 2
#                 profres = profile.objects.get(id=n)
#                 parres = parent.objects.get(id=m)
#                 chires = child.objects.get(id=o)
#                 connection = routeros_api.RouterOsApiPool(profres.ipadd, username=profres.username, password=profres.password, port=profres.portapi, plaintext_login=True)
#                 api = connection.get_api()
#                 simple = api.get_resource("/queue/simple") 
#                 simple.set(id=str(chires.id), max_limit="{}/{}".format(uploads,downloads))
#                 connection.disconnect()
#             except Exception as e:
#                 print("Failed to set "+ e)

#             msg     = "Value edited."
#             success = True
#             context = {
#                 'form': form,
#                 'msg': msg,
#                 'success': success
#             }
            
#             return render(request, "value.html", context)
#         #else:
#         #    msg = 'Form is not valid'    
#     else:
#         form = SetValue()
#         conform = ConfigForm()
#         profile_result=profile.objects.all()
#         queue_result=child.objects.all() 
#         #print("gagal")

#     return render(request, "value.html", {"form": form,'profile_result': profile_result,'queue_result': queue_result, "conform": conform})
# def backup(request):
#     if request.method == 'POST':
#             backups = 
