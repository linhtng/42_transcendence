from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
import os
import requests
import json
import urllib.parse

# Create your views here.


def register(request):
    """Register a new user."""
    if request.method != 'POST':
        # Display blank registration form.
        # If we’re not responding to a POST request, we make an instance of
        # UserCreationForm with no initial data
        form = UserCreationForm()
    else:
        # Process completed form.
        # Make an instance of UserCreationForm based on the submitted data
        form = UserCreationForm(data=request.POST)
        if form.is_valid():
            """ If the submitted data is valid, we call the form's save() 
            method to save the username and the hash of the password to the database """
            new_user = form.save()
            """ Log the user in and then redirect to home page. The save() method returns
            the newly created user object, which we assign to new_user. When the user's 
            information is saved, we log them in by calling the login() function with 
            the request and new_user objects, which creates a valid session for the new user """
            login(request, new_user)
            return JsonResponse({'success': True, 'username': new_user.username}, status=201)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    # Display a blank or invalid form.
    return render(request, 'registration/register.html', {'form': form})

def custom_login(request):
    if request.method != 'POST':
        form = AuthenticationForm()
    else:
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return JsonResponse({'success': True, 'username': user.username}, status=201)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    # Display a blank or invalid form.
    return render(request, 'registration/login.html', {'form': form})

def custom_logout(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            logout(request)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

"""
The oauth_token view is used to authenticate users with the 42 API
and log them in to the application. The view receives a code from the
42 API and uses it to get an access token. The access token is then used
to get the user's login, i.e. username from the 42 API. If the user exists in the
database, they are logged in. If the user does not exist, a new user is created
"""
def oauth_token(request):
    code = request.GET.get('code')
    if code is None:
        return JsonResponse({'success': False, 'error': 'OAuth no code'}, status=400)
    data = {
        'grant_type': 'authorization_code',
        'client_id': os.getenv('FTAPI_UID'),
        'client_secret': os.getenv('FTAPI_SECRET'),
        'code': code,
        'redirect_uri': os.getenv('FTAPI_REDIR_URL'),
    }
    response = requests.post('https://api.intra.42.fr/oauth/token', data=data)
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        # Save the access token in the session or database
        request.session['access_token'] = access_token
        # Use the access token to get the user info
        headers = {'Authorization': f'Bearer {access_token}'}
        user_info_response = requests.get('https://api.intra.42.fr/v2/me', headers=headers)
        user_login = user_info_response.json().get('login')
        # Get the user model
        User = get_user_model()

        # Check if a user with the given username exists
        try:
            user = User.objects.get(username=user_login)
        except User.DoesNotExist:
            # If the user doesn't exist, create a new user
            # Note: You should set an unusable password for the user since
            # the password is not used in the OAuth flow
            user = User.objects.create_user(username=user_login)
            print(f"Creating new user: {user.username}")
            user.set_unusable_password()
            user.save()

        # Log the user in
        login(request, user)
        return JsonResponse({'success': True, 'username': user.username}, status=201)
    else:
        return JsonResponse({'success': False, 'error': '42 authentication failed'}, status=401)