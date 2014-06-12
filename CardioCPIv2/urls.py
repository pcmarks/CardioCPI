from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',

    url(r'^$', 'CardioCPIv2.views.home',
        name='home'),
    url(r'^platform_selection$', 'CardioCPIv2.views.platform_selection',
        name='platform_selection'),
    url(r'^gene_selection$', 'CardioCPIv2.views.gene_selection',
        name='gene_selection'),
    url(r'^plots$', 'CardioCPIv2.views.all_plots',
        name='all_plots'),
    url(r'^statistics$', 'CardioCPIv2.views.statistics',
        name = 'statistics'),
    url(r'^export$', 'CardioCPIv2.views.export',
        name = 'export'),

    # Examples:
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Tack on the static files locations
urlpatterns += staticfiles_urlpatterns()

