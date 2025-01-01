from django.urls import path
from .views import RegisterView, LoginView, LogoutView
from .views import CSVUploadView, TemplateEditorView
from .views import SendEmailView, AIGenerateSuggestionsView
from .views import WelcomePageView, SignupPageView, SigninPageView, HomeView

urlpatterns = [
    path('', WelcomePageView.as_view(), name='welcome-page'), 
    path('signup/', SignupPageView.as_view(), name='signup-page'), 
    path('register/', RegisterView.as_view(), name='register'),
    path('signin/', SigninPageView.as_view(), name='signin-page'), 
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('home/', HomeView.as_view(), name='home'),
    path('upload-csv/', CSVUploadView.as_view(), name='upload-csv'),
    path('template/', TemplateEditorView.as_view(), name='template-editor'),
    path('send-email/', SendEmailView.as_view(), name='send-email'),
    path('ai-suggestions/', AIGenerateSuggestionsView.as_view(), name='ai-suggestions'),
]
