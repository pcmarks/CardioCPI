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
        name='plots'),
    url(r'^chart/correlation$', 'CardioCPIv2.views.correlation_chart',
        name='correlation_chart'),
    url(r'^chart/heatmap$', 'CardioCPIv2.views.heatmap_chart',
        name='heatmap_chart'),
    url(r'^chart/combined_correlation$', 'CardioCPIv2.views.combined_correlation_chart',
        name = 'combined_correlation_chart'),
    url(r'^chart/combined_heatmap$', 'CardioCPIv2.views.combined_heatmap_chart',
        name = 'combined_heatmap_chart'),
    url(r'^statistics$', 'CardioCPIv2.views.statistics',
        name = 'statistics'),

    # Examples:
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Tack on the static files locations
urlpatterns += staticfiles_urlpatterns()

