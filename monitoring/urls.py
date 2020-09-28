from django.urls import path
from . views import *
from monitoring.views import grafik,get_data,DataView,LoginView, HomeView, CanvasView, pelanggan, RangeView, BulanView

urlpatterns = [
    path('tambah/',LoginView.as_view(), name='getuser'),
    path('canvas/', CanvasView.as_view(), name='canvas'),
    path('data/', get_data),
    path('api/chart/<username>/', DataView.as_view()),
    path('api/chart/<username>/<bulan>/', BulanView.as_view()),
    path('api/chart/<username>/<awal>/<akhir>', RangeView.as_view()),
    path('api/chart/', DataView.as_view()),
]
