from django.shortcuts import render
import routeros_api
from routeros import login
# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.forms.utils import ErrorList
from django.http import HttpResponse
from .models import *
from .forms import SetValueForm , SetValue


def set_value(request):
    if request.method == 'POST':
        form = SetValue(request.POST)
        if form.is_valid():
            forms = request.POST
            print(request.POST)
            disprof = forms['showprofile']
            disqueue = forms['showqueue']
            uploads = forms['upload']
            downloads = forms['download']
            try:
                # routeros = login('admin', '4dm1ntr1', '202.169.224.45', '8738')
                # routeros.query('queue/simple/print')
                # print("success")
                # routeros.close()
                # print(uploads)
                # print(downloads)
                #connection = routeros_api.RouterOsApiPool('202.169.224.4 5', username='admin', password='4dm1ntr1', port=8738, plaintext_login=True)
                if disprof == profile.objects.get(id=1).name:
                    n = 1
                    m = 1
                    if disqueue == child.objects.get(id=1).cname:
                        o = 1
                    else :
                        o = 2
                else :
                    n = 2
                    m = 2
                    o = 2
                profres = profile.objects.get(id=n)
                parres = parent.objects.get(id=m)
                chires = child.objects.get(id=o)
                connection = routeros_api.RouterOsApiPool(profres.ipadd, username=profres.username, password=profres.password, port=profres.portapi, plaintext_login=True)
                api = connection.get_api()
                simple = api.get_resource("/queue/simple") 
                simple.set(id=str(chires.id), max_limit="{}/{}".format(uploads,downloads))
                connection.disconnect()
            except Exception as e:
                print("Failed to set "+ e)

            msg     = "Value edited."
            success = True
            context = {
                'form': form,
                'msg': msg,
                'success': success
            }
            
            return render(request, "value.html", context)
        #else:
        #    msg = 'Form is not valid'    
    else:
        form = SetValue()
        profile_result=profile.objects.all()
        queue_result=child.objects.all() 
        #print("gagal")

    return render(request, "value.html", {"form": form,'profile_result': profile_result,'queue_result': queue_result})
# def backup(request):
#     if request.method == 'POST':
#             backups = 
