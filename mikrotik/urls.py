from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path('setconfig/', views.set_config, name="setconfig")
    #path('setvalue/', views.showprofile, name="showprofile")
    #path('backup/', views.backup, name="backup")
]