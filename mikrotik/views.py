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
from activity_log.models import *
from .models import *
from .forms import *
from influxdb import InfluxDBClient
import logging, io, csv, math
import numpy as np
import pandas as pd
import time, json
import paramiko
import time, statistics
from getpass import getpass


def set_config(request):
    profile_result=profile.objects.all()
    queue_result=parent.objects.all()
    data_result = influx.objects.all()
    config_result = configuration.objects.all()
    if request.method == 'POST':
        conform = ConfigForm(request.POST)
        print(request.POST)
        if conform.is_valid(): 
            conform.save()
            #print(request.POST)
            success = True
            context = {
                'success': success,
                'profile_result': profile_result,
                'queue_result': queue_result,
                'config_result': config_result,
                'data_result': data_result,
                'conform': conform
            }   
            return render(request, "value.html", context)
        else:
            msg = 'Form is not valid'
            print(msg)
            context = {
                'msg': msg,
                'profile_result': profile_result,
                'queue_result': queue_result,
                'data_result': data_result,
                'config_result': config_result,
                'conform': conform
            }
            return render(request, "value.html", context)    
    else:
        #print("haha")
        conform = ConfigForm() 

    return render(request, "value.html", {"conform": conform, 'profile_result': profile_result,'queue_result': queue_result, 'config_result': config_result, 'data_result': data_result})


def get_log_activity(request):
    activity = ActivityLog.objects.all().order_by('-datetime')[:30]
    if "GET" == request.method:
        return render(request, "activitylog.html", {"activity": activity})
    context={
        'activity': activity
    }
    return render(request, "activitylog.html", context)
    

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
        inf_ip = con.oinflux.host
        inf_port = con.oinflux.ports
        inf_database = con.oinflux.database
        sh = con.oshared.id
        sh_id = str(int(sh)-1)
        sh_up = con.oshared.pmaxlimitup
        sh_down = con.oshared.pmaxlimitdown
        ded_down = con.odedicated.pmaxlimitdown

        # influx db
        client = InfluxDBClient(host='localhost',port=8086,database='telegraf')
        
        # mikrotik
        connection = routeros_api.RouterOsApiPool('10.33.109.121', username='farez', password='q1w2e3r4t5', port=8738, plaintext_login=True)
        api = connection.get_api()
        simple = api.get_resource('/queue/simple')
        
        # multithreading 
        while tog.is_working == True:
            tog = toogle.objects.get(id=1)
            if tog.is_working == True:
                que_mean = "SELECT derivative(mean(Download),1s) AS Download FROM \"Queue Dedicated\" where time>= now()- 10s group by time(1s) fill(null) tz('Asia/Jakarta')"
                query = "SELECT derivative(mean(Download),1s) AS Download FROM \"Queue Dedicated\" where time>= now()- 24h group by time(1s) fill(null) tz('Asia/Jakarta')"
                result = client.query(query)
                res_mean = client.query(que_mean)
                point = list(result.get_points())
                po_mean = list(res_mean.get_points())
                set_autocontrol(simple,point,po_mean,sh_up,sh_down,client,sh_id)
                time.sleep(10)
            else :
                set_falsecontrol(simple,sh_up,sh_down,sh_id)
    return HttpResponse('success')

def set_falsecontrol(simple,sh_up,sh_down,sh_id):
    newUp,newDown = sh_up,sh_down
    simple.set(id=sh_id,max_limit='{}/{}'.format(newUp,newDown))

def set_autocontrol(spl,data,da_mean,maxUp,maxDown,dbinflux,sh_id):
    down = []
    arr_mean = []
    for datas in data:
        down.append(datas['Download'])
    for arrs in da_mean:
        arr_mean.append(arrs['Download'])
    maxlimit = 100/8
    thrDown = (down[len(down)-1])/1000000
    stadev = (statistics.pstdev(arr_mean))/1000000
    avg = (statistics.mean(arr_mean))/1000000
    print("==========================")
    print("Download :" + "%.1f" %(thrDown)+ "M")	
    print("Standar Deviasi :" + "%.1f" %(stadev)+ "M")
    print("Average :" + "%.1f" %(avg) + "M")
    
    if avg >= 0.67*maxlimit:
        space = thrDown + (0.34*stadev)
        set_allocation(spl,space,maxlimit,sh_id)  
    elif avg >= 0.34*maxlimit:
        space = thrDown + (0.67*stadev)
        set_allocation(spl,space,maxlimit,sh_id)
    elif avg < 0.34*maxlimit:
        space = thrDown + stadev
        set_allocation(spl,space,maxlimit,sh_id)


def set_allocation(spl,space,maxlimit,sh_id):
    if space > maxlimit:
        allocDown,allocUp = 0.0,0.0
        newDown = str((maxlimit*8)+allocDown) + "M"
        newUp = str(((0.5*maxlimit)*8)+allocUp) + "M"
        spl.set(id=sh_id,max_limit='{}/{}'.format(newUp,newDown))
        save_influx(space,allocDown)
        print("Spacing "+ "%.1f" %(space)+"M")
        print("Allocating "+ "%.1f" %(allocDown)+"M")
    elif space < maxlimit:
        allocDown = (maxlimit - space)
        allocUp = (0.5 * allocDown)
        newDown = str((maxlimit*8)+(allocDown)*8) + "M"
        newUp = str(((0.5*maxlimit)*8)+(allocUp)*8) + "M"
        spl.set(id=sh_id,max_limit='{}/{}'.format(newUp,newDown))
        save_influx(space,allocDown)
        print("Spacing "+ "%.1f" %(space)+"M")
        print("Allocating "+ "%.1f" %(allocDown)+"M")

    # if stadev < (down[len(down)-1]):                                                            # if standard deviasi lessthan last throughput
    #     if stadev > 0.5*(down[len(down)-1]):                                                    # if standard deviasi more than 0,5*last throughput
    #         if ((((down[len(down)-1])+(0.5*stadev))/1000000)) < maxlimit:                        # if allocated less than maxlimit
    #             space = ((((down[len(down)-1])+(0.5*stadev))/1000000))                        #last throughput + 0,5 * standar deviasi
    #             allocDown = int(round(((maxlimit-space)),0))
    #             allocUp = 0.5 * allocDown
    #             newDown = str(allocDown*8) + "M"
    #             newUp = str(allocUp*8) + "M"
    #             spl.set(id='1',max_limit='{}/{}'.format(newUp,newDown))
    #             print("Allocating "+ "%.1f" %(allocDown))
    #             print("Spacing "+ "%.1f" %(space)+"M")
    #             spc = round(space*1000000,0)
    #             allUp = allocUp * 1000000
    #             allDown = int((maxlimit-space)*1000000)
    #             save_influx(spc,allDown)
    #         elif ((((down[len(down)-1])+(0.5*stadev))/1000000)) >= maxlimit:                     #if allocated more than or equal with maxlimit
    #             space = (((down[len(down)-1])+(0.5*stadev))/1000000)
    #             newUp,newDown = maxUp,maxDown
    #             spl.set(id='1',max_limit='{}/{}'.format(newUp,newDown))
    #             print("Allocating :" + str(newDown))                                  # allocated 0
    #             print("Spacing "+ "%.1f" %(space)+"M")
    #             spc = round(space*1000000,0)
    #             allUp,allDown = 0,0
    #             save_influx(spc,allDown)
    #     elif stadev <= 0.5*(down[len(down)-1]):
    #         if ((((down[len(down)-1])+stadev)/1000000)) < maxlimit:
    #             space = (((down[len(down)-1])+stadev)/1000000)
    #             allocDown = int(round(((maxlimit-space)),0))
    #             allocUp = 0.5 * allocDown
    #             newDown = str(allocDown*8) + "M"
    #             newUp = str(allocUp*8) + "M"
    #             spl.set(id='1',max_limit='{}/{}'.format(newUp,newDown)) 
    #             print("Allocating "+ "%.1f" %(allocDown))
    #             print("Spacing "+ "%.1f" %(space)+"M")
    #             spc = round(space*1000000,0)
    #             allUp = allocUp * 1000000
    #             allDown = int((maxlimit-space)*1000000)
    #             save_influx(spc,allDown)
    #         elif ((((down[len(down)-1])+stadev)/1000000)) >= maxlimit:
    #             space = ((((down[len(down)-1])+stadev)/1000000))
    #             newUp,newDown = maxUp,maxDown
    #             spl.set(id='1',max_limit='{}/{}'.format(newUp,newDown))
    #             print("Allocating :" + str(newDown))
    #             print("Spacing "+ "%.1f" %(space)+"M")
    #             spc = round(space*1000000,0)
    #             allUp,allDown = 0,0
    #             save_influx(spc,allDown)
    # elif stadev >= (down[len(down)-1]):
    #     if stadev > 1.5*(down[len(down)-1]):
    #         if (((stadev)/1000000)) < maxlimit:
    #             space = ((stadev/1000000))
    #             allocDown = int(round(((maxlimit-space)),0))
    #             allocUp = 0.5 * allocDown
    #             newDown = str(allocDown*8) + "M"
    #             newUp = str(allocUp*8) + "M"
    #             spl.set(id='1',max_limit='{}/{}'.format(newUp,newDown))
    #             print("Allocating "+ "%.1f" %(allocDown))
    #             print("Spacing "+ "%.1f" %(space)+"M")
    #             spc = round(space*1000000,0)
    #             allUp = allocUp * 1000000
    #             allDown = int((maxlimit-space)*1000000)
    #             save_influx(spc,allDown)
    #         elif (((stadev)/1000000)) >= maxlimit:
    #             space = ((stadev)/1000000)
    #             newUp,newDown = maxUp,maxDown
    #             spl.set(id='1',max_limit='{}/{}'.format(newUp,newDown))
    #             print("Allocating :" + "%.1f" %(allocDown))
    #             print("Spacing "+ "%.1f" %(space)+"M")
    #             spc = round(space*1000000,0)
    #             allUp,allDown = 0,0
    #             save_influx(spc,allDown)
    #     elif stadev <= 1.5*(down[len(down)-1]):
    #         if (((stadev+(0.5*(down[len(down)-1])))/1000000)) < maxlimit:
    #             space = (((stadev+(0.5*(down[len(down)-1])))/1000000))
    #             allocDown = int(round(((maxlimit-space)),0))
    #             allocUp = 0.5 * allocDown
    #             newDown = str(allocDown*8) + "M"
    #             newUp = str(allocUp*8) + "M"
    #             spl.set(id='1',max_limit='{}/{}'.format(newUp,newDown))
    #             print("Allocating "+ "%.1f" %(allocDown))
    #             print("Spacing "+ "%.1f" %(space)+"M")
    #             spc = round(space*1000000,0)
    #             allUp = allocUp * 1000000
    #             allDown = int((maxlimit-space)*1000000)
    #             save_influx(spc,allDown)
    #         elif (((stadev+(0.5*(down[len(down)-1])))/1000000)) >= maxlimit:
    #             space = (((0.5*(down[len(down)-1]))/1000000))
    #             newUp,newDown = maxUp,maxDown
    #             spl.set(id='1',max_limit='{}/{}'.format(newUp,newDown))
    #             print("Allocating :" + "%.1f" %(allocDown))
    #             print("Spacing "+ "%.1f" %(space)+"M")
    #             spc = round(space*1000000,0)
    #             allUp = allocUp * 1000000
    #             allDown = int(round((maxlimit-space)*1000000,0))
    #             save_influx(spc,allDown)

 
def save_influx(spacing,allocateDown):
    space = spacing * 1000000
    allocate = allocateDown * 1000000
    client = InfluxDBClient(host='10.33.109.141',username='telegraf',password='telegraf',port=8086,database='telegraf')
    json_body = [
        {
            "measurement": "bandwidth",
            "tags": {
                "host": "python"
                },
            "fields": {
                "space": space,
                "allocate": allocate
            }
        }
    ]
    result = client.write_points(json_body)
    print("saving to DB")

#def get_throughput(hulk, limit, ids, upmax, downmax, upmin, downmin, upmed, downmed):
def get_throughput(hulk,ld):
    #getting throughput value
    test = hulk.get_binary_resource('/').call('interface/monitor-traffic', {'interface': b'ether2','once':b'true'})
    getrx = test[0]['rx-bits-per-second']
    gettx = test[0]['tx-bits-per-second']
    convrx = float(getrx.decode("utf-8"))/1000
    convtx = float(gettx.decode("utf-8"))/1000
    print("Tx = ",convtx," kb")
    print("Rx = ",convrx," kb")
    ld.append(convrx)

