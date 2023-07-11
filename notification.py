import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pretty_html_table import build_table

MY_EMAIL = os.getenv("GMAIL")
MY_PASSWORD = os.getenv("PASSWORD")


class Notification:

    def __init__(self, rent_sent):
        self.df = rent_sent

    def send_sms(self):
        for place in self.df.Place.unique():
            place_df = self.df[self.df.Place == place]
            # create a multipart message
            message = MIMEMultipart()
            message['From'] = MY_EMAIL
            message['To'] = MY_EMAIL
            message['Subject'] = f"🏠{place.title()}|{place_df.shape[0]} New Rental House(s)"

            # attach the HTML content
            html_table = build_table(place_df,
                                     color="blue_light",
                                     font_size='small',
                                     font_family='Open Sans, san-serif',
                                     ).replace("; ", "<br>")
            html_part = MIMEText(html_table, 'html')
            message.attach(html_part)

            with smtplib.SMTP("smtp.gmail.com") as connection:
                connection.starttls()
                connection.login(user=MY_EMAIL, password=MY_PASSWORD)
                connection.send_message(message)
                print("Email sent successfully!")
