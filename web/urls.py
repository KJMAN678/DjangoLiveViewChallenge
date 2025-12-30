from django.urls import path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("board/<int:board_id>/", views.BoardDetailView.as_view(), name="board_detail"),
]
