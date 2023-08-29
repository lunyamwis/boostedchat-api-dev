from django.contrib import admin

from .models import AutomationSheet


@admin.register(AutomationSheet)
class AutomationAdmin(admin.ModelAdmin):
    list_display = ("category", "name", "file")

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(AutomationAdmin, self).get_form(request, obj, **kwargs)
        return form
