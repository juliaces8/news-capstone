from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Article, Publisher, Newsletter

# 1. Setup an Inline to see Users on the Publisher page


class UserInline(admin.TabularInline):
    model = CustomUser
    fields = ['username', 'role', 'is_active']
    extra = 0
    # This allows to view who works for a publisher without leaving the page
    verbose_name = "Staff Member"
    verbose_name_plural = "Staff Members (Editors/Journalists)"

# 2. Setup Custom User Admin


class CustomUserAdmin(UserAdmin):
    # Added 'publisher' to the fieldsets
    fieldsets = UserAdmin.fieldsets + (
        ('News Roles & Workplace', {'fields': ('role', 'publisher')}),
        ('Subscriptions (Readers Only)', {'fields': (
            'pub_subscriptions', 'journo_subscriptions')}),
    )
    list_display = ['username', 'email', 'role', 'publisher', 'is_staff']
    list_filter = ['role', 'publisher', 'is_staff']

# 3. Setup Article Admin


class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'publisher',
                    'is_approved', 'created_at']
    list_filter = ['is_approved', 'publisher']
    list_editable = ['is_approved']
    search_fields = ['title', 'content']

# 4. Setup Publisher Admin


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = [UserInline]

# 5. Setup Newsletter Admin


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['title', 'publisher', 'is_approved', 'created_at']
    list_filter = ['publisher', 'is_approved']

# Final Registration


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Article, ArticleAdmin)
