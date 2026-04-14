from django.db import models

class Tour(models.Model):
    title = models.CharField("Название тура", max_length=200)
    description = models.TextField("Описание")
    price = models.IntegerField("Цена (руб.)")
    main_image = models.ImageField("Главное фото", upload_to='tours/')

    def __str__(self):
        return self.title

class TourPhoto(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField("Доп. фото", upload_to='tours/gallery/')

class Feedback(models.Model):
    # ВОТ ЭТОЙ СТРОЧКИ НЕ ХВАТАЛО:
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

    # Добавим это для красоты в админке
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