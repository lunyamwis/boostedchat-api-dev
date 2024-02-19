from django.contrib import admin

from .models import AutomationSheet, Industry


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ("name",)

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(IndustryAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(AutomationSheet)
class AutomationAdmin(admin.ModelAdmin):
    list_display = ("industry", "name", "file")

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(AutomationAdmin, self).get_form(request, obj, **kwargs)
        return form
