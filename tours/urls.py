from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("profile/", views.profile_view, name="profile"),
    path("tours/", views.tour_list, name="tours"),
    path("tours/<slug:slug>/", views.tour_detail, name="tour_detail"),
    path("tours/<int:tour_id>/favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("reviews/", views.reviews, name="reviews"),
    path("reviews/<int:review_id>/like/", views.like_review, name="like_review"),
    path("reviews/<int:review_id>/comment/", views.add_review_comment, name="add_review_comment"),
    path("about/", views.about, name="about"),
    path("feedback/", views.feedback_view, name="feedback"),
    path("account/register/", views.register_view, name="register"),
    path("account/login/", views.login_view, name="login"),
    path("account/logout/", views.logout_view, name="logout"),
    path("account/cabinet/", views.cabinet_view, name="cabinet"),
]
