from django.db import models

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
    description = models.TextField("Описание")
    price = models.IntegerField("Цена (руб.)")
    is_group_tour = models.BooleanField("Групповой тур?", default=False)
    main_image = models.ImageField("Главное фото", upload_to='tours/')
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='tours',
        verbose_name="Категория"
    )

    def __str__(self):
        return self.title

class TourPhoto(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField("Доп. фото", upload_to='tours/gallery/')

class Feedback(models.Model):
    tour = models.ForeignKey(
        Tour, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Выбранный тур"
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

class HomePageSettings(models.Model):
    hero_title = models.CharField("Заголовок на главном экране", max_length=200, default="Открой сердце гор")
    hero_subtitle = models.TextField("Подзаголовок", default="Индивидуальные и групповые путешествия по самым живописным уголкам Дагестана.")
    hero_image = models.ImageField("Фоновое фото (Hero)", upload_to='hero/', null=True, blank=True)

    class Meta:
        verbose_name = "Настройки Главной страницы"
        verbose_name_plural = "Настройки Главной страницы"

    def __str__(self):
        return "Настройки Главной страницы"

class WelcomeBlock(models.Model):
    TYPES = (
        ('video', 'Видео'),
        ('photo', 'Фото'),
    )
    title = models.CharField("Заголовок (напр. 14 коренных)", max_length=100, blank=True)
    subtitle = models.CharField("Подзаголовок (напр. народов)", max_length=200, blank=True)
    file = models.FileField("Файл (Медиа)", upload_to='welcome/')
    media_type = models.CharField("Тип контента", max_length=10, choices=TYPES, default='photo')
    is_large = models.BooleanField("Большая карточка (на 2 строки)", default=False)
    order = models.PositiveIntegerField("Порядок отображения", default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Блок приветствия"
        verbose_name_plural = "Блоки приветствия"

    def __str__(self):
        return f"{self.title or 'Медиа-блок'} ({self.get_media_type_display()})"