from django.shortcuts import render, redirect
from .models import Tour, Feedback, HomePageSettings, WelcomeBlock, Category
from .services import send_tg_notification

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
        'selected_tour': selected_tour
    })

def about(request):
    return render(request, 'about.html')