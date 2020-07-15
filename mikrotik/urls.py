from django.urls import path
from .views import set_value
from . import views

urlpatterns = [
    path('setvalue/', views.set_value, name="setvalue")
    #path('setvalue/', views.showprofile, name="showprofile")
    #path('backup/', views.backup, name="backup")
]