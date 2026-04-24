from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import F, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import LoginForm, RegisterForm
from .models import (
    Category,
    Feedback,
    HomePageSettings,
    Review,
    ReviewComment,
    Tour,
    TourFavorite,
    UserProfile,
    WelcomeBlock,
)
from .services import send_tg_notification


def _get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _is_rate_limited(request, scope: str, limit: int, window_seconds: int) -> bool:
    client_ip = _get_client_ip(request)
    cache_key = f"rate_limit:{scope}:{client_ip}"

    if cache.add(cache_key, 1, timeout=window_seconds):
        return False

    try:
        current_count = cache.incr(cache_key)
    except Exception:
        current_count = int(cache.get(cache_key, 0)) + 1
        cache.set(cache_key, current_count, timeout=window_seconds)

    return current_count > limit


def _display_name(user) -> str:
    full_name = (user.get_full_name() or "").strip()
    if full_name:
        return full_name
    return user.username


def _favorite_ids_for_user(request):
    if not request.user.is_authenticated:
        return set()
    return set(
        TourFavorite.objects.filter(user=request.user).values_list("tour_id", flat=True)
    )


def _safe_next(next_url: str, fallback: str) -> str:
    if next_url and next_url.startswith("/"):
        return next_url
    return fallback


def index(request):
    welcome_blocks = WelcomeBlock.objects.all().order_by("order")
    tours = Tour.objects.all().order_by("-id")[:3]
    settings = HomePageSettings.objects.first()
    if not settings:
        settings = HomePageSettings.objects.create()

    return render(
        request,
        "index.html",
        {
            "tours": tours,
            "settings": settings,
            "welcome_blocks": welcome_blocks,
            "favorite_tour_ids": _favorite_ids_for_user(request),
        },
    )


def tour_list(request):
    category_slug = request.GET.get("category")
    categories = Category.objects.all()

    if category_slug:
        tours = Tour.objects.filter(category__slug=category_slug)
    else:
        tours = Tour.objects.all()

    return render(
        request,
        "tours.html",
        {
            "tours": tours,
            "categories": categories,
            "active_category": category_slug,
            "favorite_tour_ids": _favorite_ids_for_user(request),
        },
    )


def feedback_view(request):
    tour_id = request.GET.get("tour_id")
    selected_tour = None
    if tour_id:
        selected_tour = Tour.objects.filter(id=tour_id).first()

    all_tours = Tour.objects.all()

    prefill_name = ""
    prefill_phone = ""
    if request.user.is_authenticated:
        prefill_name = _display_name(request.user)
        profile = getattr(request.user, "profile", None)
        if profile:
            prefill_phone = profile.phone

    if request.method == "POST":
        if _is_rate_limited(request, "feedback_form", limit=8, window_seconds=3600):
            return render(
                request,
                "feedback.html",
                {
                    "tours": all_tours,
                    "selected_tour": selected_tour,
                    "rate_limit_error": "Слишком много заявок с вашего IP. Попробуйте еще раз через час.",
                    "prefill_name": prefill_name,
                    "prefill_phone": prefill_phone,
                },
            )

        name = (request.POST.get("name") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        date = request.POST.get("date")
        comment = request.POST.get("comment")
        form_tour_id = request.POST.get("tour_id")

        if request.user.is_authenticated:
            if not name:
                name = _display_name(request.user)
            if not phone:
                profile = getattr(request.user, "profile", None)
                if profile:
                    phone = profile.phone

        fb = Feedback.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=name,
            phone=phone,
            date=date,
            comment=comment,
            tour_id=form_tour_id if form_tour_id else None,
        )

        try:
            send_tg_notification(fb)
        except Exception as e:
            print(f"Error sending TG: {e}")

        return render(request, "success.html")

    return render(
        request,
        "feedback.html",
        {
            "tours": all_tours,
            "selected_tour": selected_tour,
            "rate_limit_error": None,
            "prefill_name": prefill_name,
            "prefill_phone": prefill_phone,
        },
    )


def about(request):
    return render(request, "about.html")


def reviews(request):
    errors = []
    like_rate_limited = request.GET.get("like_rate_limited") == "1"
    comment_submitted = request.GET.get("comment_submitted") == "1"
    comment_rate_limited = request.GET.get("comment_rate_limited") == "1"
    comment_error = request.GET.get("comment_error") == "1"

    form_data = {
        "city": "",
        "rating": "5",
        "text": "",
    }

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={reverse('reviews')}")

        if _is_rate_limited(request, "review_form", limit=6, window_seconds=3600):
            errors.append("Слишком много отзывов с вашего IP. Попробуйте еще раз через час.")

        city = (request.POST.get("city") or "").strip()
        text = (request.POST.get("text") or "").strip()
        rating_raw = (request.POST.get("rating") or "").strip()

        form_data = {
            "city": city,
            "rating": rating_raw or "5",
            "text": text,
        }

        if len(text) < 10:
            errors.append("Текст отзыва должен содержать минимум 10 символов.")

        try:
            rating = int(rating_raw)
            if rating < 1 or rating > 5:
                errors.append("Оценка должна быть от 1 до 5.")
        except ValueError:
            errors.append("Выберите корректную оценку.")
            rating = 5

        if not errors:
            Review.objects.create(
                user=request.user,
                name=_display_name(request.user),
                city=city,
                rating=rating,
                text=text,
            )
            return redirect(f"{reverse('reviews')}?submitted=1")

    approved_reviews = Review.objects.filter(is_approved=True).prefetch_related(
        Prefetch(
            "comments",
            queryset=ReviewComment.objects.filter(is_approved=True).order_by("-created_at"),
        )
    )

    pinned_reviews = list(
        approved_reviews.filter(is_pinned=True).order_by("-pinned_at", "-likes_count", "-created_at")
    )
    regular_reviews = list(approved_reviews.filter(is_pinned=False).order_by("-created_at"))

    liked_review_ids = []
    for review_id in request.session.get("liked_reviews", []):
        try:
            liked_review_ids.append(int(review_id))
        except (TypeError, ValueError):
            continue

    return render(
        request,
        "reviews.html",
        {
            "pinned_reviews": pinned_reviews,
            "regular_reviews": regular_reviews,
            "total_reviews": approved_reviews.count(),
            "liked_review_ids": liked_review_ids,
            "submitted": request.GET.get("submitted") == "1",
            "like_rate_limited": like_rate_limited,
            "comment_submitted": comment_submitted,
            "comment_rate_limited": comment_rate_limited,
            "comment_error": comment_error,
            "errors": errors,
            "form_data": form_data,
        },
    )


@require_POST
def like_review(request, review_id):
    if _is_rate_limited(request, "review_like", limit=120, window_seconds=600):
        return redirect(f"{reverse('reviews')}?like_rate_limited=1")

    review = get_object_or_404(Review, id=review_id, is_approved=True)
    liked_reviews = request.session.get("liked_reviews", [])
    liked_review_ids = set()

    for liked_id in liked_reviews:
        try:
            liked_review_ids.add(int(liked_id))
        except (TypeError, ValueError):
            continue

    if review.id in liked_review_ids:
        Review.objects.filter(id=review.id, likes_count__gt=0).update(
            likes_count=F("likes_count") - 1
        )
        liked_review_ids.remove(review.id)
    else:
        Review.objects.filter(id=review.id).update(likes_count=F("likes_count") + 1)
        liked_review_ids.add(review.id)

    request.session["liked_reviews"] = list(liked_review_ids)
    request.session.modified = True

    return redirect("reviews")


@login_required
@require_POST
def add_review_comment(request, review_id):
    review = get_object_or_404(Review, id=review_id, is_approved=True)

    if _is_rate_limited(request, "review_comment", limit=20, window_seconds=3600):
        return redirect(f"{reverse('reviews')}?comment_rate_limited=1#review-{review.id}")

    text = (request.POST.get("text") or "").strip()

    if len(text) < 3:
        return redirect(f"{reverse('reviews')}?comment_error=1#review-{review.id}")

    ReviewComment.objects.create(
        review=review,
        user=request.user,
        name=_display_name(request.user),
        text=text,
    )

    return redirect(f"{reverse('reviews')}?comment_submitted=1#review-{review.id}")


@login_required
@require_POST
def toggle_favorite(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    favorite = TourFavorite.objects.filter(user=request.user, tour=tour)
    if favorite.exists():
        favorite.delete()
    else:
        TourFavorite.objects.create(user=request.user, tour=tour)

    next_url = _safe_next(
        request.POST.get("next") or request.META.get("HTTP_REFERER", ""),
        reverse("tours"),
    )
    return redirect(next_url)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("cabinet")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация завершена.")
            return redirect("cabinet")
    else:
        form = RegisterForm()

    return render(request, "auth_register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("cabinet")

    next_url = request.GET.get("next") or request.POST.get("next") or reverse("cabinet")
    next_url = _safe_next(next_url, reverse("cabinet"))

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(next_url)
    else:
        form = LoginForm(request)

    return render(request, "auth_login.html", {"form": form, "next": next_url})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("index")


@login_required
def cabinet_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={"phone": ""})

    favorites = TourFavorite.objects.filter(user=request.user).select_related("tour").order_by("-created_at")
    feedbacks = Feedback.objects.filter(user=request.user).select_related("tour").order_by("-created_at")
    my_reviews = Review.objects.filter(user=request.user).order_by("-created_at")
    my_comments = ReviewComment.objects.filter(user=request.user).select_related("review").order_by("-created_at")

    return render(
        request,
        "cabinet.html",
        {
            "profile": profile,
            "favorites": favorites,
            "feedbacks": feedbacks,
            "my_reviews": my_reviews,
            "my_comments": my_comments,
        },
    )
