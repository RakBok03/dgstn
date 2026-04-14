from django.contrib import admin
from .models import Tour, TourPhoto, Feedback, HomePageSettings, WelcomeBlock, Category

class TourPhotoInline(admin.TabularInline):
    model = TourPhoto
    extra = 3

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    inlines = [TourPhotoInline]
    list_display = ('title', 'category', 'price')
    list_filter = ('category',)

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