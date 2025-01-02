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
from .models import EmailTemplate
from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model

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

class SendEmailPageView(TemplateView):
    template_name = "send-email.html"

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        # Check if username and password are provided
        if not username or not password:
            return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already exists
        User = get_user_model()
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

        # Create the user
        User = get_user_model()
        user = User.objects.create_user(username=username, password=password, email=email)
        return Response({'message': 'User registered successfully.'}, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # Authenticate the user
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)  # Log the user in

            return Response({
                'message': 'Login successful',
                'loggeduserinx': user.username,
            }, status=status.HTTP_200_OK)

        # Invalid credentials
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    def post(self, request):
        try:
            logout(request)  # This clears the session for the user
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            logger.error(f"Error during logout for user {request.user.username}: {str(e)}")  # Log any errors
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CSVUploadView(TemplateView):
    template_name = 'csv_validation.html'

class CSVValidationView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view
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
        
class CheckAuthenticationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_authenticated:
            return Response({"message": "User is authenticated", "username": request.user.username}, status=200)
        else:
            return Response({"message": "User is not authenticated"}, status=401)

class CreateTemplateView(TemplateView):
    template_name = 'template-create.html'

class TemplateEditorView(APIView):
    permission_classes = [IsAuthenticated]  # Ensures only authenticated users can access this view

    def post(self, request):
        try:
            template = request.data.get('template')

            # Check if the user is authenticated (session will automatically be checked)
            if not request.user.is_authenticated:
                return Response({"error": "User must be authenticated to create a template."}, status=status.HTTP_401_UNAUTHORIZED)

            if not template:
                return Response({"error": "Template is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Save the template to the database
            new_template = EmailTemplate.objects.create(username=request.user, created_template=template)
            new_template.save()

            return Response({
                "message": "Template created successfully.",
                "template": new_template.created_template
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get the email details from the payload
        subject = request.data.get('subject')
        message = request.data.get('message')
        recipient_list = request.data.get('recipient_list')

        # Validate the input
        if not subject or not message or not recipient_list:
            return Response({"error": "Subject, message, and recipient list are required."}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response({"error": "No valid email addresses found in the recipient list."}, status=status.HTTP_400_BAD_REQUEST)

        # Enqueue the email sending task using Celery
        send_email_task.delay(subject, message, valid_emails)



        # Return the response showing emails sent and failed ones
        return Response({
            "message": "Email sending started. Emails will be sent asynchronously.",
            "sent_to": valid_emails,
            "not_sent_to": invalid_emails
        }, status=status.HTTP_200_OK)

class AIGenerateSuggestionsView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

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

class UserTemplatesView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access this view

    def get(self, request):
        try:
            # Get all templates for the current logged-in user
            templates = EmailTemplate.objects.filter(username=request.user)
            
            # Serialize the templates (assuming you have a serializer for EmailTemplate)
            template_data = [{"id": template.id, "created_template": template.created_template} for template in templates]

            return Response({
                "templates": template_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching templates for user {request.user.username}: {str(e)}")
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
