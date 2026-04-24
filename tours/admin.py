from django.contrib import admin
from .models import Tour, TourPhoto, Feedback, HomePageSettings, WelcomeBlock, Category, Review

class TourPhotoInline(admin.TabularInline):
    model = TourPhoto
    extra = 3

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    inlines = [TourPhotoInline]
    list_display = ('title', 'category', 'price', 'is_group_tour')
    list_editable = ('is_group_tour',)
    list_filter = ('category', 'is_group_tour')
    actions = ['duplicate_tours']

    @admin.display(description="Дублировать выбранные туры")
    def duplicate_tours(self, request, queryset):
        for obj in queryset:
            # Сохраняем ID оригинального объекта, чтобы скопировать связанные фото
            original_id = obj.pk
            
            # 1. Клонируем основной объект тура
            obj.pk = None  # Сбрасываем ID, чтобы Django создал новую запись
            obj.title = f"{obj.title} (копия)"
            obj.save()
            
            # 2. Клонируем связанные фотографии (если они есть)
            original_photos = TourPhoto.objects.filter(tour_id=original_id)
            for photo in original_photos:
                TourPhoto.objects.create(
                    tour=obj,
                    image=photo.image
                )
        
        self.message_user(request, f"Выбранные туры успешно продублированы вместе с фото.")

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'tour', 'date', 'created_at')
    list_filter = ('tour', 'date', 'created_at')
    search_fields = ('name', 'phone', 'comment')
    ordering = ('-created_at',)
    readonly_fields = ('name', 'phone', 'tour', 'date', 'comment', 'created_at')

@admin.register(HomePageSettings)
class HomePageSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not HomePageSettings.objects.exists()
    
@admin.register(WelcomeBlock)
class WelcomeBlockAdmin(admin.ModelAdmin):
    list_display = ('title', 'media_type', 'is_large', 'order')
    list_editable = ('is_large', 'order')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'rating', 'likes_count', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating', 'created_at')
    search_fields = ('name', 'city', 'text')
    ordering = ('-created_at',)
    readonly_fields = ('likes_count', 'created_at')
    actions = ('approve_reviews', 'hide_reviews')

    @admin.action(description="Одобрить выбранные отзывы")
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"Одобрено отзывов: {updated}.")

    @admin.action(description="Снять с публикации выбранные отзывы")
    def hide_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"Снято с публикации: {updated}.")
