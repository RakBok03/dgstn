from django.conf import settings
from django.db import models
from django.utils.text import slugify


RUSSIAN_TRANSLIT = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def make_ascii_slug(value):
    transliterated = "".join(RUSSIAN_TRANSLIT.get(char.lower(), char.lower()) for char in value)
    return slugify(transliterated)


TOUR_TYPE_CHOICES = (
    ("jeep", "Джип-тур"),
    ("wellness", "Оздоровительный"),
    ("one_day", "Однодневный"),
    ("multi_day", "Многодневный"),
    ("active", "Активный отдых"),
    ("combined", "Комбинированный"),
    ("unknown", "Пока не знаю, нужна консультация"),
)


class Category(models.Model):
    name = models.CharField("Название категории", max_length=100)
    slug = models.SlugField("Слаг (для URL)", unique=True)
    description = models.CharField("Короткое описание", max_length=220, blank=True, default="")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Tour(models.Model):
    title = models.CharField("Название тура", max_length=200)
    slug = models.SlugField("Слаг (для URL)", max_length=220, unique=True, blank=True)
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
    not_included_items = models.TextField(
        "Что не входит",
        blank=True,
        default="",
        help_text="Каждый пункт с новой строки.",
    )
    route_points = models.TextField(
        "Ключевые точки маршрута",
        blank=True,
        default="",
        help_text="Каждая точка с новой строки: Сарыкум, Нохъо, Чиркейская ГЭС.",
    )
    itinerary = models.TextField(
        "Программа",
        blank=True,
        default="",
        help_text="Короткий план по дням или по времени. Можно писать свободным текстом.",
    )
    start_location = models.CharField("Старт", max_length=140, blank=True, default="")
    group_size = models.CharField("Размер группы", max_length=120, blank=True, default="")
    difficulty = models.CharField("Сложность", max_length=120, blank=True, default="")
    season = models.CharField("Сезон", max_length=120, blank=True, default="")
    what_to_take = models.TextField(
        "Что взять с собой",
        blank=True,
        default="",
        help_text="Каждый пункт с новой строки.",
    )
    important_notes = models.TextField("Важные примечания", blank=True, default="")
    price = models.IntegerField("Цена (руб.)")
    is_group_tour = models.BooleanField("Групповой тур?", default=False)
    main_image = models.ImageField("Главное фото", upload_to="tours/", blank=True)
    static_image = models.CharField(
        "Статичное фото",
        max_length=220,
        blank=True,
        default="",
        help_text="Путь внутри static/images, например site/sulak-canyon.jpg. Используется, если не загружено главное фото.",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tours",
        verbose_name="Категория",
    )
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name="multi_category_tours",
        verbose_name="Дополнительные категории",
    )
    is_published = models.BooleanField("Опубликован", default=True)
    is_featured = models.BooleanField("Показывать на главной", default=False)
    created_at = models.DateTimeField("Создан", auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = make_ascii_slug(self.title) or "tour"
            candidate = base_slug
            counter = 2
            while Tour.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def _split_lines(self, value):
        return [
            item.strip(" -•")
            for item in value.splitlines()
            if item.strip(" -•")
        ]

    @property
    def primary_category(self):
        if self.category:
            return self.category
        return self.categories.first()

    @property
    def category_list(self):
        categories = []
        if self.category:
            categories.append(self.category)
        categories.extend(list(self.categories.exclude(id=getattr(self.category, "id", None))))
        return categories

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
    def group_size_label(self):
        return self.group_size or ("Групповой формат" if self.is_group_tour else "Индивидуально или мини-группа")

    @property
    def start_label(self):
        return self.start_location or "Махачкала или по договоренности"

    @property
    def difficulty_label(self):
        return self.difficulty or "Комфортный темп"

    @property
    def season_label(self):
        return self.season or "По сезону и погоде"

    @property
    def route_points_list(self):
        return self._split_lines(self.route_points)

    @property
    def not_included_list(self):
        return self._split_lines(self.not_included_items)

    @property
    def what_to_take_list(self):
        return self._split_lines(self.what_to_take)

    @property
    def included_list(self):
        items = self._split_lines(self.included_items)
        if items:
            return items[:5]

        defaults = [
            "Сопровождение гида",
            "Безопасный маршрут",
            "Помощь с размещением",
            "Консультация по маршруту",
        ]
        primary_category = self.primary_category
        if primary_category and primary_category.slug == "wellness":
            defaults.append("Учет самочувствия и противопоказаний")
        else:
            defaults.append("Лучшие локации по сезону")
        return defaults

    @property
    def detail_included_list(self):
        items = self._split_lines(self.included_items)
        return items or self.included_list

    @property
    def card_static_image(self):
        if self.static_image:
            return self.static_image

        primary_category = self.primary_category
        slug = primary_category.slug if primary_category else ""
        defaults = {
            "jeep-tours": "site/jeep-route.jpg",
            "wellness": "site/guide-canyon.jpg",
            "one-day": "site/sulak-canyon.jpg",
            "multi-day": "site/hero-boat-canyon.jpg",
            "active": "site/goor-cliff.jpg",
            "combined": "site/boat-guests.jpg",
        }
        return defaults.get(slug, "site/hero-boat-canyon.jpg")


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
