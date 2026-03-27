from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Article, Newsletter, CustomUser, Publisher
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .serializers import ArticleSerializer
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q

# Helper function to check if the user is an Editor


def is_editor(user):
    return user.role == 'editor'

# --- EDITOR DASHBOARD ---


class EditorDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Article
    template_name = 'news_app/editor_dashboard.html'

    def test_func(self):
        # Allow access if user is an Editor OR a Superuser
        user = self.request.user
        return user.role == 'editor' or user.is_superuser

    def get_queryset(self):
        user = self.request.user
        # 1. Admins see EVERYTHING
        if user.is_superuser:
            return Article.objects.all().order_by('-created_at')

        # 2. Editors see only their Publisher's articles
        user_pub = getattr(user, 'publisher', None)
        if user_pub:
            return Article.objects.filter(
                publisher=user_pub
            ).order_by('-created_at')

        return Article.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 1. Logic for Superusers (Admins)
        if user.is_superuser:
            context['publisher_name'] = "All Publishers (Admin Mode)"
            context['all_newsletters'] = (
                Newsletter.objects.all().order_by('-created_at')
            )
            # Calculate total pending for the stats card
            p_art = Article.objects.filter(is_approved=False).count()
            p_nl = Newsletter.objects.filter(is_approved=False).count()
            context['total_pending'] = p_art + p_nl

        # 2. Logic for Editors
        else:
            user_pub = getattr(user, 'publisher', None)
            if user_pub:
                context['publisher_name'] = user_pub.name
                context['all_newsletters'] = (
                    Newsletter.objects.filter(publisher=user_pub).order_by(
                        '-created_at'
                    )
                )
                # Calculate total pending for this specific publisher
                p_art = Article.objects.filter(
                    publisher=user_pub, is_approved=False
                ).count()
                p_nl = Newsletter.objects.filter(
                    publisher=user_pub, is_approved=False
                ).count()
                context['total_pending'] = p_art + p_nl
            else:
                context['publisher_name'] = "No Publisher Assigned"
                context['all_newsletters'] = Newsletter.objects.none()
                context['total_pending'] = 0

        return context

# --- APPROVAL LOGIC (With Security Checks) ---


@login_required
def approve_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    # Split conditions across lines to stay under 79 characters
    is_editor = request.user.role == 'editor'
    has_pub = request.user.publisher is not None
    matches = request.user.publisher == article.publisher

    if is_editor and has_pub and matches:
        article.is_approved = True
        article.save()
        messages.success(
            request, f'Article "{article.title}" has been approved!'
        )
    else:
        messages.error(
            request, "Access Denied: You do not have permission."
        )
    return redirect('editor_dashboard')


@login_required
def unapprove_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if (request.user.role == 'editor' and
            request.user.publisher is not None and
            request.user.publisher == article.publisher):
        article.is_approved = False
        article.save()
        messages.warning(
            request, f'Article "{article.title}" has been retracted.'
        )
    else:
        messages.error(request, "Access Denied.")
    return redirect('editor_dashboard')


@login_required
def approve_newsletter(request, newsletter_id):
    nl = get_object_or_404(Newsletter, id=newsletter_id)

    if (request.user.role == 'editor' and
            request.user.publisher is not None and
            request.user.publisher == nl.publisher):
        nl.is_approved = True
        nl.save()
        messages.success(
            request, f'Newsletter "{nl.title}" has been approved!'
        )
    else:
        messages.error(request, "Access Denied.")
    return redirect('editor_dashboard')


@login_required
def unapprove_newsletter(request, newsletter_id):
    nl = get_object_or_404(Newsletter, id=newsletter_id)

    if (request.user.role == 'editor' and
            request.user.publisher is not None and
            request.user.publisher == nl.publisher):
        nl.is_approved = False
        nl.save()
        messages.warning(
            request, f'Newsletter "{nl.title}" has been retracted.'
        )
    else:
        messages.error(request, "Access Denied.")
    return redirect('editor_dashboard')


class ArticleSubscriptionListView(generics.ListAPIView):
    """
    API endpoint that allows readers to retrieve articles from
    publishers and journalists they follow.
    """
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Use Q objects to combine the logic into one clean query.
        # This is more efficient and easier to read.
        return Article.objects.filter(
            Q(publisher__in=user.pub_subscriptions.all()) |
            Q(author__in=user.journo_subscriptions.all()),
            is_approved=True
        ).distinct().order_by('-created_at')

# --- READER LANDING PAGE ---


class PublisherLandingView(ListView):
    model = Article
    template_name = 'news_app/publisher_landing.html'
    context_object_name = 'articles'

    def get_queryset(self):
        # Only show articles where is_approved is True
        # for the "Latest Articles" section
        return Article.objects.filter(is_approved=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 1. Fetch Approved Newsletters for the "Featured Newsletters" section
        context['newsletters'] = Newsletter.objects.filter(
            is_approved=True).order_by('-created_at')

        # 2. Logic for Logged-in Readers
        if user.is_authenticated and user.role == 'reader':
            subscribed_articles = Article.objects.filter(
                Q(publisher__in=user.pub_subscriptions.all()) |
                Q(author__in=user.journo_subscriptions.all()),
                is_approved=True
            )

            subscribed_newsletters = Newsletter.objects.filter(
                publisher__in=user.pub_subscriptions.all(),
                is_approved=True
            )

            # Combine them into one list
            combined_feed = list(subscribed_articles) + list(
                subscribed_newsletters)

            # Sort by created_at (most recent first)
            context['my_feed'] = sorted(
                combined_feed,
                key=lambda x: x.created_at,
                reverse=True
            )

        return context

# --- JOURNALIST CRUD (Independent & Publisher) ---


class JournalistCreateArticle(LoginRequiredMixin, CreateView):
    model = Article
    fields = ['title', 'content', 'publisher']
    template_name = 'news_app/article_form.html'
    success_url = reverse_lazy('journalist_dashboard')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        if not user.is_superuser and user.publisher:
            # Filters the dropdown to ONLY the journalist's publisher
            form.fields['publisher'].queryset = Publisher.objects.filter(
                id=user.publisher.id)
            # Sets it as the default selection
            form.fields['publisher'].initial = user.publisher
        return form

    def form_valid(self, form):
        form.instance.author = self.request.user
        # Safety check: force publisher to user's publisher if they have one
        if self.request.user.publisher:
            form.instance.publisher = self.request.user.publisher
        return super().form_valid(form)


class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Article

    def get_success_url(self):
        # Redirect back to the correct dashboard based on role
        if self.request.user.role == 'editor':
            return reverse_lazy('editor_dashboard')
        return reverse_lazy('journalist_dashboard')

    def test_func(self):
        obj = self.get_object()
        user = self.request.user
        # 1. Admins can delete
        if user.is_superuser:
            return True
        # 2. Editors can delete if it's their publisher
        if user.role == 'editor' and user.publisher == obj.publisher:
            return True
        # 3. Journalists can delete ONLY their own articles
        if user.role == 'journalist' and obj.author == user:
            return True
        return False


class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Article
    fields = ['title', 'content', 'publisher']
    template_name = 'news_app/article_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        # If the user is an Editor (and not a Superuser), lock the dropdown
        if not user.is_superuser and user.publisher:
            # This restricts the list to ONLY their own company
            form.fields['publisher'].queryset = Publisher.objects.filter(
                id=user.publisher.id
            )
        return form

    def get_success_url(self):
        if self.request.user.role == 'editor':
            return reverse_lazy('editor_dashboard')
        return reverse_lazy('journalist_dashboard')

    def test_func(self):
        obj = self.get_object()
        user = self.request.user

        # 1. Editor logic: must have correct role AND matching publisher
        is_editor = user.role == 'editor'
        matches_pub = user.publisher == obj.publisher

        if is_editor and matches_pub:
            return True

        # 2. Journalist logic: can edit their own
        return user == obj.author


class JournalistDashboardView(LoginRequiredMixin,
                              UserPassesTestMixin, ListView):
    model = Article
    template_name = 'news_app/journalist_dashboard.html'
    context_object_name = 'my_articles'

    def test_func(self):
        return self.request.user.role == 'journalist'

    def get_queryset(self):
        # Only show articles belonging to the logged-in journalist
        return Article.objects.filter(author=self.request.user).order_by(
            '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add newsletters to the same page
        context['my_newsletters'] = Newsletter.objects.filter(
            author=self.request.user)
        return context


class NewsletterCreateView(LoginRequiredMixin, CreateView):
    model = Newsletter
    fields = ['title', 'content', 'publisher']
    template_name = 'news_app/article_form.html'
    success_url = reverse_lazy('journalist_dashboard')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        # 1. This filters the dropdown list for the user
        if not user.is_superuser and user.publisher:
            # Show ONLY the user's publisher in the dropdown
            form.fields['publisher'].queryset = Publisher.objects.filter(
                id=user.publisher.id)
            # Set it as the default so they don't have to click
            form.fields['publisher'].initial = user.publisher

        return form

    def form_valid(self, form):
        # 2. This ensures the data is saved correctly in the database
        form.instance.author = self.request.user

        # Force the publisher to be the user's publisher if they have one
        if self.request.user.publisher:
            form.instance.publisher = self.request.user.publisher

        return super().form_valid(form)


class NewsletterUpdateView(LoginRequiredMixin,
                           UserPassesTestMixin, UpdateView):
    model = Newsletter
    fields = ['title', 'content', 'publisher']
    template_name = 'news_app/article_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        # 1. Logic: If not a superuser, lock the publisher dropdown
        if not user.is_superuser and user.publisher:
            # Only show the user's own publisher in the list
            form.fields['publisher'].queryset = Publisher.objects.filter(
                id=user.publisher.id)

        return form

    def get_success_url(self):
        # 2. Logic: Send the user back to their specific dashboard
        if self.request.user.role == 'editor':
            return reverse_lazy('editor_dashboard')
        return reverse_lazy('journalist_dashboard')

    def test_func(self):
        # 3. Security: Who is allowed to edit this newsletter?
        obj = self.get_object()
        user = self.request.user

        if user.is_superuser:
            return True

        # Editors can edit if the newsletter belongs to their publisher
        if user.role == 'editor' and user.publisher == obj.publisher:
            return True

        # Journalists can edit only their own newsletters
        if user.role == 'journalist' and obj.author == user:
            return True

        return False


class NewsletterDeleteView(LoginRequiredMixin,
                           UserPassesTestMixin, DeleteView):
    model = Newsletter

    def get_success_url(self):
        if self.request.user.role == 'editor':
            return reverse_lazy('editor_dashboard')
        return reverse_lazy('journalist_dashboard')

    def test_func(self):
        obj = self.get_object()
        user = self.request.user
        # Allow if Admin, or if Editor of that publisher, or if the Author
        if user.is_superuser:
            return True
        if user.role == 'editor' and user.publisher == obj.publisher:
            return True
        return user == obj.author


@login_required
def toggle_follow(request, target_id, target_type):
    user = request.user

    if target_type == 'publisher':
        target = get_object_or_404(Publisher, id=target_id)
        # Using the field name from CustomUser model
        if target in user.pub_subscriptions.all():
            user.pub_subscriptions.remove(target)
            messages.info(request, f"Unfollowed {target.name}")
        else:
            user.pub_subscriptions.add(target)
            messages.success(request, f"Now following {target.name}!")

    elif target_type == 'journalist':
        target = get_object_or_404(CustomUser, id=target_id)
        # Using the self-referential field name
        if target in user.journo_subscriptions.all():
            user.journo_subscriptions.remove(target)
            messages.info(request, f"Unfollowed {target.username}")
        else:
            user.journo_subscriptions.add(target)
            messages.success(request, f"Now following {target.username}!")

    return redirect(request.META.get('HTTP_REFERER', 'publisher_landing'))
