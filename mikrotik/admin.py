from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(profile),
admin.site.register(parent),
admin.site.register(configuration),
admin.site.register(influx),
admin.site.register(toogle)