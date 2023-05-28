import json
import requests
from django.conf import settings
from django.http import HttpResponseRedirect
from django.views import View
from urllib.parse import urlencode
from django.http import JsonResponse
from django.shortcuts import render

GOOGLE_OAUTH2_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_OAUTH2_TOKEN_URL = "https://accounts.google.com/o/oauth2/token"
GOOGLE_API_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


class GoogleCalendarInitView(View):
    def get(self, request):
        # Step 1: Redirect user to Google OAuth2 authorization URL
        params = {
            'client_id': settings.CLIENT_ID,
            'redirect_uri': request.build_absolute_uri('/rest/v1/calendar/redirect/'),
            'scope': 'https://www.googleapis.com/auth/calendar.readonly',
            'response_type': 'code',
        }
        redirect_url = f"{GOOGLE_OAUTH2_AUTH_URL}?{urlencode(params)}"
        return HttpResponseRedirect(redirect_url)

class GoogleCalendarRedirectView(View):
    def get(self, request):
        # Step 2: Handle redirect request from Google with authorization code
        code = request.GET.get('code')

        # Exchange authorization code for access token
        token_data = {
            'code': code,
            'client_id': settings.CLIENT_ID,
            'client_secret': settings.CLIENT_SECRET,
            'redirect_uri': request.build_absolute_uri('/rest/v1/calendar/redirect/'),
            'grant_type': 'authorization_code',
        }
        token_response = requests.post(GOOGLE_OAUTH2_TOKEN_URL, data=token_data)
        token_json = token_response.json()
        access_token = token_json.get('access_token')

        if access_token:
            # Get list of events using the access token
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }
            events_response = requests.get(GOOGLE_API_EVENTS_URL, headers=headers)
            events_json = events_response.json()
            events = events_json.get('items', [])
            # Process and return the events as needed
            return JsonResponse({'events': events})

        # Handle error case when access token is not obtained
        error = token_json.get('error', 'Unknown error')
        return JsonResponse({'error': error}, status=400)