from django.contrib import admin

from .models import Prompt


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ("prompt", "stage")

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(PromptAdmin, self).get_form(request, obj, **kwargs)
        return form
