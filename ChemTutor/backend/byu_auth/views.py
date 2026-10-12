import requests
from .models import create_user

from django.conf import settings
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth import get_user_model, login as django_login, logout as django_logout
from authlib.integrations.django_client import OAuth


### ---- BYU CAS Specific Functions ---- ###
from requests.structures import CaseInsensitiveDict
import base64
import json

# Get the info using the code returned from CAS
def get_info(code):
    '''
    Using the information from the SSO for BYU, uses the API to get information on user.

    Parameters:
        code (str):     code from BYU after user logs in to BYU, it is returned in the url
    returns:
        info (dict):    the info from the API as a dictionary jarbled mess
    '''
    url = settings.TOKEN_ENDPOINT
    headers = CaseInsensitiveDict()
    client_id = settings.CAS_CLIENT_ID
    client_secret = settings.CAS_CLIENT_SECRET
    cas_redirect_uri = settings.CAS_REDIRECT_URI
    to_encode = f"{client_id}:{client_secret}"
    urlSafeEncodedBytes = base64.urlsafe_b64encode(to_encode.encode("utf-8"))
    urlSafeEncodedStr = str(urlSafeEncodedBytes, "utf-8")
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    headers["Authorization"] = f"Basic {urlSafeEncodedStr}"
    data = f"grant_type=authorization_code&code={code}&redirect_uri={cas_redirect_uri}"
    r = requests.post(url, headers=headers, data=data)

    # Gotten into system, now to access api
    data = r.json()
    access_token = data["access_token"]
    url = "https://api.byu.edu:443/openid-userinfo/v1/userinfo?schema=openid"
    headers = {
                "Accept": "application/json",
                "Authorization": "Bearer " + access_token,
            }
    r = requests.get(url, headers=headers)
    info = json.loads(r.content)
    
    return info


#Takes code given from CAS, get the user information, and Logs them in
def logging_in(request):
    
    '''
    Logs the user in and then redierects them to the homepage
    '''
    code = request.GET.get('code', None)
    info = get_info(code)
    byu_id = info['http://byu.edu/claims/resourceowner_byu_id']

    user_info = get_user_info(byu_id)
    user = get_or_create_user(user_info)
    django_login(request, user)
    return redirect(settings.FRONTEND_URL)


# Redirect to the BYU Login
def to_login(request):
    '''
    This builds the URL to access the BYU API, and send the user to it in order to login.
    '''
    # Here is the code for getting the API URL patterns. They are quite complex, so it looks really messy
    return redirect(settings.LOGIN_URL)

#### ---- Okta Specific Views ---- ###
oauth = OAuth()
oauth.register(
    "okta",
    client_id=settings.OKTA_CLIENT_ID,
    client_secret=settings.OKTA_CLIENT_SECRET,
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=(
        f"https://{settings.OKTA_DOMAIN}/oauth2/default/.well-known/openid-configuration"
    ),
)

def login(request):
    """
    Takes user to Okta login page. After successful login, user is redirected to the callback function.
    With this routing of urls, you will need your redirect uri to be https://<your-domain>/byu/callback.
    """
    redirect_uri = (f"{settings.FRONTEND_URL}/byu/callback")
    return oauth.okta.authorize_redirect(request, redirect_uri)

def callback(request):
    """
    Calls functions to get user info from API's, then creates or updates user in database
    It then logs in the user and redirects them to the home page or admin page.
    """
    token = oauth.okta.authorize_access_token(request)
    # Store the ID token in the browser session for logging out the user:
    request.session["okta_id_token"] = token["id_token"]    
    byu_id = token["userinfo"]["byu_id"]
    
    user_info = get_user_info(byu_id)
    user = get_or_create_user(user_info)
    django_login(request, user)

    # if user.is_staff:
    #     return redirect("/adminpage/")
    return redirect("/")


def logout(request):
    """
    Retrieves the user's login token from their browser session and logs them out of the Django application. 
    It then redirects the user to the Okta logout endpoint, passing the ID token to ensure the right person is logged out.
    """
    id_token = request.session.get("okta_id_token")
    django_logout(request)

    if not id_token:
        """
        If the ID token is not found (ie it returns None), their Okta session has expired, so they don't need to be logged out of Okta.
        Redirect to the home page without resubmitting the logout request to Okta, as it will fail without the ID token.
        """
        return redirect(settings.FRONTEND_URL)

    """
    This is what actually logs the user out of Okta.
    You need to make sure you use the Logout Redirect URL in your Okta application settings, and that it matches the URL you are redirecting to after logout.
    With this routing of urls, you will need your redirect uri to be https://<your-domain>/logout/callback.
    """
    return oauth.okta.logout_redirect(
        request,
        post_logout_redirect_uri=settings.OKTA_LOGOUT_ENDPOINT,
        id_token_hint=id_token,
    )

def logout_callback(request):
    """
    This is the last step in the logout process.
    It checks the logout response from Okta to confirm the logout was a success, then redirects the user to the home page.
    """
    oauth.okta.validate_logout_response(request)
    return redirect(settings.FRONTEND_URL)


def get_or_create_user(user_info):
    """
    Using the info from the BYU API, gets the user from the database or creates a new one if it doesn't exist.

    Parameters:
        user_info (dict):    the info from the BYU API
    Returns:
        user (NewUser): the user object from the database
    """
    User = get_user_model()
    groups = user_info['groups']
    username = user_info['net_id']

    if User.objects.filter(username=username).exists():
        # Getting the user and updating permissions
        user = User.objects.get(username=username)
        user.is_staff = bool(settings.FACULTY_GROUPS.intersection(groups))
        user.is_superuser = bool(settings.ADMIN_GROUPS.intersection(groups))
        user.is_inspector = bool(settings.INSPECTOR_GROUPS.intersection(groups))
        user.save()
        return user
    else:
        # Creating a new user
        return create_user(user_info)

def get_user_info(byu_id):
    """
    Setup the authorizations for the BYU API.
    Sends request to API using credentials and BYU ID number.
    Returns organized dictionary of user details.
    """
    access_token = get_byu_api_token()
    person_data = call_byu_api(f"persons/v4/{byu_id}", access_token)
    groups_data = call_byu_api(f"persons/v4/{byu_id}/group_memberships", access_token)

    return normalize_byu_person(person_data, groups_data)

def normalize_byu_person(person_data, groups_data):
    """
    Extracts user values and which gro groups they belong to.
    (This assumes the groups have a read-only administrative SAM account in gro)
    Returns organized dictionary of user details.
    """
    # Pull all the persons attributes. You can choose additional/remove some from the return statement
    person_values = person_data.get("basic")
    if not person_values:
        raise RuntimeError(
            f"BYU Persons API response did not include a basic field set."
        )
    
    # Sorts through the returned gro groups. The only groups that show are the ones that are authorized.
    # See https://developer.byu.edu/request-a-service-account for more information.
    group_values = groups_data.get("values", [])
    groups = []
    for item in group_values:
        group_id = item.get("group_id", {})
        if isinstance(group_id, dict):
            description = group_id.get("description")
            if description:
                groups.append(description)

    return {
        "first_name": get_api_value(person_values, "preferred_first_name") or get_api_value(person_values, "first_name"),
        "last_name": get_api_value(person_values, "preferred_surname") or get_api_value(person_values, "surname"),
        "net_id": get_api_value(person_values, "net_id"),
        "email": get_api_value(person_values, "byu_internal_email"),
        "groups": groups,
    }


def get_byu_api_token():
    """
    Uses the API credentials to create an access token.
    This allows the call to BYUs API to be verified as legitimate.
    """
    response = requests.post(
        settings.TOKEN_ENDPOINT,
        data={"grant_type": "client_credentials"},
        auth=(settings.API_ID, settings.API_SECRET),
        timeout=20,
    )
    response.raise_for_status()

    return response.json()["access_token"]


def call_byu_api(path, access_token):
    """
    Takes the access token with the correct permissions to access the API,
    Then adds the headers and points it to the API url with the needed info.
    """
    response = requests.get(
        f"https://api.byu.edu/byuapi/{path.lstrip('/')}",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        timeout=20,
    )
    response.raise_for_status()

    return response.json()

def get_api_value(data, key, default=None):
    """
    Retrieves the requested values from a dictionary.
    Returns that value, or the default value if the key is not found.
    """
    field = data.get(key)

    if isinstance(field, dict):
        return (
            field.get("value")
            or field.get("description")
            or default
        )

    return field or default