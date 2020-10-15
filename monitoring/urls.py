from django.urls import path
from . views import *
from monitoring.views import LiveView,SepuluhView,get_data,DataView,LoginView, HomeView, CanvasView, pelanggan, RangeView, BulanView, ChartView,SpacingView,SpaceView

urlpatterns = [
    path('tambah/',LoginView.as_view(), name='getuser'),
    path('canvas/', CanvasView.as_view(), name='canvas'),
    path('chart/', ChartView.as_view(), name='chart'),
    path('space/',SpaceView.as_view(),name='space'),
    path('data/', get_data),
    path('api/chart/<username>/', DataView.as_view()),
    path('api/chart/<username>/<bulan>/', BulanView.as_view()),
    path('api/chart/<username>/<awal>/<akhir>', RangeView.as_view()),
    path('api/chart/', DataView.as_view()),
    path('api/live/<username>/', SepuluhView.as_view()),
    path('api/live/add/<username>/',LiveView.as_view()),
    path('api/spacing/<username>/',SpacingView.as_view()),
]
