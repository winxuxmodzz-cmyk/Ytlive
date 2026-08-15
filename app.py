from flask import Flask, render_template, request, redirect, flash
from werkzeug.utils import secure_filename
import subprocess
import os

app = Flask(__name__)
app.secret_key = "super_secret_key"

UPLOAD_VIDEO = 'static/videos'
UPLOAD_THUMB = 'static/thumbnails'
os.makedirs(UPLOAD_VIDEO, exist_ok=True)
os.makedirs(UPLOAD_THUMB, exist_ok=True)

stream_process = None

@app.route('/')
def dashboard():
    videos = os.listdir(UPLOAD_VIDEO)
    thumbnails = os.listdir(UPLOAD_THUMB)
    is_streaming = stream_process is not None and stream_process.poll() is None
    return render_template('dashboard.html', videos=videos, thumbnails=thumbnails, is_streaming=is_streaming)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file or file.filename == '':
        flash('Kono file select kora hoyni!', 'danger')
        return redirect('/')
    
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower()
    
    if ext in {'mp4', 'mkv', 'avi', 'mov'}:
        file.save(os.path.join(UPLOAD_VIDEO, filename))
        flash('Video uploaded!', 'success')
    elif ext in {'png', 'jpg', 'jpeg'}:
        file.save(os.path.join(UPLOAD_THUMB, filename))
        flash('Thumbnail uploaded!', 'success')
        
    return redirect('/')

@app.route('/start_stream', methods=['POST'])
def start_stream():
    global stream_process
    video_file = request.form.get('video_file')
    stream_key = request.form.get('stream_key')
    
    if not video_file or not stream_key:
        flash("Video ebong Stream Key dorkar!", "danger")
        return redirect('/')

    video_path = f"{UPLOAD_VIDEO}/{video_file}"
    youtube_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    
    command = [
        'ffmpeg', '-stream_loop', '-1', '-re', '-i', video_path,
        '-c:v', 'libx264', '-preset', 'veryfast', '-maxrate', '3000k',
        '-bufsize', '6000k', '-pix_fmt', 'yuv420p', '-g', '50',
        '-c:a', 'aac', '-b:a', '160k', '-ar', '44100',
        '-f', 'flv', youtube_url
    ]

    if stream_process is None or stream_process.poll() is not None:
        stream_process = subprocess.Popen(command)
        flash("Live Stream Running! 🚀", "success")
    
    return redirect('/')

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    global stream_process
    if stream_process and stream_process.poll() is None:
        stream_process.terminate()
        stream_process = None
        flash("Live Stream Stopped.", "danger")
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
