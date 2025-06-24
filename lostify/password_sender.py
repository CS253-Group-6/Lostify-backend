from azure.communication.email import EmailClient
from dotenv import dotenv_values

POLLER_WAIT_TIME = 10   # seconds

def send_password(password: str, email: str, recipient_display_name: str):
    try:
        env = dotenv_values(".env", verbose = True)

        email_client = EmailClient.from_connection_string(env['AZURE_CONNECTION_STRING'])

        message = {
            "content": {
                "subject": "Lostify: Reset password",
                "plainText": f"LOSTIFY\n----------\nYour new password is: {password}\nPlease change this password upon login.",
                "html": """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Password Reset Verification</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    /* Global reset & font styling */
    body, p, table, td {
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
      color: #333;
    }

    body {
      background-color: #f2f2f2;
      line-height: 1.6;
    }

    .container {
      max-width: 600px;
      margin: 40px auto;
      background-color: #ffffff;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }

    .header {
      background-color: rgb(146, 146, 252);
      color: #ffffff;
      padding: 20px;
      text-align: center;
      font-size: 1.5em;
      font-weight: bold;
    }

    .content {
      padding: 20px;
    }

    .title {
      margin-top: 0;
      font-size: 1.2em;
      margin-bottom: 10px;
    }

    .highlight-code {
      font-size: 1.8em;
      font-weight: bold;
      text-align: center;
      margin: 20px 0;
    }

    .footer {
      font-size: 0.9em;
      color: #777;
      padding: 20px;
      text-align: center;
    }

    .footer p {
      margin: 5px 0;
    }
  </style>
</head>
<body>
  <table class="container" align="center" cellpadding="0" cellspacing="0">
    <!-- HEADER SECTION -->
    <tr>
      <td class="header">
        Lostify: Password Reset
      </td>
    </tr>
    
    <!-- CONTENT SECTION -->
    <tr>
      <td class="content">
        <p class="title">Hello, """ + recipient_display_name + """!</p>
        <p>You&rsquo;ve requested to reset your password for your Lostify account.</p>
        <p>Please use the following password the next time you log in:</p>
        
        <p class="highlight-code"><code>""" + password + """</code></p>
        
        <p>Please change the password upon login.</p>
      </td>
    </tr>

    <tr>
      <td class="footer">
        <p>This is an automated message, please do not reply directly to this email.</p>
      </td>
    </tr>
  </table>
</body>
</html>
""",
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