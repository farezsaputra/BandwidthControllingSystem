from django.urls import path
from . views import *
from . import views

urlpatterns = [
    path('setconfig/', views.set_config, name="setconfig"),
    path('forecasting/', views.set_forecast, name="set_forecast")
    #path('backup/', views.backup, name="backup")
]