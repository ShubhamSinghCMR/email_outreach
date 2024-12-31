from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import pandas as pd
from rest_framework.parsers import MultiPartParser, FormParser

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
            validate_password(password)
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

class CSVUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        file = request.FILES.get('file')
        
        if not file:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Read the CSV file using pandas
            df = pd.read_csv(file)
            
            # Validate necessary columns exist
            required_columns = ['email', 'first_name']  # Example columns
            for column in required_columns:
                if column not in df.columns:
                    raise ValidationError(f"Missing required column: {column}")
            
            # Optionally, you can store this data in the database for future use or just return the data for now
            return Response({
                "message": "File uploaded and validated successfully.",
                "data": df.head().to_dict(orient='records')  # Just show a preview of the uploaded data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class TemplateEditorView(APIView):
    def post(self, request):
        template = request.data.get('template')
        
        if not template:
            return Response({"error": "Template is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate placeholders (for simplicity, we just check for {first_name})
        if '{first_name}' not in template:
            return Response({"error": "Template must contain {first_name} placeholder."}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "Template created successfully.", "template": template}, status=status.HTTP_200_OK)
