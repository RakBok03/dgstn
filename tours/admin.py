from django.contrib import admin
from django.utils import timezone

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
    extra = 3


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    inlines = [TourPhotoInline]
    list_display = ("title", "category", "price", "is_group_tour")
    list_editable = ("is_group_tour",)
    list_filter = ("category", "is_group_tour")
    actions = ["duplicate_tours"]

    @admin.display(description="Дублировать выбранные туры")
    def duplicate_tours(self, request, queryset):
        for obj in queryset:
            original_id = obj.pk
            obj.pk = None
            obj.title = f"{obj.title} (копия)"
            obj.save()

            original_photos = TourPhoto.objects.filter(tour_id=original_id)
            for photo in original_photos:
                TourPhoto.objects.create(tour=obj, image=photo.image)

        self.message_user(request, "Выбранные туры успешно продублированы вместе с фото.")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "user", "tour", "date", "created_at")
    list_filter = ("tour", "date", "created_at")
    search_fields = ("name", "phone", "comment", "user__username")
    ordering = ("-created_at",)
    readonly_fields = ("name", "phone", "user", "tour", "date", "comment", "created_at")


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
