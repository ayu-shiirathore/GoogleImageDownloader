from flask import Flask, render_template, request, redirect, url_for
import os
import requests
import smtplib
from serpapi import GoogleSearch
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Initialize Flask app
app = Flask(__name__)

# SerpAPI key (Get it from SerpAPI: https://serpapi.com/)
SERP_API_KEY = 'e3f8d918ab45f7e12af57ba7ac200d5f1a5f7dda79a1c6125171e09a5b73c200'

# Your email configuration (Use environment variables for security)
EMAIL_USER = 'ayurathore2307@gmail.com'
EMAIL_PASSWORD = 'hey its ayushi'

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle the search query and download images
@app.route('/search', methods=['POST'])
def search_images():
    query = request.form.get('query')
    number = int(request.form.get('number'))

    if query:
        search_params = {
            "q": query,
            "tbm": "isch",  # Image search
            "num": number,
            "api_key": SERP_API_KEY
        }

        save_path = os.path.join('static', 'downloads', query.replace(' ', '_'))
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        try:
            search = GoogleSearch(search_params)
            results = search.get_dict()
            image_results = results.get("images_results", [])

            # Download and save images
            for index, image in enumerate(image_results[:number]):
                image_url = image["original"]
                img_data = requests.get(image_url).content
                with open(os.path.join(save_path, f"{index}.jpg"), 'wb') as handler:
                    handler.write(img_data)

            return redirect(url_for('download_page', query=query))
        except Exception as e:
            return f"Error: {str(e)}"

    return redirect(url_for('index'))

# Route to display the downloaded images
@app.route('/downloads/<query>')
def download_page(query):
    query_dir = query.replace(' ', '_')
    download_path = os.path.join('static', 'downloads', query_dir)
    images = [f"downloads/{query_dir}/{img}" for img in os.listdir(download_path)]
    return render_template('downloads.html', images=images, query=query)

# Route to send the images to an email
@app.route('/send_email', methods=['POST'])
def send_email():
    query = request.form.get('query')
    email = request.form.get('email')
    query_dir = query.replace(' ', '_')
    download_path = os.path.join('static', 'downloads', query_dir)
    images = os.listdir(download_path)

    if email and images:
        try:
            # Set up the email
            msg = MIMEMultipart()
            msg['From'] = EMAIL_USER
            msg['To'] = email
            msg['Subject'] = f"Downloaded Images for {query}"

            body = f"Attached are the images for your search query: {query}."
            msg.attach(MIMEText(body, 'plain'))

            # Attach the images
            for image in images:
                image_path = os.path.join(download_path, image)
                attachment = open(image_path, "rb")
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {image}")
                msg.attach(part)

            # Sending the email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(EMAIL_USER, email, text)
            server.quit()

            return f"Email successfully sent to {email}!"
        except Exception as e:
            return f"Error: {str(e)}"
    return "Email address or images not found."

if __name__ == '__main__':
    app.run(debug=True)

