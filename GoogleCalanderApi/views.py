import json
import requests
from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from urllib.parse import urlencode
from google.oauth2 import credentials
from google.auth.transport.requests import Request

GOOGLE_OAUTH2_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_OAUTH2_TOKEN_URL = "https://accounts.google.com/o/oauth2/token"
GOOGLE_API_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

class LandingPageView(View):
    def get(self, request):
        # Render the landing page template
        return render(request, 'landing.html')

class GoogleCalendarInitView(View):
    def get(self, request):
        # Redirect user to Google OAuth2 authorization URL
        params = {
            'client_id': settings.CLIENT_ID,
            'redirect_uri': request.build_absolute_uri(reverse('calendar_redirect')),
            'scope': 'https://www.googleapis.com/auth/calendar.readonly',
            'response_type': 'code',
        }
        redirect_url = f"{GOOGLE_OAUTH2_AUTH_URL}?{urlencode(params)}"
        return HttpResponseRedirect(redirect_url)

class GoogleCalendarRedirectView(View):
    def get(self, request):
        code = request.GET.get('code')

        token_data = {
            'code': code,
            'client_id': settings.CLIENT_ID,
            'client_secret': settings.CLIENT_SECRET,
            'redirect_uri': request.build_absolute_uri(reverse('calendar_redirect')),
            'grant_type': 'authorization_code',
        }

        token_response = requests.post(GOOGLE_OAUTH2_TOKEN_URL, data=token_data)
        token_json = token_response.json()

        if 'error' in token_json and token_json['error'] == 'invalid_grant':
            # Handle invalid_grant error by redirecting to the authorization URL again
            return HttpResponseRedirect(reverse('calendar_init'))

        access_token = token_json.get('access_token')
        refresh_token = token_json.get('refresh_token')

        if access_token:
            # Store the access token and refresh token in the session
            request.session['access_token'] = access_token
            request.session['refresh_token'] = refresh_token

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }
            events_response = requests.get(GOOGLE_API_EVENTS_URL, headers=headers)
            events_json = events_response.json()
            events = events_json.get('items', [])
            return JsonResponse({'events': events})

        error = token_json.get('error', 'Unknown error')
        return JsonResponse({'error': error}, status=400)
