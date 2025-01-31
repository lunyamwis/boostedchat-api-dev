# Register your models here.
import json
from django.contrib import admin

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Account, Message, OutSourced, Photo, StatusCheck, Thread, Video,OutreachTime,AccountsClosed, UnwantedAccount, Comment, Like

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



@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    search_fields = ['igname__icontains',]
    actions = [get_cut_info_action]

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(AccountAdmin, self).get_form(request, obj, **kwargs)
        return form
    
class RecentAccountsFilter(admin.SimpleListFilter):
    title = _('Recent Accounts')  # Displayed in the admin sidebar
    parameter_name = 'recent_accounts'  # URL parameter for the filter

    def lookups(self, request, model_admin):
        # Define the filter options
        return (
            ('recent', _('Added from yesterday')),
        )

    def queryset(self, request, queryset):
        # Apply the filter logic
        if self.value() == 'recent':
            yesterday = timezone.now() - timezone.timedelta(days=1)
            return queryset.filter(outreach_time__gte=yesterday)
        return queryset


class UnqualifiedAccountsFilter(admin.SimpleListFilter):
    title = _('Unqualified Accounts')  # Displayed in the admin sidebar
    parameter_name = 'unqualified_accounts'  # URL parameter for the filter

    def lookups(self, request, model_admin):
        # Define the filter options
        return (
            ('unqualified', _('Unqualified Accounts')),
        )

    def queryset(self, request, queryset):
        # Apply the filter logic
        if self.value() == 'unqualified':
            return queryset.filter(qualified=False)
        return queryset

@admin.register(OutreachTime)
class OutreachTimeAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(OutreachTimeAdmin, self).get_form(request, obj, **kwargs)
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
    search_fields = ['account__igname__icontains',]
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



@admin.register(UnwantedAccount)
class UnwantedAccountAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(UnwantedAccountAdmin, self).get_form(request, obj, **kwargs)
        return form
    

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(CommentAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(LikeAdmin, self).get_form(request, obj, **kwargs)
        return form
