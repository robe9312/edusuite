from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__)
app.secret_key = 'dev-secret-key'

# Project root (one level up from this file)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

@app.route('/')
def index():
    files = []
    for root, _, filenames in os.walk(BASE_DIR):
        for f in filenames:
            if f.endswith('.py') or f.endswith('.txt'):
                rel_path = os.path.relpath(os.path.join(root, f), BASE_DIR)
                files.append(rel_path)
    return render_template('index.html', files=files)

@app.route('/edit/<path:filepath>', methods=['GET', 'POST'])
def edit_file(filepath):
    abs_path = os.path.abspath(os.path.join(BASE_DIR, filepath))
    if not abs_path.startswith(BASE_DIR):
        flash('Invalid path')
        return redirect(url_for('index'))
    if request.method == 'POST':
        content = request.form.get('content', '')
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        flash('Saved')
        return redirect(url_for('edit_file', filepath=filepath))
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        content = f'Error reading file: {e}'
    return render_template('edit.html', filepath=filepath, content=content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
