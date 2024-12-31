from django.urls import path
from .views import RegisterView, LoginView, LogoutView
from .views import CSVUploadView, TemplateEditorView
from .views import SendEmailView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('upload-csv/', CSVUploadView.as_view(), name='upload-csv'),
    path('template/', TemplateEditorView.as_view(), name='template-editor'),
    path('send-email/', SendEmailView.as_view(), name='send-email'),
]
