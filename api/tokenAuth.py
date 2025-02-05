from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

class TokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        # Get token from cookies
        cookieToken = request.COOKIES.get('authToken')
        auth_header = request.headers.get('Authorization')

        if cookieToken:
            token = cookieToken
        elif auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        else:
            return None

        # Authenticate the user with the token
        try:
            return self.authenticate_credentials(token)
        except AuthenticationFailed:
            return None 
