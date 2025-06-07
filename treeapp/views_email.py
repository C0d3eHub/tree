import random
import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import UserProfile

def verify_email(request, token):
    """View for verifying email address using token"""
    try:
        profile = UserProfile.objects.get(email_verification_token=token)
        profile.email_verified = True
        profile.email_verification_token = None  # Clear token after use
        profile.save()
        
        messages.success(request, "Your email has been verified successfully!")
        return redirect('login')
    except UserProfile.DoesNotExist:
        messages.error(request, "Invalid verification link.")
        return redirect('login')

def resend_verification(request):
    """View for resending verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            profile = UserProfile.objects.get(user=user)
            
            # Generate new verification token
            verification_token = str(uuid.uuid4())
            profile.email_verification_token = verification_token
            profile.save()
            
            # Send verification email
            verification_url = request.build_absolute_uri(
                reverse('verify_email', args=[verification_token])
            )
            
            send_mail(
                'Verify your email for Family Tree',
                f'Please click the link below to verify your email address:\n\n{verification_url}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, "Verification email has been sent. Please check your inbox.")
            return redirect('login')
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            messages.error(request, "No account found with this email address.")
    
    return render(request, 'treeapp/verify_email.html')

def password_reset_view(request):
    """Custom password reset view that uses OTP verification"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, "Please enter your email address.")
            return render(request, 'treeapp/password_reset_custom.html')
            
        try:
            user = User.objects.get(email=email)
            
            # Generate OTP
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Store OTP in session
            request.session['email_otp'] = otp
            request.session['email_for_otp'] = email
            
            # Send OTP via email
            try:
                send_mail(
                    'Your OTP for Family Tree Password Reset',
                    f'Your OTP is: {otp}\n\nThis OTP will expire in 5 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                # Store timestamp for OTP expiration
                # request.session['otp_timestamp'] = datetime.now()
                return render(request, 'treeapp/verify_otp.html', {'email': email})
            except Exception as e:
                print(f"Error sending email: {e}")
                messages.error(request, "Failed to send OTP. Please try again later.")
                
        except User.DoesNotExist:
            messages.error(request, "No account found with this email address.")
    
    return render(request, 'treeapp/password_reset_custom.html')

def send_otp(request):
    """View for sending OTP to user's email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, "Please enter your email address.")
            return redirect('password_reset')
            
        try:
            user = User.objects.get(email=email)
            
            # Generate OTP
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Store OTP in session
            request.session['email_otp'] = otp
            request.session['email_for_otp'] = email
            
            # Send OTP via email
            try:
                send_mail(
                    'Your OTP for Family Tree',
                    f'Your OTP is: {otp}\n\nThis OTP will expire in 5 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                return render(request, 'treeapp/verify_otp.html', {'email': email})
            except Exception as e:
                print(f"Error sending email: {e}")
                messages.error(request, "Failed to send OTP. Please try again later.")
        except User.DoesNotExist:
            messages.error(request, "No account found with this email address.")
        
    return redirect('password_reset')

def verify_otp(request):
    """View for verifying OTP entered by user"""
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('email_otp')
        email = request.session.get('email_for_otp')
        
        if not entered_otp:
            messages.error(request, "Please enter the OTP.")
            return render(request, 'treeapp/verify_otp.html', {'email': email})
            
        # Check if OTP has expired (if you're storing timestamp)
        # otp_timestamp = request.session.get('otp_timestamp')
        # if otp_timestamp and (datetime.now() - otp_timestamp).total_seconds() > 300:
        #    messages.error(request, "OTP has expired. Please request a new one.")
        #    return render(request, 'treeapp/verify_otp.html', {'email': email})
            
        if entered_otp == stored_otp:
            # OTP verified, allow password reset
            try:
                user = User.objects.get(email=email)
                
                # Clear session data
                del request.session['email_otp']
                del request.session['email_for_otp']
                
                # Generate password reset token
                from django.contrib.auth.tokens import default_token_generator
                from django.utils.http import urlsafe_base64_encode
                from django.utils.encoding import force_bytes
                
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                
                reset_url = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                
                return redirect(reset_url)
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('password_reset')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, 'treeapp/verify_otp.html', {'email': email})
    
    return redirect('password_reset')