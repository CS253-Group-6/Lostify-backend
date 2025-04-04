from azure.communication.email import EmailClient
from dotenv import dotenv_values

POLLER_WAIT_TIME = 10   # seconds

def send_otp(otp: int, email: str, recipient_display_name: str):
    try:
        env = dotenv_values(".env", verbose = True)

        email_client = EmailClient.from_connection_string(env['AZURE_CONNECTION_STRING'])

        message = {
            "content": {
                "subject": "Lostify: Sign up",
                "plainText": f"LOSTIFY\n----------\nOTP for signup: {str(otp).zfill(4)}\nPlease enter this OTP to complete your signup.",
                "html": f"<html><h1>Lostify</h1><p>OTP for signup: <b>{str(otp).zfill(4)}</b><p>Please enter this OTP to complete your signup.</html>"
            },
            "recipients": {
                "to": [
                    {
                        "address": email,
                        "displayName": recipient_display_name
                    }
                ]
            },
            "senderAddress": env['AZURE_SENDER_EMAIL']
        }

        poller = email_client.begin_send(message)

        time_elapsed = 0
        while not poller.done():
            print("Email send poller status: " + poller.status())

            poller.wait(POLLER_WAIT_TIME)
            time_elapsed += POLLER_WAIT_TIME

            if time_elapsed > 6 * POLLER_WAIT_TIME:
                raise TimeoutError("Polling timed out.")

        if poller.result()["status"] == "Succeeded":
            print(f"Successfully sent the email (operation id: {poller.result()['id']})")
        else:
            raise RuntimeError(str(poller.result()["error"]))
    except Exception as ex:
        print('Exception: ')
        print(ex)
        raise ex
