from django.contrib import admin
from .models import Tour, TourPhoto, Feedback, HomePageSettings

class TourPhotoInline(admin.TabularInline):
    model = TourPhoto
    extra = 3

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    inlines = [TourPhotoInline]
    list_display = ('title', 'price')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    # Какие колонки показывать в списке
    list_display = ('name', 'phone', 'tour', 'date', 'created_at')
    # По каким полям можно фильтровать (справа появится панель)
    list_filter = ('tour', 'date', 'created_at')
    # По каким полям работает поиск
    search_fields = ('name', 'phone', 'comment')
    # Сортировка: сначала новые
    ordering = ('-created_at',)
    # Запрещаем редактировать заявки (их можно только смотреть или удалять)
    readonly_fields = ('name', 'phone', 'tour', 'date', 'comment', 'created_at')

@admin.register(HomePageSettings)
class HomePageSettingsAdmin(admin.ModelAdmin):
    # Запрещаем создавать больше одной записи настроек
    def has_add_permission(self, request):
        if HomePageSettings.objects.exists():
            return False
        return True