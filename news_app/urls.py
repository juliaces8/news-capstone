"""
URL configuration for news_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from news_app import views
from . import views

"""URL routing configuration for the news_app."""

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('editor/approve/<int:article_id>/', views.approve_article,
         name='approve_article'),
    path('api/articles/subscribed/',
         views.ArticleSubscriptionListView.as_view(),
         name='api_subscribed_articles'),
    path('', views.PublisherLandingView.as_view(), name='publisher_landing'),
    path('journalist/create/', views.JournalistCreateArticle.as_view(),
         name='article_create'),
    path('editor/dashboard/', views.EditorDashboardView.as_view(),
         name='editor_dashboard'),
    path('article/<int:pk>/delete/', views.ArticleDeleteView.as_view(),
         name='article_delete'),
    path('article/<int:pk>/edit/', views.ArticleUpdateView.as_view(),
         name='article_edit'),
    path('journalist/dashboard/', views.JournalistDashboardView.as_view(),
         name='journalist_dashboard'),
    path('newsletter/<int:pk>/edit/', views.NewsletterUpdateView.as_view(),
         name='newsletter_edit'),
    path('newsletter/<int:pk>/delete/', views.NewsletterDeleteView.as_view(),
         name='newsletter_delete'),
    path('newsletter/create/', views.NewsletterCreateView.as_view(),
         name='newsletter_create'),
    path('editor/approve-newsletter/<int:newsletter_id>/',
         views.approve_newsletter, name='approve_newsletter'),
    path('article/unapprove/<int:article_id>/', views.unapprove_article,
         name='unapprove_article'),
    path('newsletter/unapprove/<int:newsletter_id>/',
         views.unapprove_newsletter, name='unapprove_newsletter'),
    path('follow/<str:target_type>/<int:target_id>/', views.toggle_follow,
         name='toggle_follow'),
]
