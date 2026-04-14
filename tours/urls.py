from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),               # Главная
    path('tours/', views.tour_list, name='tours'),         # Все туры
    path('about/', views.about, name='about'),         # О нас
    path('feedback/', views.feedback_view, name='feedback'), # Форма
]
