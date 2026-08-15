"""
URL configuration for harvester app (Web UI and API).
"""
from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # Web UI Views
    path('', views.home_view, name='home'),
    path('upload/', views.upload_view, name='upload'),
    path('search/', views.search_view, name='search'),
    path('urls/', views.url_list_view, name='url_list'),
    path('urls/<int:pk>/', views.url_detail_view, name='url_detail'),
    path('ingest/', views.trigger_ingest_view, name='trigger_ingest'),

    # REST API Endpoints (Task 1 Requirements)
    path('api/urls/', api_views.HarvestedURLListView.as_view(), name='api_url_list'),
    path('api/urls/<int:pk>/', api_views.HarvestedURLDetailView.as_view(), name='api_url_detail'),
    path('api/upload/', api_views.CSVUploadAPIView.as_view(), name='api_csv_upload'),
    path('api/harvest/', api_views.URLHarvestAPIView.as_view(), name='api_harvest'),
    path('api/ingest/', api_views.IngestVectorDBAPIView.as_view(), name='api_ingest'),
    path('api/search/', api_views.SemanticSearchAPIView.as_view(), name='api_semantic_search'),
    path('api/stats/', api_views.SystemStatsAPIView.as_view(), name='api_stats'),
]
