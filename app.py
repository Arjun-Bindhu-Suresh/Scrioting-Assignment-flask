from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import boto3


load_dotenv()


app = Flask(__name__)


AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_REGION = os.getenv('AWS_REGION')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')


s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Upload to AWS S3
            s3_client.upload_file(file_path, AWS_BUCKET_NAME, filename)
            os.remove(file_path)  
            return redirect(url_for('files'))

    return render_template('upload.html')

@app.route('/files')
def files():
    # List files in the S3 bucket
    files_list = s3_client.list_objects_v2(Bucket=AWS_BUCKET_NAME).get('Contents', [])
    return render_template('files.html', files=files_list)

@app.route('/download/<filename>')
def download_file(filename):
    # Download file from S3
    file_url = s3_client.generate_presigned_url('get_object', Params={'Bucket': AWS_BUCKET_NAME, 'Key': filename})
    return redirect(file_url)

@app.route('/delete/<filename>')
def delete_file(filename):
    # Delete file from S3
    s3_client.delete_object(Bucket=AWS_BUCKET_NAME, Key=filename)
    return redirect(url_for('files'))

if __name__ == '__main__':
    app.run(debug=True)
