from django import template
from django.template.defaultfilters import stringfilter
from django.core.urlresolvers import reverse
from microblogging.models import Tweet
import re

register = template.Library()
user_ref_re = re.compile("@(\w+)")

def make_user_link(text):
    username = text.group(1)
    return """@<a href="%s">%s</a>""" % (reverse("profile_detail", args=[username]), username)

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

@register.filter
@stringfilter
def fmt_user(value):
    return user_ref_re.sub(make_user_link, value)
