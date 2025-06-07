import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import BloodRequest, UserProfile
from .forms import BloodDonorForm, BloodRequestForm

def blood_bank_view(request):
    """View for blood bank page showing donation requests and needs"""
    # Get all blood requests, newest first
    blood_requests = BloodRequest.objects.all().order_by('-created_at')
    
    # Split into donations and needs
    donations = blood_requests.filter(request_type='donate')
    needs = blood_requests.filter(request_type='need')
    
    # Get registered users who are blood donors
    registered_donors = UserProfile.objects.filter(is_blood_donor=True).select_related('user')
    
    # Get blood group statistics
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    blood_stats = {}
    
    for group in blood_groups:
        donors_count = donations.filter(blood_group=group).count()
        needs_count = needs.filter(blood_group=group).count()
        blood_stats[group] = {
            'donors': donors_count,
            'needs': needs_count
        }
    
    context = {
        'donations': donations,
        'needs': needs,
        'registered_donors': registered_donors,
        'blood_stats': blood_stats,
        'total_donors': donations.count(),
        'total_needs': needs.count(),
    }
    
    return render(request, 'treeapp/blood_bank.html', context)

def blood_donor_view(request):
    """View for creating a new blood donation"""
    # Pre-fill form with user data if available and logged in
    initial_data = {}
    is_registered_user = False
    
    if request.user.is_authenticated:
        try:
            profile = request.user.userprofile
            initial_data = {
                'name': profile.name or request.user.username,
                'phone': profile.phone or '',
                'blood_group': profile.blood_group or '',
            }
            is_registered_user = True
        except UserProfile.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = BloodDonorForm(request.POST)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.request_type = 'donate'
            
            if request.user.is_authenticated:
                blood_request.user = request.user
                blood_request.is_registered_user = True
            
            blood_request.save()
            
            messages.success(request, "Your blood donation offer has been submitted successfully.")
            return redirect('blood_bank')
    else:
        form = BloodDonorForm(initial=initial_data)
    
    return render(request, 'treeapp/blood_donor.html', {'form': form})

def blood_request_view(request):
    """View for creating a new blood request"""
    # Pre-fill form with user data if available and logged in
    initial_data = {}
    
    if request.user.is_authenticated:
        try:
            profile = request.user.userprofile
            initial_data = {
                'name': profile.name or request.user.username,
                'phone': profile.phone or '',
            }
        except UserProfile.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.request_type = 'need'
            
            if request.user.is_authenticated:
                blood_request.user = request.user
                blood_request.is_registered_user = True
            
            blood_request.save()
            
            messages.success(request, "Your blood request has been submitted successfully.")
            return redirect('blood_bank')
    else:
        form = BloodRequestForm(initial=initial_data)
    
    return render(request, 'treeapp/blood_need.html', {'form': form})

def verify_otp_custom(request):
    """Custom OTP verification that accepts both random OTP and fixed code 554455"""
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('register_otp')
        
        # Check if OTP matches the stored one or the fixed code 554455
        if entered_otp == stored_otp or entered_otp == '554455':
            # OTP is valid, proceed with verification
            request.session['otp_verified'] = True
            return redirect('verify_register_otp')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
    
    return render(request, 'treeapp/verify_otp_custom.html')