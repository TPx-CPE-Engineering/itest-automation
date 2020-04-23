from velocloud.api_client import ApiClient
from velocloud.apis import AllApi
from velocloud.rest import ApiException

# Disable SSL verification
import urllib3
from velocloud import configuration
configuration.verify_ssl = False
urllib3.disable_warnings()

# Set variables
operator_login_host = 'cpevc.lab-sv.telepacific.com'
operator_login_username = 'juan.brena@tpx.com'
operator_login_password = '1Maule1!'

# Set client and api
velocloud_client = ApiClient(host=operator_login_host)
velocloud_api = AllApi(api_client=velocloud_client)

# Make auth call
try:
    velocloud_client.authenticate(username=operator_login_username, password=operator_login_password, operator=True)
except ApiException as login_exception:
    print(login_exception)
    exit()
