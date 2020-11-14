from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from django.forms.utils import ErrorList
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from requests.exceptions import ConnectionError
from django.views.generic import View
from rest_framework.views import APIView
from rest_framework.response import Response
from pysnmp.hlapi import SnmpEngine,CommunityData,UdpTransportTarget,ContextData,ObjectType,getCmd,ObjectIdentity
from influxdb import InfluxDBClient
from monitoring.forms import AuthForm, PrintForm
import datetime
import paramiko
import re
import pymysql
import sys
import json
import os, socket, time
import requests
# Create your views here.
class HomeView(View):
    def get(self, request, *args, **kwargs):
        return render(request,'tes.html')

class LoginView(View):
    def get(self,request):
        sekarang = datetime.date.today()
        form = AuthForm()
        db = pymysql.connect("localhost","root","","monitoring")
        cursor = db.cursor()
        cursor.execute('SELECT name FROM user_oid where tanggal=\"'+str(sekarang)+'\"')
        result = cursor.fetchall()
        newuser = []
        for x in result:
            newuser.append(x[0]) 
        return render(request,'tambah.html', {'form' : form,'baru' : newuser})
    def post(self,request):    
        form = AuthForm(request.POST)
        if form.is_valid():
            try:
                address = form.cleaned_data['address']
                port = form.cleaned_data['port']
                router = form.cleaned_data['router']
                sandi = form.cleaned_data['sandi']
                community = form.cleaned_data['community']
                sekarang = datetime.date.today()
                form = AuthForm()
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(address,port=int(port),username=router,password=sandi)
                print('Berhasil')
                stdin, stdout, stderr = ssh_client.exec_command('queue simple print oid')
                with open("ghanny.txt", 'a') as f:
                        f.writelines(stdout.read().decode('ascii').strip("\n"))
                f = open("ghanny.txt")
                lines = f.readlines()
                f.close()
                f = open("ghanny.txt", 'w')
                f.writelines(lines[1:])
                f.close()
                f = open("ghanny.txt")
                lines = f.readlines()
                f.close()
                f = open("ghanny.txt", 'w')
                for line in lines:
                    f.write(line[6:].replace(" ",""))
                f.close()
                hilang = [';;;','queues','packets']
                with open('ghanny.txt') as old, open('hasil.txt', 'w') as new:
                    for line in old:
                        if not any(a in line for a in hilang):
                            new.write(line)
                def get(host,oid,community):
                    errorIndication, errorStatus, errorIndex, varBinds = next(
                        getCmd(SnmpEngine(),
                            CommunityData(community, mpModel=0),
                            UdpTransportTarget((host, 161)),
                            ContextData(),
                            ObjectType(ObjectIdentity(oid)))
                    )
                    if errorIndication:
                        print(errorIndication)
                    elif errorStatus:
                        print('%s at %s' % (errorStatus.prettyPrint(),
                                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                    else:
                        for varBind in varBinds:
                            print(varBind[1])
                    return varBind[1]
                db = pymysql.connect("localhost","root","","monitoring")
                cursor = db.cursor()
                count = 1
                try:
                    with open("hasil.txt", 'r') as f:
                        kamu = []
                        for line in f.readlines():
                            if((count%3) != 0 or count == 0):    
                                count += 1
                                d = line.strip().split("=")
                                kamu.append(d[1])
                            elif (count == 3):
                                d = line.strip().split("=")
                                kamu.append(d[1])
                                name = get(address, kamu[0],community)
                                cursor.execute('insert into user_oid (name,upload,download,tanggal) select * from (select "%s" as name,"%s" as upload,"%s" as download,"%s" as tanggal) as tmp where not exists (select name from user_oid where name = "%s") limit 1' % (name,kamu[2],kamu[1],sekarang,name))
                                db.commit()
                                print("Data Berhasil Masuk!")
                                kamu = []
                                count = 1                   
                            else:
                                db.rollback()
                                print("Data Gagal Masuk!")
                except Exception as e:
                    ssh_client.close()
                    os.system("rm ghanny.txt")
                    os.system("rm hasil.txt")
                    form = AuthForm()
                    msg = "SNMP Request Time Out! Cek kembali Community yang digunakan!"
                    args = {'form' : form, 'text' : msg}
                    return render(request,"tambah.html", args)     
                cursor.execute("SELECT name,upload,download FROM user_oid")
                result = cursor.fetchall()
                for x in result:
                    with open(x[0]+".conf","a") as f:
                        f.writelines("[[inputs.snmp]]\n")
                        f.writelines("agents = [\""+address+":161\"]\n")
                        f.writelines("version = 1\n")
                        f.writelines("community = \""+community+"\"\n")
                        f.writelines("name = \""+x[0]+"\"\n\n")
                        f.writelines("[[inputs.snmp.field]]\n")
                        f.writelines("name = \"Upload\"\n")
                        f.writelines("oid = \""+x[1]+"\"\n")
                        f.writelines("[[inputs.snmp.field]]\n")
                        f.writelines("name = \"Download\"\n")
                        f.writelines("oid = \""+x[2]+"\"\n\n")
                cursor.execute('SELECT name FROM user_oid where tanggal=\"'+str(sekarang)+'\"')
                result = cursor.fetchall()
                newuser = []
                for x in result:
                    newuser.append(x[0]) 
                os.system("cp *.conf /etc/telegraf/telegraf.d/")
                os.system("rm *.conf")
                os.system("service telegraf stop")
                os.system("service telegraf start")
                os.system("rm ghanny.txt")
                os.system("rm hasil.txt")              
                db.close
                if(len(newuser)==0):
                    msg = "Tidak Ada Pelanggan Baru."
                else:
                    msg = "Pelanggan Baru Berhasil Ditambahkan!"
                status = True
                args = {'form' : form, 'text' : msg, 'baru' : newuser, 'status' : status}
            except paramiko.AuthenticationException:
                os.system("rm ghanny.txt")
                os.system("rm hasil.txt")
                msg = "Login gagal, tolong masukkan user dan password yang benar!"
                form = AuthForm()
                args = {'form' : form, 'text' : msg}
                return render(request,"tambah.html", args)
            except paramiko.SSHException as sshException:
                os.system("rm ghanny.txt")
                os.system("rm hasil.txt")
                msg = "SSH tidak menanggapi, error : %s" % sshException
                form = AuthForm()
                args = {'form' : form, 'text' : msg}
                return render(request,"tambah.html", args)
            except socket.timeout as e:
                os.system("rm ghanny.txt")
                os.system("rm hasil.txt")
                msg = "Connection Timed Out"
                form = AuthForm()
                args = {'form' : form, 'text' : msg}
                return render(request,"tambah.html", args)
            except Exception as e:
                os.system("rm ghanny.txt")
                os.system("rm hasil.txt")
                ssh_client.close()
                form = AuthForm()
                msg = "Koneksi Gagal! Pastikan alamat dan port router tujuan benar!"
                args = {'form' : form, 'text' : msg}
                return render(request,"tambah.html", args) 
        return render(request,"tambah.html", args)

class CanvasView(View):
    def get(self, request, pengguna=None, id=None):
        pengguna = request.GET['pengguna']
        if (pengguna is None):
            return render(request,'list.html')
        else:
            form = PrintForm()
            pelanggan = []
            bulan = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"]
            db = pymysql.connect("localhost","root","","monitoring")
            cursor = db.cursor()
            cursor.execute("SELECT name FROM user_oid")
            result = cursor.fetchall()
            for x in result:
                pelanggan.append(x[0])
            return render(request,'chart.html', {'pengguna': pengguna, 'pelanggan' : pelanggan, 'bulan' : bulan, 'form' : form})
    # def post(self,request):    
    #     form = PrintForm(request.POST)
    #     if form.is_valid():
    #         try:
    #             nama = form.cleaned_data['nama']
    #             bulan = form.cleaned_data['bulan']
    #             upload = form.cleaned_data['upload']
    #             download = form.cleaned_data['download']
    #             langganan = form.cleaned_data['langganan']
    #             biaya = form.cleaned_data['biaya']
    #             return render(request, 'report.html', {'nama' : nama, 'bulan' : bulan, 'upload' : upload, 'download' : download, 'langganan' : langganan, 'biaya' : biaya })
    #         except Exception as e:
    #             form = PrintForm()
    #             return render(request,'chart.html', {'pengguna': pengguna, 'pelanggan' : pelanggan, 'bulan' : bulan, 'form' : form})

class ChartView(View):
    def get(self, request, pengguna=None, id=None):
        pengguna = request.GET['pengguna']
        if (pengguna is None):
            return render(request,'list.html')
        else:
            pelanggan = []
            db = pymysql.connect("localhost","root","","monitoring")
            cursor = db.cursor()
            cursor.execute("SELECT name FROM user_oid")
            result = cursor.fetchall()
            for x in result:
                pelanggan.append(x[0])
            return render(request,'canvas.html', {'pengguna': pengguna, 'pelanggan' : pelanggan})

class SpaceView(View):
    def get(self, request, pengguna=None, id=None):
        pengguna = request.GET['pengguna']
        if (pengguna is None):
            return render(request,'list.html')
        else:
            pelanggan = []
            db = pymysql.connect("localhost","root","","monitoring")
            cursor = db.cursor()
            cursor.execute("SELECT name FROM user_oid")
            result = cursor.fetchall()
            for x in result:
                pelanggan.append(x[0])
            return render(request,'spacing.html', {'pengguna': pengguna, 'pelanggan' : pelanggan})

def get_data(request, *args, **kwargs):
    client = InfluxDBClient(host='localhost',username='telegraf',password='telegraf',port=8086,database='telegraf')
    query = "SELECT derivative(mean(Upload),1s) AS Download, derivative(mean(Download),1s) AS Upload FROM \"FTTH PPPOE HUB CDT\" where time>= now()- 10h group by time(1s) fill(null) tz('Asia/Jakarta')"
    result = client.query(query)
    point = list(result.get_points())
    time = []
    upload = []
    download = []
    upload1 = []
    upload2 = []
    upload3 = []
    download1 = []
    download2 = []
    download3 = []
    for poin in point:
        if(poin['Upload']<=1250000):
            upload1.append(poin['Upload'])
        elif((1250000<poin['Upload']) and (poin['Upload']<=2500000)):
            upload2.append(poin['Upload'])
        elif(poin['Upload']>2500000):
            upload3.append(poin['Upload'])
        else:
            print("Tidak Ada Data")
        if(poin['Download']<=1250000):
            download1.append(poin['Download'])
        elif((1250000<poin['Download']) and (poin['Download']<=2500000)):
            download2.append(poin['Download'])
        elif(poin['Download']>2500000):
            download3.append(poin['Download'])
        else:
            print("Tidak Ada Data")
        time.append(poin['time'])
        upload.append(poin['Upload'])
        download.append(poin['Download'])
    influx = {
        'waktu' : time,
        'upload' : upload,
        'download' : download,
    }
    json_object = json.dumps(point)
    return render(request,'list.html', json_object)
    # return Response(json_object)
class BulanView(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request, username, bulan, format=None):
        context = {}
        context['username'] = "{}".format(username)
        context['bulan'] = "{}".format(bulan)
        print(context['bulan'])
        x = context['bulan']
        now = datetime.datetime.now()
        last = now.year - 1
        year = now.year
        last = str(last)
        year = str(year)
        if(x=="Januari"):
            awal = last+'-12-31T17:00:00Z'
            akhir = year+'-01-31T16:59:59Z'
        elif(x=="Februari"):
            if(now.year%4):
                awal = year+'-01-31T17:00:00Z'
                akhir = year+'-02-29T16:59:59Z'
            else:
                awal = year+'-01-31T17:00:00Z'
                akhir = year+'-02-28T16:59:59Z'
        elif(x=="Maret"):
            if(now.year%4):
                awal = year+'-02-29T17:00:00Z'
                akhir = year+'-03-31T16:59:59Z'
            else:
                awal = year+'-02-28T17:00:00Z'
                akhir = year+'-03-31T16:59:59Z'
        elif(x=="April"):
            awal = year+'-03-31T17:00:00Z'
            akhir = year+'-04-30T16:59:59Z'
        elif(x=="Mei"):
            awal = year+'-04-30T17:00:00Z'
            akhir = year+'-05-31T16:59:59Z'
        elif(x=="Juni"):
            awal = year+'-05-31T17:00:00Z'
            akhir = year+'-06-30T16:59:59Z'
        elif(x=="Juli"):
            awal = year+'-06-30T17:00:00Z'
            akhir = year+'-07-31T16:59:59Z'
        elif(x=="Agustus"):
            awal = year+'-07-31T17:00:00Z'
            akhir = year+'-08-31T16:59:59Z'
        elif(x=="September"):
            awal = year+'-08-31T17:00:00Z'
            akhir = year+'-09-30T16:59:59Z'
        elif(x=="Oktober"):
            awal = year+'-09-30T17:00:00Z'
            akhir = year+'-10-31T16:59:59Z'
        elif(x=="November"):
            awal = year+'-10-31T17:00:00Z'
            akhir = year+'-11-30T16:59:59Z'
        elif(x=="Desember"):
            awal = year+'-11-30T17:00:00Z'
            akhir = year+'-12-31T16:59:59Z'
        else:
            print("Bulan Tidak Ditemukan")
        try:
            client = InfluxDBClient(host='localhost',port=8086,database='telegraf')
            query = "SELECT derivative(mean(Upload),1s) AS Upload, derivative(mean(Download),1s) AS Download FROM \"" + context['username'] + "\" where time >= \'" + awal + "\' and time < \'" + akhir + "\' group by time(1s)"
            query2 = "SELECT derivative(mean(Upload),1s) AS Upload, derivative(mean(Download),1s) AS Download FROM \"" + context['username'] + "\" where time >= \'" + awal + "\' and time < \'" + akhir + "\' group by time(1m)"
            result = client.query(query)
            result2 = client.query(query2)
            point = list(result.get_points())
            point2 = list(result2.get_points())
            time = []
            upload = []
            download = []
            upload1 = []
            upload2 = []
            upload3 = []
            total = 0
            download1 = []
            download2 = []
            download3 = []
            total1 = 0    
            range1 = []
            range2 = []
            usage = []
            unduh = []
            unggah = []
            for poin in point2:
                time.append(poin['time'])
                unduh.append(poin['Download'])
                unggah.append(poin['Upload'])   
            for poin in point:
                if(poin['Upload']<=1250000):
                    upload1.append(poin['Upload'])
                elif((1250000<poin['Upload']) and (poin['Upload']<=2500000)):
                    upload2.append(poin['Upload'])
                elif(poin['Upload']>2500000):
                    upload3.append(poin['Upload'])
                else:
                    print("Tidak Ada Data")
                if(poin['Download']<=1250000):
                    download1.append(poin['Download'])
                elif((1250000<poin['Download']) and (poin['Download']<=2500000)):
                    download2.append(poin['Download'])
                elif(poin['Download']>2500000):
                    download3.append(poin['Download'])
                else:
                    print("Tidak Ada Data")
                upload.append(poin['Upload'])
                download.append(poin['Download'])
            total = sum(upload)
            total1 = sum(download)
            up = len(upload1)+len(upload2)+len(upload3)
            down = len(download1)+len(download2)+len(download3)
            up1 = "%.2f" %((len(upload1)/up) *100)
            up2 = "%.2f" %((len(upload2)/up) *100)
            up3 = "%.2f" %((len(upload3)/up) *100)
            down1 = "%.2f" %((len(download1)/down) *100)
            down2 = "%.2f" %((len(download2)/down) *100)
            down3 = "%.2f" %((len(download3)/down) *100)
            usage = [total,total1]
            range1 = [up1,up2,up3]
            range2 = [down1,down2,down3]
            langganan = []
            try:
                db = pymysql.connect("localhost","root","","monitoring")
                cursor = db.cursor()
                sqlquery = ("SELECT langganan FROM user_oid where name=\"{}\"").format(username)
                cursor.execute(sqlquery)
                result = cursor.fetchall()
                for x in result:
                    langganan.append(x[0])
                if(len(langganan)==0 or langganan == []):
                    biaya = "Rp 0"
                else:
                    if(langganan[0]=="10"):
                        jumlah = total+total1
                        biaya = "Rp {:,.2f}".format((jumlah/1000000) * 5)                                                                
                    elif(langganan[0]=="20"):
                        jumlah = total+total1
                        biaya = "Rp {:,.2f}".format((jumlah/1000000) * 10)
                    elif(langganan[0]=="50"):
                        jumlah = total+total1
                        biaya = "Rp {:,.2f}".format((jumlah/1000000) * 15)
                    elif(langganan[0]=="100"):
                        jumlah = total+total1
                        biaya = "Rp {:,.2f}".format((jumlah/1000000) * 20)
                    else:
                        biaya = "Rp 0" 
            except Exception as e:
                msg = str(e)
                pesan = "Error! Database tidak merespon."
                influx = {
                    'msg' : msg,
                    'pesan' :  pesan,
                }
                json_object = json.dumps(influx)
                return Response(influx)
        except ConnectionError as e :
            msg = str(e)
            print(msg)
            pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
            influx = {
                'msg' : msg,
                'pesan' :  pesan,
            }
            json_object = json.dumps(influx)
            return Response(influx)
        except requests.exceptions.Timeout as e :
            msg = str(e)
            print(msg)
            pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
            influx = {
                'msg' : msg,
                'pesan' :  pesan,
            }
            json_object = json.dumps(influx)
            return Response(influx)   
        except Exception as e:
            msg = str(e)
            pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
            influx = {
                'msg' : msg,
                'pesan' :  pesan,
            }
            json_object = json.dumps(influx)
            return Response(influx)
        pesan = "Success"        
        influx = {
            'usage' : usage,
            'biaya' : biaya,
            'range1' : range1,
            'range2' : range2,
            'langganan' : langganan,
            'waktu' : time,
            'upload' : unggah,
            'download' : unduh,
            'pesan' : pesan,
        }
        json_object = json.dumps(influx)
        return Response(influx)
class RangeView(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request, username, awal, akhir, format=None):
        try:
            client = InfluxDBClient(host='localhost',port=8086,database='telegraf')
            context = {}
            context['username'] = "{}".format(username)
            context['awal'] = "{}".format(awal).replace('\"','')
            context['akhir'] = "{}".format(akhir).replace('\"','')
            query = "SELECT derivative(mean(Upload),1s) AS Upload, derivative(mean(Download),1s) AS Download FROM \"" + context['username'] + "\" where time >= \'" + context['awal'] + "\' and time < \'" + context['akhir'] + "\' group by time(1s)"
            query2 = "SELECT derivative(mean(Upload),1s) AS Upload, derivative(mean(Download),1s) AS Download FROM \"" + context['username'] + "\" where time >= \'" + context['awal'] + "\' and time < \'" + context['akhir'] + "\' group by time(1m)"
            result = client.query(query)
            result2 = client.query(query2)
            point = list(result.get_points())
            point2 = list(result2.get_points())
            time = []
            upload = []
            download = []
            upload1 = []
            upload2 = []
            upload3 = []
            total = 0
            download1 = []
            download2 = []
            download3 = []
            total1 = 0
            range1 = []
            range2 = []
            usage = []
            unduh = []
            unggah = []
            for poin in point2:
                time.append(poin['time'])
                unduh.append(poin['Download'])
                unggah.append(poin['Upload'])        
            for poin in point:
                if(poin['Upload']<=1250000):
                    upload1.append(poin['Upload'])
                elif((1250000<poin['Upload']) and (poin['Upload']<=2500000)):
                    upload2.append(poin['Upload'])
                elif(poin['Upload']>2500000):
                    upload3.append(poin['Upload'])
                else:
                    print("Tidak Ada Data")
                if(poin['Download']<=1250000):
                    download1.append(poin['Download'])
                elif((1250000<poin['Download']) and (poin['Download']<=2500000)):
                    download2.append(poin['Download'])
                elif(poin['Download']>2500000):
                    download3.append(poin['Download'])
                else:
                    print("Tidak Ada Data")
                upload.append(poin['Upload'])
                download.append(poin['Download'])
            total = sum(upload)
            total1 = sum(download)
            up = len(upload1)+len(upload2)+len(upload3)
            down = len(download1)+len(download2)+len(download3)
            up1 = "%.2f" %((len(upload1)/up) *100)
            up2 = "%.2f" %((len(upload2)/up) *100)
            up3 = "%.2f" %((len(upload3)/up) *100)
            down1 = "%.2f" %((len(download1)/down) *100)
            down2 = "%.2f" %((len(download2)/down) *100)
            down3 = "%.2f" %((len(download3)/down) *100)
            usage = [total,total1]
            range1 = [up1,up2,up3]
            range2 = [down1,down2,down3]
            langganan = []
            try:
                    db = pymysql.connect("localhost","root","","monitoring")
                    cursor = db.cursor()
                    sqlquery = ("SELECT langganan FROM user_oid where name=\"{}\"").format(username)
                    cursor.execute(sqlquery)
                    result = cursor.fetchall()
                    for x in result:
                        langganan.append(x[0])
                    if(len(langganan)==0):
                        biaya = "Rp 0"
                    else:
                        if(langganan[0]=="10"):
                            jumlah = total+total1
                            biaya = "Rp {:,.2f}".format((jumlah/1000000) * 5)                                                                
                        elif(langganan[0]=="20"):
                            jumlah = total+total1
                            biaya = "Rp {:,.2f}".format((jumlah/1000000) * 10)
                        elif(langganan[0]=="50"):
                            jumlah = total+total1
                            biaya = "Rp {:,.2f}".format((jumlah/1000000) * 15)
                        elif(langganan[0]=="100"):
                            jumlah = total+total1
                            biaya = "Rp {:,.2f}".format((jumlah/1000000) * 20) 
                            
            except Exception as e:
                    msg = str(e)
                    pesan = "Error! Database tidak merespon."
                    influx = {
                        'msg' : msg,
                        'pesan' :  pesan,
                    }
                    json_object = json.dumps(influx)
                    return Response(influx) 
        except ConnectionError as e :
            msg = str(e)
            print(msg)
            pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
            influx = {
                'msg' : msg,
                'pesan' :  pesan,
            }
            json_object = json.dumps(influx)
            return Response(influx)
        except requests.exceptions.Timeout as e :
            msg = str(e)
            print(msg)
            pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
            influx = {
                'msg' : msg,
                'pesan' :  pesan,
            }
            json_object = json.dumps(influx)
            return Response(influx)   
        except Exception as e:
            msg = str(e)
            pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
            influx = {
                'msg' : msg,
                'pesan' :  pesan,
            }
            json_object = json.dumps(influx)
            return Response(influx)
        pesan = "Success"        
        influx = {
            'usage' : usage,
            'biaya' : biaya,
            'range1' : range1,
            'range2' : range2,
            'langganan' : langganan,
            'waktu' : time,
            'upload' : unggah,
            'download' : unduh,
            'pesan' : pesan,
        }
        json_object = json.dumps(influx)
        return Response(influx)

class DataView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request,username='Test',format=None):
        context = {}
        context['username'] = "{}".format(username)
        check = context['username']
        if(check == "None"):
            pesan = "Silakan pilih pelanggan!"
            influx = {
                'pesan' :  pesan,
            }
            json_object = json.dumps(influx)
            return Response(influx)
        else:
            try:
                client = InfluxDBClient(host='localhost',port=8086,database='telegraf',timeout=5)
                query = "SELECT derivative(mean(Upload),1s) AS Upload, derivative(mean(Download),1s) AS Download FROM \"{}\" where time>= now()- 1h group by time(1s) fill(null)".format(username)
                result = client.query(query)
                point = list(result.get_points())
                time = []
                upload = []
                download = []
                upload1 = []
                upload2 = []
                upload3 = []
                total = 0
                download1 = []
                download2 = []
                download3 = []
                total1 = 0
                range1 = []
                range2 = []
                usage = []
                biaya = 0.0        
                for poin in point:
                    if(poin['Upload']<=1250000):
                        upload1.append(poin['Upload'])
                    elif((1250000<poin['Upload']) and (poin['Upload']<=2500000)):
                        upload2.append(poin['Upload'])
                    elif(poin['Upload']>2500000):
                        upload3.append(poin['Upload'])
                    else:
                        print("Tidak Ada Data")
                    if(poin['Download']<=1250000):
                        download1.append(poin['Download'])
                    elif((1250000<poin['Download']) and (poin['Download']<=2500000)):
                        download2.append(poin['Download'])
                    elif(poin['Download']>2500000):
                        download3.append(poin['Download'])
                    else:
                        print("Tidak Ada Data")
                    time.append(poin['time'])
                    upload.append(poin['Upload'])
                    download.append(poin['Download'])
                total = sum(upload)
                total1 = sum(download)
                up = len(upload1)+len(upload2)+len(upload3)
                down = len(download1)+len(download2)+len(download3)
                up1 = "%.2f" %((len(upload1)/up) *100)
                up2 = "%.2f" %((len(upload2)/up) *100)
                up3 = "%.2f" %((len(upload3)/up) *100)
                down1 = "%.2f" %((len(download1)/down) *100)
                down2 = "%.2f" %((len(download2)/down) *100)
                down3 = "%.2f" %((len(download3)/down) *100)
                usage = [total,total1]
                range1 = [up1,up2,up3]
                range2 = [down1,down2,down3]
                langganan = []
                try:
                    db = pymysql.connect("localhost","root","","monitoring")
                    cursor = db.cursor()
                    sqlquery = ("SELECT langganan FROM user_oid where name=\"{}\"").format(username)
                    cursor.execute(sqlquery)
                    result = cursor.fetchall()
                    for x in result:
                        langganan.append(x[0])
                    if(len(langganan)==0):
                        biaya = "Rp 0"
                    else:
                        if(langganan[0]=="10"):
                            jumlah = total+total1
                            biaya = "Rp {:,.2f}".format((jumlah/1000000) * 5)                                                                
                        elif(langganan[0]=="20"):
                            jumlah = total+total1
                            biaya = "Rp {:,.2f}".format((jumlah/1000000) * 10)
                        elif(langganan[0]=="50"):
                            jumlah = total+total1
                            biaya = "Rp {:,.2f}".format((jumlah/1000000) * 15)
                        elif(langganan[0]=="100"):
                            jumlah = total+total1
                            biaya = "Rp {:,.2f}".format((jumlah/1000000) * 20) 
                except Exception as e:
                    msg = str(e)
                    pesan = "Error! Database tidak merespon."
                    influx = {
                        'msg' : msg,
                        'pesan' :  pesan,
                    }
                    json_object = json.dumps(influx)
                    return Response(influx) 
            except ConnectionError as e :
                msg = str(e)
                print(msg)
                pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
                influx = {
                    'msg' : msg,
                    'pesan' :  pesan,
                }
                json_object = json.dumps(influx)
                return Response(influx)
            except requests.exceptions.Timeout as e :
                msg = str(e)
                print(msg)
                pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
                influx = {
                    'msg' : msg,
                    'pesan' :  pesan,
                }
                json_object = json.dumps(influx)
                return Response(influx)   
            except Exception as e:
                msg = str(e)
                pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
                influx = {
                    'msg' : msg,
                    'pesan' :  pesan,
                }
                json_object = json.dumps(influx)
                return Response(influx)
        pesan = "Success"        
        influx = {
            'usage' : usage,
            'biaya' : biaya,
            'range1' : range1,
            'range2' : range2,
            'langganan' : langganan,
            'waktu' : time,
            'upload' : upload,
            'download' : download,
            'pesan' : pesan,
        }
        json_object = json.dumps(influx)
        return Response(influx)

class SepuluhView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self,request,username="Test",format=None):
        context = {}
        context['username'] = "{}".format(username)
        check = context['username']
        if(check == "None"):
            pesan = "Silakan pilih pelanggan!"
            influx = {
                'pesan' :  pesan,
            }
            json_object = json.dumps(influx)
            return Response(influx)
        else:
            try:
                client = InfluxDBClient(host='localhost',port=8086,database='telegraf',timeout=5)
                query = "SELECT derivative(mean(Upload),1s) AS Upload, derivative(mean(Download),1s) AS Download FROM \"{}\" where time>= now()- 10s group by time(1s) fill(null)".format(username)
                result = client.query(query)
                point = list(result.get_points())
                time = []
                upload = []
                download = []
                for poin in point:
                    time.append(poin['time'])
                    upload.append(poin['Upload'])
                    download.append(poin['Download'])
            except ConnectionError as e :
                msg = str(e)
                print(msg)
                pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
                influx = {
                    'msg' : msg,
                    'pesan' :  pesan,
                }
                json_object = json.dumps(influx)
                return Response(influx)
            except requests.exceptions.Timeout as e :
                msg = str(e)
                print(msg)
                pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
                influx = {
                    'msg' : msg,
                    'pesan' :  pesan,
                }
                json_object = json.dumps(influx)
                return Response(influx)   
            except Exception as e:
                msg = str(e)
                pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
                influx = {
                    'msg' : msg,
                    'pesan' :  pesan,
                }
                json_object = json.dumps(influx)
                return Response(influx)
        pesan = "Success"
        influx = {
            'waktu' : time,
            'upload' : upload,
            'download' : download,
            'pesan' : pesan
        }
        return Response(influx)

class LiveView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self,request,username="Test",format=None):
        context = {}
        context['username'] = "{}".format(username)
        check = context['username']
        if(check == "None"):
            pesan = "Silakan pilih pelanggan!"
            influx = {
                'pesan' :  pesan,
            }
            json_object = json.dumps(influx)
            return Response(influx)
        else:
            try:
                client = InfluxDBClient(host='localhost',port=8086,database='telegraf',timeout=5)
                query = "SELECT derivative(mean(Upload),1s) AS Upload, derivative(mean(Download),1s) AS Download FROM \"{}\" where time>= now()- 2s group by time(1s)".format(username)
                result = client.query(query)
                point = list(result.get_points())
                time = []
                upload = []
                download = []
                for poin in point:
                    time.append(poin['time'])
                    upload.append(poin['Upload'])
                    download.append(poin['Download'])
            except ConnectionError as e :
                msg = str(e)
                print(msg)
                pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
                influx = {
                    'msg' : msg,
                    'pesan' :  pesan,
                }
                json_object = json.dumps(influx)
                return Response(influx)
            except requests.exceptions.Timeout as e :
                msg = str(e)
                print(msg)
                pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
                influx = {
                    'msg' : msg,
                    'pesan' :  pesan,
                }
                json_object = json.dumps(influx)
                return Response(influx)   
            except Exception as e:
                msg = str(e)
                pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
                influx = {
                    'msg' : msg,
                    'pesan' :  pesan,
                }
                json_object = json.dumps(influx)
                return Response(influx)
        pesan = "Success"
        influx = {
            'waktu' : time,
            'upload' : upload,
            'download' : download,
            'pesan' : pesan
        }
        return Response(influx)

def pelanggan(request):
    pelanggan = []
    db = pymysql.connect("localhost","root","","monitoring")
    cursor = db.cursor()
    cursor.execute("SELECT name FROM user_oid")
    result = cursor.fetchall()
    for x in result:
        pelanggan.append(x[0])
    pilihan = {
        'pelanggan' : pelanggan
    }
    return render(request,'list.html',pilihan)

class SpacingView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request,username='Test',format=None):
        context = {}
        context['username'] = "{}".format(username)
        check = context['username']
        if(check == "None"):
            pesan = "Silakan pilih pelanggan!"
            influx = {
                'pesan' :  pesan,
            }
            json_object = json.dumps(influx)
            return Response(influx)
        else:
            try:
                client = InfluxDBClient(host='localhost',port=8086,database='telegraf',timeout=5)
                query = "SELECT derivative(mean(Upload),1s) AS Upload, derivative(mean(Download),1s) AS Download FROM \"{}\" where time>= now()- 1h group by time(1s) fill(null)".format(username)
                result = client.query(query)
                point = list(result.get_points())
                query2 = "select space from bandwidth where time>= now() - 1h"
                result2 = client.query(query2)
                point2 = list(result2.get_points())
                spacing = []
                time2 = []
                time = []
                upload = []
                download = []        
                for poin in point:
                    time.append(poin['time'])
                    upload.append(poin['Upload'])
                    download.append(poin['Download'])
                for poin in point2:
                    spacing.append(poin['space'])
                    time2.append(poin['time'])
            except ConnectionError as e :
                msg = str(e)
                print(msg)
                pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
                influx = {
                    'msg' : msg,
                    'pesan' :  pesan,
                }
                json_object = json.dumps(influx)
                return Response(influx)
            except requests.exceptions.Timeout as e :
                msg = str(e)
                print(msg)
                pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
                influx = {
                    'msg' : msg,
                    'pesan' :  pesan,
                }
                json_object = json.dumps(influx)
                return Response(influx)   
            except Exception as e:
                msg = str(e)
                pesan = "Server Influx tidak merespon! Cek kembali koneksi ke Server."
                influx = {
                    'msg' : msg,
                    'pesan' :  pesan,
                }
                json_object = json.dumps(influx)
                return Response(influx)
        pesan = "Success"        
        influx = {
            'waktu' : time,
            'upload' : upload,
            'download' : download,
            'pesan' : pesan,
            'spacing' : spacing,
            'waktu2' : time2,
        }
        json_object = json.dumps(influx)
        return Response(influx)
