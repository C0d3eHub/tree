import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import BloodRequest, UserProfile, RecentDonation
from .forms import BloodDonorForm, BloodRequestForm

def blood_bank_view(request):
    """View for blood bank page showing donation requests and needs"""
    # Get all blood requests, newest first
    blood_requests = BloodRequest.objects.all().order_by('-created_at')
    
    # Show all donors to superusers, only visible to others
    if request.user.is_superuser:
        registered_donors = UserProfile.objects.filter(is_blood_donor=True).select_related('user')
    else:
        registered_donors = UserProfile.objects.filter(is_blood_donor=True, hide_from_donor_list=False).select_related('user')
    registered_user_ids = registered_donors.values_list('user_id', flat=True)
    donations = blood_requests.filter(request_type='donate').exclude(user_id__in=registered_user_ids)
    needs = blood_requests.filter(request_type='need')
    
    # Get blood group statistics
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    blood_stats = {}
    
    for group in blood_groups:
        donors_count = donations.filter(blood_group=group).count() + registered_donors.filter(blood_group=group).count()
        needs_count = needs.filter(blood_group=group).count()
        blood_stats[group] = {
            'donors': donors_count,
            'needs': needs_count
        }
    
    # Check if user is already a donor
    is_already_donor = False
    if request.user.is_authenticated:
        try:
            is_already_donor = request.user.userprofile.is_blood_donor
        except UserProfile.DoesNotExist:
            pass
    
    # Get recent donations for all users
    recent_donations = RecentDonation.objects.all().select_related('user').order_by('-donation_date')
    
    context = {
        'donations': donations,
        'needs': needs,
        'registered_donors': registered_donors,
        'blood_stats': blood_stats,
        'total_donors': donations.count() + registered_donors.count(),
        'total_needs': needs.count(),
        'is_already_donor': is_already_donor,
        'recent_donations': recent_donations,
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

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect

@staff_member_required
def toggle_hide_donor(request, user_id):
    profile = get_object_or_404(UserProfile, user_id=user_id)
    profile.hide_from_donor_list = not profile.hide_from_donor_list
    profile.save()
    return redirect('blood_bank')

@login_required
def register_recent_donation(request):
    """View for registering a recent blood donation"""
    if request.method == 'POST':
        donation_date = request.POST.get('donation_date')
        donation_location = request.POST.get('donation_location')
        donation_notes = request.POST.get('donation_notes')

        if not donation_date or not donation_location:
            messages.error(request, "Please fill in all required fields.")
            return redirect('blood_bank')

        try:
            RecentDonation.objects.create(
                user=request.user,
                donation_date=donation_date,
                donation_location=donation_location,
                donation_notes=donation_notes
            )
            messages.success(request, "Your recent donation has been recorded successfully!")
        except Exception as e:
            messages.error(request, "An error occurred while recording your donation. Please try again.")
        
        return redirect('blood_bank')