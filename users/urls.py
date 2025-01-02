from django.urls import path
from .views import RegisterView, LoginView, LogoutView
from .views import CSVUploadView, TemplateEditorView
from .views import SendEmailView, AIGenerateSuggestionsView, CheckAuthenticationView
from .views import WelcomePageView, SignupPageView, SigninPageView, HomeView, CSVUploadView, CSVValidationView, CreateTemplateView

urlpatterns = [
    path('', WelcomePageView.as_view(), name='welcome-page'), 
    path('signup/', SignupPageView.as_view(), name='signup-page'), 
    path('register/', RegisterView.as_view(), name='register'),
    path('signin/', SigninPageView.as_view(), name='signin-page'), 
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('home/', HomeView.as_view(), name='home'),
    path('csv-validation/', CSVValidationView.as_view(), name='csv_validation'),
    path('upload-csv/', CSVUploadView.as_view(), name='upload-csv'),
    path('create-template/', CreateTemplateView.as_view(), name='create-template'),
    path('template/', TemplateEditorView.as_view(), name='template-editor'),
    path('send-email/', SendEmailView.as_view(), name='send-email'),
    path('ai-suggestions/', AIGenerateSuggestionsView.as_view(), name='ai-suggestions'),
    path('check-authentication/', CheckAuthenticationView.as_view(), name='check-authentication'),
]
