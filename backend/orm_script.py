
import psycopg2
import requests

def get_headers(api_key) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    return  headers

def send_resend_email(payload):
    if payload is None:
        raise ValueError("payload for email not found")
    api_key = "re_9vYBCPE1_Ga3WH7o46uBqJb9LCFiWp9fG"

    # request_path = RESEND_REQUEST_PATH
    # api_key = RESEND_API_KEY
    # if api_key is None:
    #     raise ValueError("Resend APi Key is Empty")
    #
    # if not  validators.url(request_path):
    #     raise ValueError("invalid url")

    headers = get_headers(api_key)
    request_path = "https://api.resend.com/emails"

    response = requests.post(request_path, json=payload, headers=headers)
    return response.json()


def ready():

   payload = {
       "from": "ogennaisrael98@gmail.com",
       "to": "ogennaisrael@gmail.com",
       "subject": "Testing Testing",
       "html": "<h1> Your account is ready to view </h1>"
   }
   emails = send_resend_email(payload)
   print(emails)

if __name__ == "__main__":
    ready()


