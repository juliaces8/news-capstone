from rest_framework import serializers
from .models import Article


class ArticleSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.username')
    # Use a SerializerMethodField to handle "Independent" publishers
    publisher_name = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content', 'author_name',
            'publisher_name', 'created_at'
        ]

    def get_publisher_name(self, obj):
        return obj.publisher.name if obj.publisher else "Independent"
