from datetime import datetime

from django.db import models
from django.db.models.signals import post_save
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

try:
    from notification import models as notification
except ImportError:
    notification = None

# relational databases are a terrible way to do
# multicast messages (just ask Twitter) but here you have it :-)

# @@@ need to make @ and # handling more abstract

import re
reply_re = re.compile("^@(\w+)")
    
class Tweet(models.Model):
    """
    a single tweet from a user
    """
    
    text = models.CharField(_('text'), max_length=140)
    sender_type = models.ForeignKey(ContentType)
    sender_id = models.PositiveIntegerField()
    sender = generic.GenericForeignKey('sender_type', 'sender_id')
    sent = models.DateTimeField(_('sent'), default=datetime.now)
    
    def __unicode__(self):
        return self.text
    
    def get_absolute_url(self):
        return ("single_tweet", [self.id])
    get_absolute_url = models.permalink(get_absolute_url)

    class Meta:
        ordering = ('-sent',)


class TweetInstanceManager(models.Manager):
    
    def tweets_for(self, recipient):
        recipient_type = ContentType.objects.get_for_model(recipient)
        return TweetInstance.objects.filter(recipient_type=recipient_type, recipient_id=recipient.id)


class TweetInstance(models.Model):
    """
    the appearance of a tweet in a follower's timeline
    
    denormalized for better performance
    """
    
    text = models.CharField(_('text'), max_length=140)
    sender_type = models.ForeignKey(ContentType, related_name='tweet_instances')
    sender_id = models.PositiveIntegerField()
    sender = generic.GenericForeignKey('sender_type', 'sender_id')
    sent = models.DateTimeField(_('sent'))
    
    # to migrate to generic foreign key, find out the content_type id of User and do something like:
    # ALTER TABLE "microblogging_tweetinstance"
    #     ADD COLUMN "recipient_type_id" integer NOT NULL
    #     REFERENCES "django_content_type" ("id")
    #     DEFAULT <user content type id>;
    #
    # NOTE: you will also need to drop the foreign key constraint if it exists
    
    # recipient = models.ForeignKey(User, related_name="received_tweet_instances", verbose_name=_('recipient'))
    
    recipient_type = models.ForeignKey(ContentType)
    recipient_id = models.PositiveIntegerField()
    recipient = generic.GenericForeignKey('recipient_type', 'recipient_id')
    
    objects = TweetInstanceManager()


def tweet(sender, instance, created, **kwargs):
    #if tweet is None:
    #    tweet = Tweet.objects.create(text=text, sender=user)
    recipients = set() # keep track of who's received it
    user = instance.sender
    
    # add the sender's followers
    user_content_type = ContentType.objects.get_for_model(user)
    followings = Following.objects.filter(followed_content_type=user_content_type, followed_object_id=user.id)
    for follower in (following.follower_content_object for following in followings):
        recipients.add(follower)
    
    # add sender
    recipients.add(user)
    
    # if starts with @user send it to them too even if not following
    match = reply_re.match(instance.text)
    if match:
        try:
            reply_recipient = User.objects.get(username=match.group(1))
            recipients.add(reply_recipient)
        except User.DoesNotExist:
            pass # oh well
        else:
            if notification:
                notification.send([reply_recipient], "tweet_reply_received", {'tweet': instance,})
    
    # now send to all the recipients
    for recipient in recipients:
        tweet_instance = TweetInstance.objects.create(text=instance.text, sender=user, recipient=recipient, sent=instance.sent)


class FollowingManager(models.Manager):
    
    def is_following(self, follower, followed):
        try:
            following = self.get(follower_object_id=follower.id, followed_object_id=followed.id)
            return True
        except Following.DoesNotExist:
            return False
    
    def follow(self, follower, followed):
        if follower != followed and not self.is_following(follower, followed):
            Following(follower_content_object=follower, followed_content_object=followed).save()
    
    def unfollow(self, follower, followed):
        try:
            following = self.get(follower_object_id=follower.id, followed_object_id=followed.id)
            following.delete()
        except Following.DoesNotExist:
            pass


class Following(models.Model):
    follower_content_type = models.ForeignKey(ContentType, related_name="followed", verbose_name=_('follower'))
    follower_object_id = models.PositiveIntegerField()
    follower_content_object = generic.GenericForeignKey('follower_content_type', 'follower_object_id')
    
    followed_content_type = models.ForeignKey(ContentType, related_name="followers", verbose_name=_('followed'))
    followed_object_id = models.PositiveIntegerField()
    followed_content_object = generic.GenericForeignKey('followed_content_type', 'followed_object_id')
    
    objects = FollowingManager()

post_save.connect(tweet, sender=Tweet)