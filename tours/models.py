from django.conf import settings
from django.db import models


TOUR_TYPE_CHOICES = (
    ("jeep", "Джип-тур"),
    ("wellness", "Оздоровительный"),
    ("one_day", "Однодневный"),
    ("multi_day", "Многодневный"),
    ("family", "Семейный"),
    ("individual", "Индивидуальный"),
    ("unknown", "Пока не знаю, нужна консультация"),
)


class Category(models.Model):
    name = models.CharField("Название категории", max_length=100)
    slug = models.SlugField("Слаг (для URL)", unique=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Tour(models.Model):
    title = models.CharField("Название тура", max_length=200)
    short_description = models.CharField(
        "Короткое описание для карточки",
        max_length=260,
        blank=True,
        default="",
        help_text="1-2 коротких предложения. Длинное описание оставьте в поле ниже.",
    )
    description = models.TextField("Описание")
    duration = models.CharField("Длительность", max_length=80, blank=True, default="")
    trip_format = models.CharField(
        "Формат поездки",
        max_length=120,
        blank=True,
        default="",
        help_text="Например: персональный, парный, семейный, компания.",
    )
    included_items = models.TextField(
        "Что входит",
        blank=True,
        default="",
        help_text="Каждый пункт с новой строки. На карточке показываются первые 5 пунктов.",
    )
    price = models.IntegerField("Цена (руб.)")
    is_group_tour = models.BooleanField("Групповой тур?", default=False)
    main_image = models.ImageField("Главное фото", upload_to="tours/")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tours",
        verbose_name="Категория",
    )

    def __str__(self):
        return self.title

    @property
    def card_description(self):
        return self.short_description or self.description

    @property
    def duration_label(self):
        return self.duration or "По договоренности"

    @property
    def format_label(self):
        if self.trip_format:
            return self.trip_format
        if self.is_group_tour:
            return "Группа или компания"
        return "Персональный, парный или семейный"

    @property
    def included_list(self):
        items = [
            item.strip(" -•")
            for item in self.included_items.splitlines()
            if item.strip(" -•")
        ]
        if items:
            return items[:5]

        defaults = [
            "Сопровождение гида",
            "Безопасный маршрут",
            "Помощь с размещением",
            "Консультация по маршруту",
        ]
        if self.category and self.category.slug == "wellness":
            defaults.append("Учет самочувствия и противопоказаний")
        else:
            defaults.append("Лучшие локации по сезону")
        return defaults


class TourPhoto(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField("Доп. фото", upload_to="tours/gallery/")


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    phone = models.CharField("Телефон", max_length=20)

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"Профиль {self.user.username}"


class TourFavorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tour_favorites",
        verbose_name="Пользователь",
    )
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="Тур",
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Избранный тур"
        verbose_name_plural = "Избранные туры"
        constraints = [
            models.UniqueConstraint(fields=["user", "tour"], name="unique_user_tour_favorite")
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.tour.title}"


class Feedback(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedback_requests",
        verbose_name="Пользователь",
    )
    tour = models.ForeignKey(
        Tour,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Выбранный тур",
    )
    tour_type = models.CharField(
        "Тип тура",
        max_length=30,
        choices=TOUR_TYPE_CHOICES,
        blank=True,
        default="",
    )
    name = models.CharField("Имя", max_length=100)
    phone = models.CharField("Телефон", max_length=20)
    date = models.DateField("Дата")
    comment = models.TextField("Пожелания", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отклик"
        verbose_name_plural = "Отклики"

    def __str__(self):
        return f"Заявка от {self.name}"


class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
        verbose_name="Пользователь",
    )
    name = models.CharField("Имя", max_length=100)
    city = models.CharField("Город", max_length=100, blank=True)
    rating = models.PositiveSmallIntegerField("Оценка", default=5)
    text = models.TextField("Текст отзыва")
    likes_count = models.PositiveIntegerField("Лайки", default=0)
    is_approved = models.BooleanField("Одобрен", default=False)
    is_pinned = models.BooleanField("Закреплен", default=False)
    pinned_at = models.DateTimeField("Закреплен в", null=True, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-pinned_at", "-created_at"]
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self):
        return f"{self.name} ({self.rating}/5)"


class ReviewComment(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Отзыв",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="review_comments",
        verbose_name="Пользователь",
    )
    name = models.CharField("Имя", max_length=100)
    text = models.TextField("Комментарий")
    is_approved = models.BooleanField("Одобрен", default=False)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Комментарий к отзыву"
        verbose_name_plural = "Комментарии к отзывам"

    def __str__(self):
        return f"{self.name}: {self.text[:40]}"


class HomePageSettings(models.Model):
    hero_title = models.CharField(
        "Заголовок на главном экране", max_length=200, default="Открой сердце гор"
    )
    hero_subtitle = models.TextField(
        "Подзаголовок",
        default="Индивидуальные и групповые путешествия по самым живописным уголкам Дагестана.",
    )
    hero_image = models.ImageField("Фоновое фото (Hero)", upload_to="hero/", null=True, blank=True)

    class Meta:
        verbose_name = "Настройки Главной страницы"
        verbose_name_plural = "Настройки Главной страницы"

    def __str__(self):
        return "Настройки Главной страницы"


class WelcomeBlock(models.Model):
    TYPES = (
        ("video", "Видео"),
        ("photo", "Фото"),
    )
    title = models.CharField("Заголовок (напр. 14 коренных)", max_length=100, blank=True)
    subtitle = models.CharField("Подзаголовок (напр. народов)", max_length=200, blank=True)
    file = models.FileField("Файл (Медиа)", upload_to="welcome/")
    media_type = models.CharField("Тип контента", max_length=10, choices=TYPES, default="photo")
    is_large = models.BooleanField("Большая карточка (на 2 строки)", default=False)
    order = models.PositiveIntegerField("Порядок отображения", default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "Блок приветствия"
        verbose_name_plural = "Блоки приветствия"

    def __str__(self):
        return f"{self.title or 'Медиа-блок'} ({self.get_media_type_display()})"
