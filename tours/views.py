from django.db.models import F, Prefetch
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Tour, Feedback, HomePageSettings, WelcomeBlock, Category, Review, ReviewComment
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


def index(request):
    """Главная страница с турами и настройками."""
    welcome_blocks = WelcomeBlock.objects.all().order_by('order')
    tours = Tour.objects.all().order_by('-id')[:3]
    settings = HomePageSettings.objects.first()
    if not settings:
        settings = HomePageSettings.objects.create()
        
    return render(request, 'index.html', {
        'tours': tours,
        'settings': settings,
        'welcome_blocks': welcome_blocks,
    })

def tour_list(request):
    """Страница со списком всех туров с фильтрацией."""
    category_slug = request.GET.get('category')
    categories = Category.objects.all()
    
    if category_slug:
        tours = Tour.objects.filter(category__slug=category_slug)
    else:
        tours = Tour.objects.all()
        
    return render(request, 'tours.html', {
        'tours': tours,
        'categories': categories,
        'active_category': category_slug
    })

def feedback_view(request):
    tour_id = request.GET.get('tour_id')
    selected_tour = None
    if tour_id:
        selected_tour = Tour.objects.filter(id=tour_id).first()

    all_tours = Tour.objects.all()

    if request.method == 'POST':
        if _is_rate_limited(request, "feedback_form", limit=8, window_seconds=3600):
            return render(request, 'feedback.html', {
                'tours': all_tours,
                'selected_tour': selected_tour,
                'rate_limit_error': 'Слишком много заявок с вашего IP. Попробуйте еще раз через час.',
            })

        name = request.POST.get('name')
        phone = request.POST.get('phone')
        date = request.POST.get('date')
        comment = request.POST.get('comment')
        form_tour_id = request.POST.get('tour_id')
        
        fb = Feedback.objects.create(
            name=name,
            phone=phone,
            date=date,
            comment=comment,
            tour_id=form_tour_id if form_tour_id else None
        )

        try:
            send_tg_notification(fb)
        except Exception as e:
            print(f"Error sending TG: {e}")

        return render(request, 'success.html')

    return render(request, 'feedback.html', {
        'tours': all_tours,
        'selected_tour': selected_tour,
        'rate_limit_error': None,
    })

def about(request):
    return render(request, 'about.html')


def reviews(request):
    errors = []
    like_rate_limited = request.GET.get("like_rate_limited") == "1"
    comment_submitted = request.GET.get("comment_submitted") == "1"
    comment_rate_limited = request.GET.get("comment_rate_limited") == "1"
    comment_error = request.GET.get("comment_error") == "1"
    form_data = {
        "name": "",
        "city": "",
        "rating": "5",
        "text": "",
    }

    if request.method == "POST":
        if _is_rate_limited(request, "review_form", limit=6, window_seconds=3600):
            errors.append("Слишком много отзывов с вашего IP. Попробуйте еще раз через час.")

        name = (request.POST.get("name") or "").strip()
        city = (request.POST.get("city") or "").strip()
        text = (request.POST.get("text") or "").strip()
        rating_raw = (request.POST.get("rating") or "").strip()

        form_data = {
            "name": name,
            "city": city,
            "rating": rating_raw or "5",
            "text": text,
        }

        if len(name) < 2:
            errors.append("Укажите имя (минимум 2 символа).")
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
                name=name,
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
    popular_reviews = list(
        approved_reviews.order_by("-likes_count", "-created_at")[:5]
    )
    popular_ids = [review.id for review in popular_reviews]
    recent_reviews = list(
        approved_reviews.exclude(id__in=popular_ids).order_by("-created_at")
    )

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
            "popular_reviews": popular_reviews,
            "recent_reviews": recent_reviews,
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


@require_POST
def add_review_comment(request, review_id):
    review = get_object_or_404(Review, id=review_id, is_approved=True)

    if _is_rate_limited(request, "review_comment", limit=20, window_seconds=3600):
        return redirect(f"{reverse('reviews')}?comment_rate_limited=1#review-{review.id}")

    name = (request.POST.get("name") or "").strip()
    text = (request.POST.get("text") or "").strip()

    if len(name) < 2 or len(text) < 3:
        return redirect(f"{reverse('reviews')}?comment_error=1#review-{review.id}")

    ReviewComment.objects.create(
        review=review,
        name=name,
        text=text,
    )

    return redirect(f"{reverse('reviews')}?comment_submitted=1#review-{review.id}")
