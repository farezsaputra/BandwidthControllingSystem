from django.urls import path
from . views import *
from . import views

urlpatterns = [
    path('setconfig/', views.set_config, name="setconfig"),
    path('forecasting/', views.set_forecast, name="set_forecast"),
    path('setcontrol/', views.set_control, name="setcontrol"),
    path('logactivity', views.get_log_activity, name="getlog")    
    #path('backup/', views.backup, name="backup")
]