from django.urls import path
from . import views

urlpatterns = [
    path("ajax", views.ajax, name="ajax"),
    path("room", views.room, name="room"),
    path('', views.index, name='index'),
]
