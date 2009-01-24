from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from microblogging.utils import twitter_account_for_user, twitter_verify_credentials
from microblogging.models import Tweet, TweetInstance, Following
from microblogging.forms import TweetForm

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None


def personal(request, form_class=TweetForm,
        template_name="microblogging/personal.html", success_url=None):
    """
    just the tweets the current user is following
    """
    twitter_account = twitter_account_for_user(request.user)

    if request.method == "POST":
        form = form_class(request.user, request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            form.save()
            if request.POST.get("pub2twitter", False):
                twitter_account.PostUpdate(text)
            if success_url is None:
                success_url = reverse('microblogging.views.personal')
            return HttpResponseRedirect(success_url)
        reply = None
    else:
        reply = request.GET.get("reply", None)
        form = form_class()
        if reply:
            form.fields['text'].initial = u"@%s " % reply
    tweets = TweetInstance.objects.tweets_for(request.user).order_by("-sent")
    return render_to_response(template_name, {
        "form": form,
        "reply": reply,
        "tweets": tweets,
        "twitter_authorized": twitter_verify_credentials(twitter_account),
    }, context_instance=RequestContext(request))
personal = login_required(personal)
    
def public(request, template_name="microblogging/public.html"):
    """
    all the tweets
    """
    tweets = Tweet.objects.all().order_by("-sent")

    return render_to_response(template_name, {
        "tweets": tweets,
    }, context_instance=RequestContext(request))

def single(request, id, template_name="microblogging/single.html"):
    """
    A single tweet.
    """
    tweet = get_object_or_404(Tweet, id=id)
    return render_to_response(template_name, {
        "tweet": tweet,
    }, context_instance=RequestContext(request))


def _follow_list(request, other_user, follow_list, template_name):
    # the only difference between followers/following views is template
    # this function captures the similarity
    
    return render_to_response(template_name, {
        "other_user": other_user,
        "follow_list": follow_list,
    }, context_instance=RequestContext(request))

def followers(request, username, template_name="microblogging/followers.html"):
    """
    a list of users following the given user.
    """
    other_user = get_object_or_404(User, username=username)
    users_followers = Following.objects.filter(followed_object_id=other_user.id, followed_content_type=ContentType.objects.get_for_model(other_user))
    follow_list = [u.follower_content_object for u in users_followers]
    return _follow_list(request, other_user, follow_list, template_name)

def following(request, username, template_name="microblogging/following.html"):
    """
    a list of users the given user is following.
    """
    other_user = get_object_or_404(User, username=username)
    following = Following.objects.filter(follower_object_id=other_user.id, follower_content_type=ContentType.objects.get_for_model(other_user))
    follow_list = [u.followed_content_object for u in following]
    return _follow_list(request, other_user, follow_list, template_name)

def toggle_follow(request, username):
    """
    Either follow or unfollow a user.
    """
    other_user = get_object_or_404(User, username=username)
    if request.user == other_user:
        is_me = True
    else:
        is_me = False
    if request.user.is_authenticated() and request.method == "POST" and not is_me:
        if request.POST["action"] == "follow":
            Following.objects.follow(request.user, other_user)
            request.user.message_set.create(message=_("You are now following %(other_user)s") % {'other_user': other_user})
            if notification:
                notification.send([other_user], "tweet_follow", {"user": request.user})
        elif request.POST["action"] == "unfollow":
            Following.objects.unfollow(request.user, other_user)
            request.user.message_set.create(message=_("You have stopped following %(other_user)s") % {'other_user': other_user})
    return HttpResponseRedirect(reverse("profile_detail", args=[other_user]))
