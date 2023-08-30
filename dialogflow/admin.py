from django.contrib import admin

from .models import ScriptStage

# Register your models here.


@admin.register(ScriptStage)
class ScriptStageAdmin(admin.ModelAdmin):
    list_display = ("name",)

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(ScriptStageAdmin, self).get_form(request, obj, **kwargs)
        return form
