
from django import template
from microblogging.models import Tweet

register = template.Library()

@register.inclusion_tag('microblogging/listing.html', takes_context=True)
def tweet_listing(context, tweets, prefix_sender, are_mine):
    request = context.get('request', None)
    sc = {
        'tweets': tweets.select_related(depth=1),
        'prefix_sender': prefix_sender,
        'are_mine': are_mine
    }
    if request is not None:
        sc['request'] = request
    return sc

@register.inclusion_tag('microblogging/listing.html', takes_context=True)
def sent_tweet_listing(context, user, prefix_sender, are_mine):
    tweets = Tweet.objects.filter(sender_id=user.pk)
    return tweet_listing(context, tweets, prefix_sender, are_mine)
