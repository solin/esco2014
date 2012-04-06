from django.conf.urls.defaults import patterns, include
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^', include('femtec.site.views')),
    (r'^admin/', include(admin.site.urls)),
)

handler404 = 'femtec.site.views.handler404'
handler500 = 'femtec.site.views.handler500'
