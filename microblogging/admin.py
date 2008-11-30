from django.contrib import admin
from microblogging.models import Tweet, TweetInstance, Following

class TweetAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender_type', 'sender_id', 'text',)

class TweetInstanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender_type', 'sender_id', 'text', 'recipient_type', 'recipient_id')

class FollowingAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower_content_type', 'follower_object_id', 'followed_content_type', 'followed_object_id')


admin.site.register(Tweet, TweetAdmin)
admin.site.register(TweetInstance, TweetInstanceAdmin)
admin.site.register(Following, FollowingAdmin)