from django.urls import path

from backend.apps.categories.views import CategoryAPIView


urlpatterns = [
    path('', CategoryAPIView.as_view(), name='create-categories'),
    path('<int:pk>/', CategoryAPIView.as_view(), name='get-categories'),
]
