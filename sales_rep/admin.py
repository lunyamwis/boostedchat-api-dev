# Register your models here.
from django.contrib import admin
from django import forms
from .models import SalesRep, Influencer
from django.contrib.auth.forms import ReadOnlyPasswordHashField

class SalesRepChangeForm(forms.ModelForm):
    ig_password = ReadOnlyPasswordHashField(
        label="Password",
        help_text=(
            "Raw passwords are not stored, so there is no way to see this "
        ),
    )
    class Meta:
        model = SalesRep
        fields = '__all__'
@admin.register(SalesRep)
class SalesRepAdmin(admin.ModelAdmin):
    form = SalesRepChangeForm
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(SalesRepAdmin, self).get_form(request, obj, **kwargs)
        return form




@admin.register(Influencer)
class InfluencerAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(InfluencerAdmin, self).get_form(request, obj, **kwargs)
        return form
