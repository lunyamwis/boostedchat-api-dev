# Register your models here.

from django.contrib import admin

from .models import Account, Message, OutSourced, Photo, StatusCheck, Thread, Video,OutreachTime,AccountsClosed

admin.site.register(Photo)
admin.site.register(Video)

@admin.register(OutreachTime)
class OutreachTimeAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(OutreachTimeAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    search_fields = ['igname__icontains',]

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