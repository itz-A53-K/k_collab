from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

class CookieTokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        # Get token from cookies
        token = request.COOKIES.get('authToken')
        if not token:
            return None

        # Authenticate the user with the token
        try:
            return self.authenticate_credentials(token)
        except AuthenticationFailed:
            return None 
