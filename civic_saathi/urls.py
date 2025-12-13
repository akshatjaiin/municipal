from django.urls import path
from .views import (
    ComplaintCreateView,
    MyComplaintsView,
    ComplaintDetailView,
    ComplaintLogsView
)

urlpatterns = [
    path("complaints/create/", ComplaintCreateView.as_view()),
    path("complaints/my/", MyComplaintsView.as_view()),
    path("complaints/<int:pk>/", ComplaintDetailView.as_view()),
    path("complaints/<int:pk>/logs/", ComplaintLogsView.as_view()),
]
