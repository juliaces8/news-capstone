from django.contrib.auth.models import AbstractUser
from django.db import models

"""Database models for News articles and Custom Users."""


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('reader', 'Reader'),
        ('editor', 'Editor'),
        ('journalist', 'Journalist'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # This is the PRIMARY link for Editors and Journalists to their workplace
    publisher = models.ForeignKey(
        'Publisher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff'
    )

    # 1. READERS following PUBLISHERS
    pub_subscriptions = models.ManyToManyField(
        'Publisher',
        blank=True,
        related_name='reader_subs'
    )

    # 2. READERS following JOURNALISTS (Self-referential)
    # This allows a User (Reader) to follow another User (Journalist)
    journo_subscriptions = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='follower_subs'
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Publisher(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='articles')
    publisher = models.ForeignKey(
        Publisher, on_delete=models.SET_NULL, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_newsletter(self):
        return False


class Newsletter(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='newsletters')
    # If publisher is null, it's an "independent" publication
    publisher = models.ForeignKey(
        Publisher, on_delete=models.SET_NULL, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_newsletter(self):
        return True
