from django.conf.urls.defaults import patterns, include
from django.contrib import admin

from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    (r'^', include('femtec.site.views')),
    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )

handler404 = 'femtec.site.views.handler404'
handler500 = 'femtec.site.views.handler500'
