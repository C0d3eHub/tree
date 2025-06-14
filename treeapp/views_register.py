import random
import json
import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .forms import RegisterForm
from .models import UserProfile, BloodRequest

def register_view(request):
    """First step of registration - collect user data"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Don't save the user yet, just collect the data
            user_data = {
                'username': form.cleaned_data.get('username'),
                'email': form.cleaned_data.get('email'),
                'password': form.cleaned_data.get('password1'),
                'name': form.cleaned_data.get('name'),
                'father_name': form.cleaned_data.get('father_name'),
                'phone': form.cleaned_data.get('phone', ''),
                'blood_group': form.cleaned_data.get('blood_group'),
                'is_blood_donor': form.cleaned_data.get('is_blood_donor', False)
            }
            
            # Generate OTP
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Store OTP in session
            request.session['register_otp'] = otp
            request.session['register_email'] = user_data['email']
            
            # Store user data in session (as JSON string)
            request.session['register_user_data'] = json.dumps(user_data)
            
            # Send OTP via email
            try:
                send_mail(
                    'Your OTP for Family Tree Registration',
                    f'Your OTP is: {otp}\n\nThis OTP will expire in 5 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user_data['email']],
                    fail_silently=False,
                )
                return render(request, 'treeapp/verify_register_otp.html', {
                    'email': user_data['email'],
                    'user_data': json.dumps(user_data)
                })
            except Exception as e:
                print(f"Error sending email: {e}")
                messages.error(request, "Failed to send OTP. Please try again later.")
    else:
        form = RegisterForm()
    
    return render(request, 'treeapp/register.html', {'form': form})

def verify_register_otp(request):
    """Second step of registration - verify OTP and create user"""
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('register_otp')
        email = request.session.get('register_email')
        user_data_json = request.session.get('register_user_data')
        
        if not entered_otp:
            messages.error(request, "Please enter the OTP.")
            return render(request, 'treeapp/verify_register_otp.html', {'email': email})
        
        if not user_data_json:
            messages.error(request, "Registration session expired. Please register again.")
            return redirect('register')
        
        user_data = json.loads(user_data_json)
        
        # Check if OTP matches the stored one or the fixed code 554455
        if entered_otp == stored_otp or entered_otp == '554455':
            # OTP verified, create the user
            try:
                # Create user
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password']
                )
                user.is_active = False  # User needs admin approval
                user.save()
                
                # Generate verification token
                verification_token = str(uuid.uuid4())
                
                # Create user profile
                UserProfile.objects.create(
                    user=user,
                    name=user_data['name'],
                    father_name=user_data['father_name'],
                    phone=user_data['phone'],
                    plain_password=user_data['password'],
                    email_verification_token=None,  # Already verified by OTP
                    email_verified=True,  # Mark as verified
                    blood_group=user_data.get('blood_group'),
                    is_blood_donor=user_data.get('is_blood_donor', False)
                )
                
                # Clear session data
                if 'register_otp' in request.session:
                    del request.session['register_otp']
                if 'register_email' in request.session:
                    del request.session['register_email']
                if 'register_user_data' in request.session:
                    del request.session['register_user_data']
                
                # Show success message
                return render(request, 'treeapp/register_success.html', {
                    'username': user.username,
                    'name': user_data['name'],
                    'father_name': user_data['father_name'],
                    'email': user.email,
                    'verification_sent': False,  # No need for email verification
                    'email_verified': True
                })
            except Exception as e:
                print(f"Error creating user: {e}")
                messages.error(request, f"Error creating account: {str(e)}")
                return redirect('register')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, 'treeapp/verify_register_otp.html', {
                'email': email,
                'user_data': user_data_json
            })
    
    # If GET request or any other issue, redirect to register
    return redirect('register')

def resend_register_otp(request):
    """Resend OTP for registration"""
    email = request.session.get('register_email')
    user_data_json = request.session.get('register_user_data')
    
    if not email or not user_data_json:
        messages.error(request, "Registration session expired. Please register again.")
        return redirect('register')
    
    # Generate new OTP
    otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    request.session['register_otp'] = otp
    
    # Send OTP via email
    try:
        send_mail(
            'Your OTP for Family Tree Registration',
            f'Your OTP is: {otp}\n\nThis OTP will expire in 5 minutes.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        messages.success(request, "OTP has been resent to your email.")
    except Exception as e:
        print(f"Error sending email: {e}")
        messages.error(request, "Failed to send OTP. Please try again later.")
    
    return render(request, 'treeapp/verify_register_otp.html', {
        'email': email,
        'user_data': user_data_json
    })