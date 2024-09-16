from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("pick_player", views.pick_player, name="pick_player")
]