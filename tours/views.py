from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import F, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import LoginForm, ProfileUpdateForm, RegisterForm
from .models import (
    Category,
    Feedback,
    HomePageSettings,
    Review,
    ReviewComment,
    Tour,
    TourFavorite,
    TOUR_TYPE_CHOICES,
    UserProfile,
    WelcomeBlock,
)
from .services import send_tg_notification

MAX_REVIEW_WORDS = 120
REVIEW_PREVIEW_WORDS = 35

TOUR_CATEGORY_TABS = [
    {"slug": "jeep-tours", "name": "Джип-туры"},
    {"slug": "wellness", "name": "Оздоровительные"},
    {"slug": "one-day", "name": "Однодневные"},
    {"slug": "multi-day", "name": "Многодневные"},
    {"slug": "family", "name": "Семейные"},
    {"slug": "active", "name": "Активный отдых"},
    {"slug": "combined", "name": "Комбинированные"},
]

CATEGORY_TO_FEEDBACK_TYPE = {
    "jeep-tours": "jeep",
    "wellness": "wellness",
    "one-day": "one_day",
    "multi-day": "multi_day",
    "family": "family",
    "combined": "unknown",
    "active": "unknown",
}

POPULAR_DIRECTIONS = [
    {
        "title": "Махачкала",
        "image": "Главное меню_2.JPG",
        "tagline": "Столица у Каспия, музеи, Джума-мечеть и панорама Тарки-Тау.",
        "description": (
            "Город удобно ставить в начало маршрута: традиционный завтрак, "
            "исторические и этнографические музеи, прогулка по центру, пляж, "
            "смотровая Тарки-Тау и вечерняя Махачкала."
        ),
        "highlights": ["Музеи и культура", "Тарки-Тау", "Каспийское море"],
        "category": "one-day",
        "tour_type": "one_day",
    },
    {
        "title": "Бархан Сары-Кум",
        "image": "Главный экран_1.jpg",
        "tagline": "Крупная песчаная дюна рядом с Махачкалой и редкий природный контраст.",
        "description": (
            "Сары-Кум часто включают в маршрут к Сулакскому каньону. Здесь "
            "важно идти по настилам, беречь экосистему и учитывать жару в сезон."
        ),
        "highlights": ["Смотровые настилы", "Заповедная территория", "Легенды бархана"],
        "category": "one-day",
        "tour_type": "one_day",
    },
    {
        "title": "Главрыба и Сулак",
        "image": "Комбинированный тур - Джип + Оздоровительный.jpg",
        "tagline": "Экотуркомплекс на реке Сулак, форель, катера и локации рядом с каньоном.",
        "description": (
            "В один день удобно соединить Сары-Кум, Главрыбу, пещеры Нохъо, "
            "Чиркейскую ГЭС, смотровые Сулакского каньона и водную прогулку."
        ),
        "highlights": ["Форель и кухня", "Катера по Сулаку", "Пещеры Нохъо"],
        "category": "combined",
        "tour_type": "unknown",
    },
]

TOUR_TYPE_CARDS = [
    {
        "title": "Природные маршруты",
        "description": "Каньоны, водопады, горы, бархан и смотровые без лишней спешки.",
        "category": "one-day",
    },
    {
        "title": "Исторические экскурсии",
        "description": "Дербент, крепости, аулы, музеи и культура народов Дагестана.",
        "category": "one-day",
    },
    {
        "title": "Активный отдых",
        "description": "Джипы, горные тропы, канатные дороги и активности по сезону.",
        "category": "active",
    },
    {
        "title": "Оздоровительный отдых",
        "description": "Термальные и минеральные источники с учетом самочувствия гостей.",
        "category": "wellness",
    },
    {
        "title": "Походы и кемпинг",
        "description": "Палатки, лошади, квадроциклы или джип-маршруты в горах.",
        "category": "active",
    },
    {
        "title": "Комбинированные туры",
        "description": "Горы, море, кухня, мастер-классы и отдых в одном маршруте.",
        "category": "combined",
    },
]

TOUR_INCLUDES = [
    "Трансфер по маршруту",
    "Проживание в гостевом доме по договоренности",
    "Сопровождение гида",
    "Безопасный маршрут и помощь в дороге",
    "Питание и национальная кухня, если предусмотрено программой",
    "Мастер-классы и экскурсии по маршруту",
]

DAY_ROUTE_EXAMPLE = [
    ("08:00", "Традиционный завтрак", "Спокойный старт дня и короткий брифинг по маршруту."),
    ("10:00", "Первая локация", "Смотровая, музей, бархан или горный маршрут по выбранной категории."),
    ("13:30", "Обед", "Национальная кухня или ресторанный дворик по погоде и логистике."),
    ("15:00", "Главная точка дня", "Каньон, Дербент, Главрыба, источники или высокогорье."),
    ("18:30", "Возвращение и ужин", "Вечерняя прогулка, гостевой дом или трансфер к месту проживания."),
]

ACCENT_TOURS = [
    {
        "title": "Оздоровительный тур",
        "image": "Оздоровительный тур - Все включено.jpg",
        "description": (
            "Посещение термальных и минеральных источников, море по желанию, "
            "Дербент, Сулакский каньон и спокойный ритм поездки."
        ),
        "note": "Перед посещением лечебных источников важно учитывать состояние здоровья.",
        "category": "wellness",
        "tour_type": "wellness",
    },
    {
        "title": "Джип-туры в горы",
        "image": "Джип-тур - Все включено.jpg",
        "description": (
            "Видовые дороги, высокогорные маршруты, гостевые дома, кухня и "
            "безопасное сопровождение гида."
        ),
        "note": "Маршрут подбирается по сезону, погоде и подготовке группы.",
        "category": "jeep-tours",
        "tour_type": "jeep",
    },
]


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


def _category_tabs(categories):
    fixed_slugs = {item["slug"] for item in TOUR_CATEGORY_TABS}
    tabs = [{"slug": "", "name": "Все"}] + TOUR_CATEGORY_TABS.copy()
    for category in categories:
        if category.slug not in fixed_slugs:
            tabs.append({"slug": category.slug, "name": category.name})
    return tabs


def _valid_feedback_type(value):
    allowed = {choice[0] for choice in TOUR_TYPE_CHOICES}
    return value if value in allowed else ""


def _safe_next(next_url: str, fallback: str) -> str:
    if next_url and next_url.startswith("/"):
        return next_url
    return fallback


def index(request):
    welcome_blocks = WelcomeBlock.objects.all().order_by("order")
    tours = Tour.objects.select_related("category").prefetch_related("photos").order_by("-id")[:3]
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
            "popular_directions": POPULAR_DIRECTIONS,
            "tour_type_cards": TOUR_TYPE_CARDS,
            "favorite_tour_ids": _favorite_ids_for_user(request),
        },
    )


def tour_list(request):
    category_slug = request.GET.get("category")
    categories = Category.objects.all().order_by("name")

    if category_slug:
        tours = Tour.objects.filter(category__slug=category_slug)
    else:
        tours = Tour.objects.all()

    tours = tours.select_related("category").prefetch_related("photos").order_by("-id")

    return render(
        request,
        "tours.html",
        {
            "tours": tours,
            "categories": categories,
            "category_tabs": _category_tabs(categories),
            "active_category": category_slug,
            "tour_includes": TOUR_INCLUDES,
            "day_route_example": DAY_ROUTE_EXAMPLE,
            "accent_tours": ACCENT_TOURS,
            "favorite_tour_ids": _favorite_ids_for_user(request),
        },
    )


def feedback_view(request):
    tour_id = request.GET.get("tour_id")
    selected_type = _valid_feedback_type(request.GET.get("tour_type") or "")
    selected_tour = None
    if tour_id:
        selected_tour = Tour.objects.select_related("category").filter(id=tour_id).first()
        if selected_tour and selected_tour.category and not selected_type:
            selected_type = CATEGORY_TO_FEEDBACK_TYPE.get(selected_tour.category.slug, "")

    all_tours = Tour.objects.all().order_by("title")

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
                    "selected_type": selected_type,
                    "tour_type_choices": TOUR_TYPE_CHOICES,
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
        form_tour_type = _valid_feedback_type(request.POST.get("tour_type") or "")

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
            tour_type=form_tour_type,
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
            "selected_type": selected_type,
            "tour_type_choices": TOUR_TYPE_CHOICES,
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

        words_count = len(text.split()) if text else 0
        if words_count > MAX_REVIEW_WORDS:
            errors.append(f"Отзыв слишком длинный. Максимум {MAX_REVIEW_WORDS} слов.")

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
        approved_reviews.filter(is_pinned=True).order_by(
            "-pinned_at", "-likes_count", "-created_at"
        )
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
            "review_word_limit": MAX_REVIEW_WORDS,
            "review_preview_words": REVIEW_PREVIEW_WORDS,
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
        return redirect("profile")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация завершена.")
            return redirect("profile")
    else:
        form = RegisterForm()

    return render(request, "auth_register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("profile")

    next_url = request.GET.get("next") or request.POST.get("next") or reverse("profile")
    next_url = _safe_next(next_url, reverse("profile"))

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


def profile_view(request):
    if not request.user.is_authenticated:
        return render(request, "profile_guest.html")

    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={"phone": ""})

    if request.method == "POST":
        profile_form = ProfileUpdateForm(request.POST, user=request.user)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Профиль обновлен.")
            return redirect("profile")
    else:
        profile_form = ProfileUpdateForm(user=request.user)

    favorites = (
        TourFavorite.objects.filter(user=request.user)
        .select_related("tour")
        .order_by("-created_at")
    )
    feedbacks = (
        Feedback.objects.filter(user=request.user)
        .select_related("tour")
        .order_by("-created_at")
    )
    my_reviews = Review.objects.filter(user=request.user).order_by("-created_at")
    my_comments = (
        ReviewComment.objects.filter(user=request.user)
        .select_related("review")
        .order_by("-created_at")
    )

    return render(
        request,
        "cabinet.html",
        {
            "profile": profile,
            "profile_form": profile_form,
            "favorites": favorites,
            "feedbacks": feedbacks,
            "my_reviews": my_reviews,
            "my_comments": my_comments,
        },
    )


def cabinet_view(request):
    return redirect("profile")
