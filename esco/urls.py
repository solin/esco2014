from django.conf.urls.defaults import patterns, include
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^', include('esco.site.views')),
    (r'^admin/(.*)', admin.site.root),
)

handler404 = 'esco.site.views.handler404'
handler500 = 'esco.site.views.handler500'

