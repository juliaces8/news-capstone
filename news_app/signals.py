import tweepy
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Article, Newsletter


@receiver(post_save, sender=Article)
@receiver(post_save, sender=Newsletter)
def notify_subscribers_and_post_to_x(sender, instance, created, **kwargs):
    # Only trigger if the content is approved
    if instance.is_approved:

        # 1. IDENTIFY THE TYPE
        content_type = "Newsletter" if instance.is_newsletter else "Article"

        # 2. GATHER RECIPIENTS
        # (Readers following the Journalist OR the Publisher)
        # journalist followers
        subscribers = instance.author.follower_subs.all()

        # publisher subscribers
        if instance.publisher:
            pub_subs = instance.publisher.reader_subs.all()
            subscribers = (subscribers | pub_subs).distinct()

        recipient_list = list(subscribers.values_list('email', flat=True))
        recipient_list = [email for email in recipient_list if email]

        # 3. SEND EMAILS
        if recipient_list:
            send_mail(
                subject=f"New {content_type}: {instance.title}",
                message=f"Read the latest {content_type} from {
                    instance.author.username}: \n\n{
                        instance.content[:200]}...",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=recipient_list,
                fail_silently=True,
            )

        # 4. POST TO X
        try:
            client = tweepy.Client(
                consumer_key=settings.X_API_KEY,
                consumer_secret=settings.X_API_SECRET,
                access_token=settings.X_ACCESS_TOKEN,
                access_token_secret=settings.X_ACCESS_TOKEN_SECRET
            )

            tweet_text = f"📢 New {content_type}: {instance.title} by {
                instance.author.username} #NewsApp"
            client.create_tweet(text=tweet_text)

        except Exception as e:
            # Defensive coding: print the error but
            # don't crash the save process
            print(f"X Post Failed: {e}")
