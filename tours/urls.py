from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),                      # Главная
    path('tours/', views.tour_list, name='tours'),        # Все туры (исправлено с 'tours' на 'tour_list')
    path('reviews/', views.reviews, name='reviews'),      # Отзывы
    path('reviews/<int:review_id>/like/', views.like_review, name='like_review'),
    path('reviews/<int:review_id>/comment/', views.add_review_comment, name='add_review_comment'),
    path('about/', views.about, name='about'),                # О нас
    path('feedback/', views.feedback_view, name='feedback'),  # Форма
]
