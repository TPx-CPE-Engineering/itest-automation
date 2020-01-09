from velocloud.api_client import ApiClient
from velocloud.apis import AllApi
from velocloud.rest import ApiException

# Set variables
operator_login_host = 'cpevc.lab-sv.telepacific.com'
operator_login_username = 'juan.brena@tpx.com'
operator_login_password = '1Maule1!'

# Set client and api
client = ApiClient(host=operator_login_host)
api = AllApi(api_client=client)

# Make auth call
try:
    client.authenticate(username=operator_login_username, password=operator_login_password, operator=True)
except ApiException as login_exception:
    print(login_exception)
    exit()
