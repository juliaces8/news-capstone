from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # This "includes" all the URLs from the app
    path('', include('news_app.urls')),
]
