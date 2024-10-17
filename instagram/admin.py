# Register your models here.
import json
from django.contrib import admin

from .models import Account, Message, OutSourced, Photo, StatusCheck, Thread, Video,OutreachTime,AccountsClosed

admin.site.register(Photo)
admin.site.register(Video)

from django.http import HttpResponseRedirect
from django.urls import reverse
from .utils import get_the_cut_info  # Import your function

@admin.action(description='Get The Cut Info')
def get_cut_info_action(modeladmin, request, queryset):
    for obj in queryset:
        # Call your function for each selected object
        outsourced = obj.outsourced_set.get(account__id=obj.id)
        print(outsourced.results.get("external_url"))
        the_cut_username = outsourced.results.get("external_url").split('/')[-1]
        print(the_cut_username)
        info = get_the_cut_info(the_cut_username)
        # Do something with the info, for example, update a field
        obj.referral = json.dumps(info)
        obj.save()

    # Redirect to the admin page after the action is done
    return HttpResponseRedirect(reverse('admin:app_list', args=('instagram',)))

@admin.register(OutreachTime)
class OutreachTimeAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(OutreachTimeAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    search_fields = ['igname__icontains',]
    actions = [get_cut_info_action]

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(AccountAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(StatusCheck)
class StatusAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(StatusAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(ThreadAdmin, self).get_form(request, obj, **kwargs)
        return form

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(MessageAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(OutSourced)
class OutSourcedAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(OutSourcedAdmin, self).get_form(request, obj, **kwargs)
        return form



@admin.register(AccountsClosed)
class AccountsClosedAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(AccountsClosedAdmin, self).get_form(request, obj, **kwargs)
        return form