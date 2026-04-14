from django.shortcuts import render, redirect
from .models import Tour, Feedback, HomePageSettings
from .services import send_tg_notification

def index(request):
    """Главная страница с турами и настройками."""
    # Берем последние 3 тура
    tours = Tour.objects.all().order_by('-id')[:3]
    
    # Берем настройки главной (или создаем пустые, если их нет)
    settings = HomePageSettings.objects.first()
    if not settings:
        settings = HomePageSettings.objects.create()
        
    return render(request, 'index.html', {
        'tours': tours,
        'settings': settings
    })

def tour_list(request):
    """Страница со списком всех туров."""
    tours = Tour.objects.all()
    return render(request, 'tours.html', {'tours': tours})

def feedback_view(request):
    """Страница формы бронирования и обработка заявок."""
    # 1. Пытаемся понять, пришел ли человек по кнопке конкретного тура
    tour_id = request.GET.get('tour_id')
    selected_tour = None
    if tour_id:
        selected_tour = Tour.objects.filter(id=tour_id).first()

    # 2. Достаем все туры для выпадающего списка в форме
    all_tours = Tour.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        date = request.POST.get('date')
        comment = request.POST.get('comment')
        form_tour_id = request.POST.get('tour_id')
        
        # Сохраняем заявку в базу данных
        fb = Feedback.objects.create(
            name=name,
            phone=phone,
            date=date,
            comment=comment,
            tour_id=form_tour_id if form_tour_id else None
        )

        # 3. ЛОГИКА ОТПРАВКИ В TELEGRAM
        print(f"--- DEBUG: Новая заявка от {name} ---")
        try:
            # Вызываем функцию из services.py
            send_tg_notification(fb)
            print("--- DEBUG: Уведомление в Telegram отправлено успешно ---")
        except Exception as e:
            # Если бот упадет, сайт продолжит работать, а мы увидим ошибку в логах
            print(f"--- DEBUG ERROR: Ошибка при отправке в TG: {e} ---")

        # После успешной отправки показываем страницу благодарности
        return render(request, 'success.html')

    # 4. Рендерим страницу формы
    return render(request, 'feedback.html', {
        'tours': all_tours,
        'selected_tour': selected_tour
    })

def about(request):
    """Страница о Дагестане."""
    return render(request, 'about.html')