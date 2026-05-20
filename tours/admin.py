from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Category,
    Feedback,
    HomePageSettings,
    Review,
    ReviewComment,
    Tour,
    TourFavorite,
    TourPhoto,
    UserProfile,
    WelcomeBlock,
)


class TourPhotoInline(admin.TabularInline):
    model = TourPhoto
    extra = 1
    readonly_fields = ("preview",)

    @admin.display(description="Превью")
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 96px; height: 72px; object-fit: cover; border-radius: 8px;" />',
                obj.image.url,
            )
        return "Нет фото"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "description")
    list_editable = ("order",)
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    inlines = [TourPhotoInline]
    list_display = (
        "image_preview",
        "title",
        "category",
        "category_badges",
        "duration",
        "price",
        "is_published",
        "is_featured",
    )
    list_editable = ("is_published", "is_featured")
    list_filter = ("is_published", "is_featured", "category", "categories", "is_group_tour")
    search_fields = (
        "title",
        "short_description",
        "description",
        "route_points",
        "included_items",
    )
    filter_horizontal = ("categories",)
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("image_preview_large", "created_at", "updated_at")
    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "title",
                    "slug",
                    "is_published",
                    "is_featured",
                    "category",
                    "categories",
                    "main_image",
                    "static_image",
                    "image_preview_large",
                    "price",
                    "is_group_tour",
                )
            },
        ),
        (
            "Карточка",
            {
                "fields": (
                    "short_description",
                    "duration",
                    "trip_format",
                    "group_size",
                    "start_location",
                    "difficulty",
                    "season",
                )
            },
        ),
        (
            "Маршрут и продажи",
            {
                "fields": (
                    "description",
                    "route_points",
                    "itinerary",
                    "included_items",
                    "not_included_items",
                    "what_to_take",
                    "important_notes",
                )
            },
        ),
        ("Служебное", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    actions = ["duplicate_tours", "publish_tours", "hide_tours", "mark_featured", "unmark_featured"]

    @admin.display(description="Фото")
    def image_preview(self, obj):
        if obj.main_image:
            return format_html(
                '<img src="{}" style="width: 72px; height: 52px; object-fit: cover; border-radius: 8px;" />',
                obj.main_image.url,
            )
        if obj.static_image:
            return format_html(
                '<span style="display:inline-block; width:72px; padding:6px; border-radius:8px; background:#eef2f7; font-size:11px;">static</span>'
            )
        return "Нет"

    @admin.display(description="Превью фото")
    def image_preview_large(self, obj):
        if obj and obj.main_image:
            return format_html(
                '<img src="{}" style="max-width: 360px; max-height: 220px; object-fit: cover; border-radius: 12px;" />',
                obj.main_image.url,
            )
        if obj and obj.static_image:
            return format_html(
                '<div style="padding:12px; border:1px solid #dbe3ea; border-radius:12px;">Static image: <strong>{}</strong></div>',
                obj.static_image,
            )
        return "Загрузите фото или укажите static_image."

    @admin.display(description="Категории")
    def category_badges(self, obj):
        names = [category.name for category in obj.category_list]
        return ", ".join(names) if names else "Не указаны"

    @admin.display(description="Дублировать выбранные туры")
    def duplicate_tours(self, request, queryset):
        for obj in queryset:
            original_id = obj.pk
            original_categories = list(obj.categories.all())
            obj.pk = None
            obj.title = f"{obj.title} (копия)"
            obj.slug = ""
            obj.save()
            obj.categories.set(original_categories)

            original_photos = TourPhoto.objects.filter(tour_id=original_id)
            for photo in original_photos:
                TourPhoto.objects.create(tour=obj, image=photo.image)

        self.message_user(request, "Выбранные туры успешно продублированы вместе с фото.")

    @admin.action(description="Опубликовать выбранные туры")
    def publish_tours(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f"Опубликовано туров: {updated}.")

    @admin.action(description="Снять выбранные туры с публикации")
    def hide_tours(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f"Снято с публикации: {updated}.")

    @admin.action(description="Показывать выбранные туры на главной")
    def mark_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"Добавлено на главную: {updated}.")

    @admin.action(description="Убрать выбранные туры с главной")
    def unmark_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"Убрано с главной: {updated}.")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "user", "tour", "tour_type", "date", "created_at")
    list_filter = ("tour", "tour_type", "date", "created_at")
    search_fields = ("name", "phone", "comment", "user__username")
    ordering = ("-created_at",)
    readonly_fields = (
        "name",
        "phone",
        "user",
        "tour",
        "tour_type",
        "date",
        "comment",
        "created_at",
    )


@admin.register(HomePageSettings)
class HomePageSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not HomePageSettings.objects.exists()


@admin.register(WelcomeBlock)
class WelcomeBlockAdmin(admin.ModelAdmin):
    list_display = ("title", "media_type", "is_large", "order")
    list_editable = ("is_large", "order")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "city",
        "rating",
        "likes_count",
        "is_pinned",
        "is_approved",
        "created_at",
    )
    list_filter = ("is_approved", "is_pinned", "rating", "created_at")
    search_fields = ("name", "city", "text", "user__username")
    ordering = ("-is_pinned", "-pinned_at", "-created_at")
    readonly_fields = ("likes_count", "created_at", "pinned_at")
    actions = ("approve_reviews", "hide_reviews", "pin_reviews", "unpin_reviews")

    @admin.action(description="Одобрить выбранные отзывы")
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"Одобрено отзывов: {updated}.")

    @admin.action(description="Снять с публикации выбранные отзывы")
    def hide_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"Снято с публикации: {updated}.")

    @admin.action(description="Закрепить выбранные отзывы")
    def pin_reviews(self, request, queryset):
        now = timezone.now()
        updated = queryset.update(is_pinned=True, pinned_at=now)
        self.message_user(request, f"Закреплено отзывов: {updated}.")

    @admin.action(description="Открепить выбранные отзывы")
    def unpin_reviews(self, request, queryset):
        updated = queryset.update(is_pinned=False, pinned_at=None)
        self.message_user(request, f"Откреплено отзывов: {updated}.")

    def save_model(self, request, obj, form, change):
        if obj.is_pinned and not obj.pinned_at:
            obj.pinned_at = timezone.now()
        if not obj.is_pinned:
            obj.pinned_at = None
        super().save_model(request, obj, form, change)


@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    list_display = ("review", "name", "user", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("name", "text", "review__name", "user__username")
    ordering = ("-created_at",)
    actions = ("approve_comments", "hide_comments")

    @admin.action(description="Одобрить выбранные комментарии")
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"Одобрено комментариев: {updated}.")

    @admin.action(description="Снять с публикации выбранные комментарии")
    def hide_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"Снято с публикации: {updated}.")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")
    search_fields = ("user__username", "user__email", "phone")


@admin.register(TourFavorite)
class TourFavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "tour", "created_at")
    search_fields = ("user__username", "tour__title")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
