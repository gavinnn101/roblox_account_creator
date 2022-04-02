import os
import random
import requests
from loguru import logger
from anticaptchaofficial.funcaptchaproxyless import *

website_url = "https://auth.roblox.com/v2/signup"

def getXsrf():
    """
    Fuck Roblox's Cross-site request forgery shit
    Returns:
        str: X-Csrf-Token
    """
    xsrHeader = requests.post("https://auth.roblox.com/v2/login", headers={
        "X-CSRF-TOKEN": ""
    }).headers['x-csrf-token']
    logger.debug(f'csrf-token: {xsrHeader}')
    return xsrHeader


def getFieldData(csrf_token):
    """
    Get the field data code thingy That Roblox uses for captchas now
    Returns:
        str: Field data for captcha
    
    To read the codes do this::
        data = getFieldData()
        captchaId = data.split(",")[0]
        captchaData = data.split(",")[1] #(not used for creating/logging into accounts
    """
    headers = {
        'authority': 'auth.roblox.com',
        'x-csrf-token': csrf_token,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
        'content-type': 'application/json;charset=UTF-8',
        'accept': 'application/json, text/plain, */*',
    }

    return requests.post('https://auth.roblox.com/v2/signup', headers=headers, json={}).json()["failureDetails"][0]["fieldData"]


def parse_field_data(field_data) -> dict:
        captcha_id, blob = field_data.split(',')
        captcha_data = {
            'captcha_id': captcha_id,
            'captcha_blob': blob
        }
        return captcha_data


def solve_captcha(blob_value):
    api_key = os.getenv('anticaptcha_api_key') # anti-captcha key
    logger.success(f'API KEY: {api_key}')
    # website_key = "A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F"  # roblox sign-up key
    website_key = requests.get("https://apis.rbxcdn.com/captcha/v1/metadata").json()["funCaptchaPublicKeys"]['ACTION_TYPE_WEB_SIGNUP']
    logger.debug(f'Website key: {website_key}')
    login_key = "9F35E182-C93C-EBCC-A31D-CF8ED317B996"  # not needed but while I found it

    solver = funcaptchaProxyless()
    solver.set_verbose(1)
    solver.set_key(api_key)
    solver.set_website_url(website_url)
    solver.set_website_key(website_key)

    solver.set_js_api_domain('https://roblox-api.arkoselabs.com') # Not sure if this is needed
    solver.set_data_blob(str({"blob":f"{blob_value}"}))
    # solver.set_data_blob("{\"blob\":\"DATA_BLOB_VALUE_HERE\"}")

    # optional funcaptcha API subdomain, see our Funcaptcha documentation for details
    # solver.set_js_api_domain("custom-api-subdomain.arkoselabs.com")

    # optional data[blob] value, read the docs
    # solver.set_data_blob("{\"blob\":\"DATA_BLOB_VALUE_HERE\"}")

    # cdn_url: https://roblox-api.arkoselabs.com/cdn/fc
    # lurl: https://audio-us-east-1.arkoselabs.com
    # surl: https://roblox-api.arkoselabs.com

    captcha_response = solver.solve_and_return_solution()
    if captcha_response != 0:
        logger.success(f"Successful Response: {captcha_response}")
        return captcha_response
    else:
        logger.error(f"Failed Captcha: {solver.error_code}")
    return None



def create_account(username: str, password: str):
    def generate_birthday():
        # Generate random birthday for the account
        day = str(random.randint(1, 25))
        month = 'Mar'
        year = str(random.randint(1980, 2006))  # Be at least 13 years old
        birthday = f"{day} {month} {year}" # This is the format that the sign-up form uses..
        return birthday

    HEADERS = {
        # 'authority': 'auth.roblox.com',
        'x-csrf-token': getXsrf(),
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
        'content-type': 'application/json;charset=UTF-8',
        'accept': 'application/json, text/plain, */*',
    }

    data = getFieldData(HEADERS['x-csrf-token'])
    captcha_data = parse_field_data(data)

    captcha_id = captcha_data['captcha_id']
    captcha_blob = captcha_data['captcha_blob']
    logger.success(captcha_id)
    logger.success(captcha_blob)
    captcha_token = solve_captcha(blob_value=captcha_blob)

    registration_payload = {
        "username": username,
        "password": password,
        "birthday": generate_birthday(),
        "gender": 1,
        "isTosAgreementBoxChecked": True,
        "context": "MultiverseSignupForm",
        "referralData": None,
        "captchaId": captcha_id,
        "captchaToken": captcha_token,
        "captchaProvider": "PROVIDER_ARKOSE_LABS",
        "agreementIds": [
            "848d8d8f-0e33-4176-bcd9-aa4e22ae7905",
            "54d8a8f0-d9c8-4cf3-bd26-0cbf8af0bba3"
        ]
    }

    with requests.session() as session:
        response = session.post(website_url, json=registration_payload, headers=HEADERS)
        if response.ok:
            logger.success('Successful Registration!')
            logger.success(f'Cookies: {response.cookies}')
        else:
            logger.error('Failed Registration!')
            logger.debug(response.headers)
            logger.debug(response.text)
            logger.debug(response.status_code)

            data = response.json()["failureDetails"][0]["fieldData"]
            captcha_data = parse_field_data(data)

            captcha_id = captcha_data['captcha_id']
            captcha_blob = captcha_data['captcha_blob']
            logger.success(captcha_id)
            logger.success(captcha_blob)

        with open('logs.txt', 'w+') as log_file:
            log_file.write(response.text)
            logger.debug('Wrote registration response text to log.txt')


create_account('penguinmasterrr31', 'ilovepy123')