from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .validators import validate_password_strength
from django.core.exceptions import ValidationError
import pandas as pd
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
import logging
from django.core.mail import send_mail, BadHeaderError
from email_validator import validate_email, EmailNotValidError
from .tasks import send_email_task  # Import the Celery task
from rest_framework.permissions import IsAuthenticated
import ollama
import subprocess
from django.views.generic import TemplateView
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.mixins import LoginRequiredMixin

# Configure logging
logger = logging.getLogger(__name__)

class WelcomePageView(TemplateView):
    template_name = "index.html"  # Path to your index.html template

class SigninPageView(TemplateView):
    template_name = 'signin.html'  # Path to your signup.html template

class SignupPageView(TemplateView):
    template_name = 'signup.html'  # Path to your signup.html template

class HomeView(TemplateView):
    template_name = "home.html"

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # Check if username and password are provided
        if not username or not password:
            return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            return Response({'error': 'User already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate the password using Django's inbuilt validators
        try:
            validate_password_strength(password)
        except ValidationError as e:
            errors = e.messages
            return Response({
                'error': 'Password is not strong enough.',
                'details': errors,
                'guidelines': [
                    'Password must be at least 8 characters long.',
                    'Password must contain both uppercase and lowercase letters.',
                    'Password must contain at least one numeric digit.',
                    'Password must contain at least one special character.'
                ]
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create user
        user = User.objects.create_user(username=username, password=password)
        return Response({'message': 'User registered successfully.'}, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        
        # Invalid credentials
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()  # Ensures the token is blacklisted
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CSVUploadView(TemplateView):
    template_name = 'csv_validation.html'

class CSVValidationView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return JsonResponse({"error": "No file uploaded."}, status=400)

        try:
            # Read the CSV file using pandas
            df = pd.read_csv(file)

            # Define required columns
            required_columns = ['email', 'first_name']
            errors = []

            # Check for missing required columns
            for column in required_columns:
                if column not in df.columns:
                    errors.append(f"Missing required column: {column}")

            # Check for extra columns
            extra_columns = [col for col in df.columns if col not in required_columns]
            if extra_columns:
                errors.append(f"Extra columns found: {', '.join(extra_columns)}")

            if errors:
                # Return all errors in a combined response
                return JsonResponse({"error": errors}, status=400)

            # Return the response as JSON with the valid data
            return JsonResponse({
                "message": "File uploaded and validated successfully.",
                "data": df.head().to_dict(orient='records'),
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": [str(e)]}, status=400)

                
class TemplateEditorView(APIView):
    def post(self, request):
        template = request.data.get('template')
        
        if not template:
            return Response({"error": "Template is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate placeholders (for simplicity, we just check for {first_name})
        if '{first_name}' not in template:
            return Response({"error": "Template must contain {first_name} placeholder."}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "Template created successfully.", "template": template}, status=status.HTTP_200_OK)

class SendEmailView(APIView):
    def post(self, request):
        # Get the email details from the payload
        subject = request.data.get('subject')
        message = request.data.get('message')
        recipient_list = request.data.get('recipient_list')

        # Validate the input
        if not subject or not message or not recipient_list:
            return Response({'error': 'Subject, message, and recipient list are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate email addresses
        valid_emails = []
        invalid_emails = []
        for email in recipient_list:
            try:
                validate_email(email)  # Validate the email format
                valid_emails.append(email)
            except EmailNotValidError as e:
                invalid_emails.append(email)
                logger.error(f"Invalid email address: {email}. Error: {str(e)}")

        # If there are no valid emails, return an error
        if not valid_emails:
            return Response({'error': 'No valid email addresses found in the recipient list.'}, status=status.HTTP_400_BAD_REQUEST)

        # Enqueue the email sending task using Celery
        send_email_task.delay(subject, message, valid_emails)

        # Return the response showing emails sent and failed ones
        return Response({
            'message': 'Email sending started. Emails will be sent asynchronously.',
            'sent_to': valid_emails,
            'not_sent_to': invalid_emails
        }, status=status.HTTP_200_OK)

class AIGenerateSuggestionsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        description = request.data.get('description')

        if not description:
            return Response({'error': 'Description is required for generating suggestions.'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate AI email subject and body via Ollama
        try:
            subject = self.generate_email_subject(description)
            body = self.generate_email_body(description)
            return Response({
                'subject': subject,
                'body': body,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': f'Error generating content: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def generate_email_subject(self, description):
        return self.generate_with_ollama(f"Generate a one-line email subject within 10 words for: : {description}")

    def generate_email_body(self, description):
        return self.generate_with_ollama(f"Do not create subject. Write an email body for: {description}")

    def generate_with_ollama(self, prompt):
        # Run the Ollama command in subprocess
        try:
            result = subprocess.run(['ollama', 'run', 'llama3.2', prompt], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error running Ollama: {str(e)}")