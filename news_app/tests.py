from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from .models import CustomUser, Publisher, Article, Newsletter


class NewsSystemTests(TestCase):

    def setUp(self):
        self.client = Client()

        # Create Publishers
        self.pub_a = Publisher.objects.create(name="Global Times")
        self.pub_b = Publisher.objects.create(name="Tech Daily")

        # Create Users
        self.editor = CustomUser.objects.create_user(
            username='editor_user', password='password123',
            role='editor', publisher=self.pub_a
        )
        self.journalist = CustomUser.objects.create_user(
            username='writer_user', password='password123',
            role='journalist', publisher=self.pub_a
        )
        self.reader = CustomUser.objects.create_user(
            username='reader_user', password='password123', role='reader'
        )

        # Create Content
        self.article = Article.objects.create(
            title="Approved Article", content="Content",
            author=self.journalist, publisher=self.pub_a, is_approved=True
        )
        self.newsletter = Newsletter.objects.create(
            title="Approved Newsletter", content="Newsletter Content",
            author=self.journalist, publisher=self.pub_a, is_approved=True
        )
        self.pending_nl = Newsletter.objects.create(
            title="Pending Newsletter", content="Secret content",
            author=self.journalist, publisher=self.pub_a, is_approved=False
        )

    # --- 1. Dashboard & Deletion Tests ---
    def test_editor_can_delete_newsletter(self):
        """Test that the delete button/URL works for editors"""
        self.client.login(username='editor_user', password='password123')
        response = self.client.post(reverse(
            'newsletter_delete', args=[self.newsletter.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Newsletter.objects.filter(
            id=self.newsletter.id).exists())

    # --- 2. Form Filtering Tests ---
    def test_journalist_publisher_filtering(self):
        """Test that journalist only sees their own publisher
        in the creation form"""
        self.client.login(username='writer_user', password='password123')
        response = self.client.get(reverse('newsletter_create'))

        # Check if the restricted queryset is in the form
        form = response.context['form']
        queryset = form.fields['publisher'].queryset

        self.assertIn(self.pub_a, queryset)
        self.assertNotIn(self.pub_b, queryset)

    # --- 3. Landing Page & Feed Tests ---
    def test_landing_page_shows_approved_content(self):
        """Test that public landing page shows approved newsletters
        but hides pending ones"""
        response = self.client.get(reverse('publisher_landing'))

        self.assertContains(response, "Approved Newsletter")
        self.assertNotContains(response, "Pending Newsletter")

    def test_reader_subscription_feed(self):
        """Test that subscribed content appears in 'For You' section"""
        # Reader subscribes to Publisher A
        self.reader.pub_subscriptions.add(self.pub_a)
        self.client.login(username='reader_user', password='password123')

        response = self.client.get(reverse('publisher_landing'))

        # Check if the 'For You' variable exists in context
        self.assertTrue('my_feed' in response.context)
        # Check if the newsletter is in that feed
        feed_titles = [item.title for item in response.context['my_feed']]
        self.assertIn("Approved Newsletter", feed_titles)

    # --- 4. Model Property Tests ---
    def test_model_properties(self):
        """Test the is_newsletter property used for template logic"""
        self.assertFalse(self.article.is_newsletter)
        self.assertTrue(self.newsletter.is_newsletter)

    # --- 5. Permission & Security Tests ---
    def test_reader_cannot_access_editor_dashboard(self):
        """
        Security Test: Ensure a user with 'reader' role is blocked
        from the Editor Dashboard.
        """
        # 1. Log in as the reader
        self.client.login(username='reader_user', password='password123')

        # 2. Try to access the editor dashboard URL
        response = self.client.get(reverse('editor_dashboard'))

        # 3. Assert they are blocked.
        # Depending on view logic, this will be 403 (Forbidden)
        # or 302 (Redirect to a 'Access Denied' or 'Login' page)
        self.assertIn(response.status_code, [403, 302])

    def test_unauthenticated_user_cannot_access_editor_dashboard(self):
        """
        Security Test: Ensure a guest (logged out) cannot access the dashboard.
        """
        # Ensure no one is logged in
        self.client.logout()

        response = self.client.get(reverse('editor_dashboard'))

        # Anonymous users should always be redirected to login (302)
        self.assertEqual(response.status_code, 302)


class ArticleAPITests(APITestCase):
    def setUp(self):
        # 1. Setup Publishers
        self.pub_tech = Publisher.objects.create(name="Tech Times")
        self.pub_sports = Publisher.objects.create(name="Sports Weekly")

        # 2. Setup Users
        self.reader = CustomUser.objects.create_user(
            username='api_reader', password='password123', role='reader'
        )
        self.journalist = CustomUser.objects.create_user(
            username='api_journalist', password='password123',
            role='journalist'
        )
        # Create a second journalist the reader DOES NOT follow
        self.other_journalist = CustomUser.objects.create_user(
            username='stranger_news', password='password123',
            role='journalist'
        )

        # 3. Create Content
        # Article 1: User follows the Publisher (Tech Times)
        self.art_subscribed = Article.objects.create(
            title="Followed Pub News",
            content="Important tech news.",
            author=self.other_journalist,
            publisher=self.pub_tech,
            is_approved=True
        )

        # Article 2: User follows the Journalist (api_journalist)
        self.art_journo_subscribed = Article.objects.create(
            title="Followed Journo News",
            content="Inside scoop.",
            author=self.journalist,
            publisher=None,
            is_approved=True
        )

        # Article 3: User follows NEITHER the Publisher nor the Author
        self.art_unsubscribed = Article.objects.create(
            title="Unfollowed News",
            content="This should remain hidden.",
            author=self.other_journalist,  # Reader doesn't follow them
            publisher=self.pub_sports,     # Reader doesn't follow this
            is_approved=True
        )

        # 4. Set Subscriptions
        self.reader.pub_subscriptions.add(self.pub_tech)
        self.reader.journo_subscriptions.add(self.journalist)

    def test_api_returns_correct_subscribed_content(self):
        """
        Verify the REST API filters articles based on the
        authenticated user's subscriptions.
        """
        self.client.login(username='api_reader', password='password123')

        url = reverse('api_subscribed_articles')
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)

        # It should be 2
        self.assertEqual(len(response.data), 2)

        # Verify the content names match
        titles = [item['title'] for item in response.data]
        self.assertIn("Followed Pub News", titles)
        self.assertIn("Followed Journo News", titles)
        self.assertNotIn("Unfollowed News", titles)

    def test_api_unauthorized_access(self):
        """
        Verify that unauthenticated requests are blocked.
        """
        self.client.logout()
        url = reverse('api_subscribed_articles')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
