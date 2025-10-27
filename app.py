#!/usr/bin/env python3
"""Simple Flask backend to expose the playscore conversion as a PWA service.

Endpoints:
- GET /        -> UI
- POST /convert -> accepts uploaded .playscore files, form fields:
    - merge (on/off) : whether to merge into single MusicXML
    - prefix_parts (on/off) : not implemented here, placeholder for future

Returns generated MusicXML (single) or ZIP of multiple MusicXML files.
"""
import os
import tempfile
import shutil
from flask import Flask, request, render_template, send_file, jsonify, make_response
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static', template_folder='templates')

# Limit upload size to 100 MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Import the conversion functions from the existing script
from playscore_to_musicxml import process_single_file, merge_files


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400

    merge = request.form.get('merge', 'off') in ('on', 'true', '1')
    overwrite = True  # allow overwrite in temp
    verbose = False

    tmpdir = tempfile.mkdtemp(prefix='playscore_pwa_')
    try:
        saved = []
        for f in files:
            fname = secure_filename(f.filename)
            if not fname:
                continue
            path = os.path.join(tmpdir, fname)
            f.save(path)
            saved.append(path)

        if not saved:
            return jsonify({'error': 'No valid files uploaded'}), 400

        if merge:
            out_path = os.path.join(tmpdir, 'merged.musicxml')
            rc = merge_files(saved, out_path, overwrite=overwrite, verbose=verbose)
            if rc != 0:
                return jsonify({'error': 'Merge failed', 'code': rc}), 500
            # schedule cleanup after response
            resp = make_response(send_file(out_path, as_attachment=True, download_name='merged.musicxml'))
            resp.headers['X-Tmpdir'] = tmpdir
            return resp

        # not merge: produce one musicxml per uploaded file
        outputs = []
        for inp in saved:
            base = os.path.splitext(os.path.basename(inp))[0]
            out = os.path.join(tmpdir, base + '.musicxml')
            rc = process_single_file(inp, out, overwrite=overwrite, verbose=verbose)
            if rc == 0 and os.path.exists(out):
                outputs.append(out)

        if not outputs:
            return jsonify({'error': 'No outputs generated'}), 500

        if len(outputs) == 1:
            resp = make_response(send_file(outputs[0], as_attachment=True, download_name=os.path.basename(outputs[0])))
            resp.headers['X-Tmpdir'] = tmpdir
            return resp

        # multiple outputs -> zip
        zip_base = os.path.join(tmpdir, 'outputs')
        shutil.make_archive(zip_base, 'zip', tmpdir)
        zip_name = zip_base + '.zip'
        resp = make_response(send_file(zip_name, as_attachment=True, download_name='playscore_outputs.zip'))
        resp.headers['X-Tmpdir'] = tmpdir
        return resp

    finally:
        # cleanup is scheduled after sending via response header handler
        pass


@app.after_request
def schedule_tmp_cleanup(response):
    """If a temporary dir was used for this response, schedule its removal."""
    tmpdir = response.headers.get('X-Tmpdir')
    if tmpdir and os.path.isdir(tmpdir):
        try:
            # remove in background so response can finish
            import threading

            def _rm(path):
                try:
                    shutil.rmtree(path)
                except Exception:
                    pass

            t = threading.Thread(target=_rm, args=(tmpdir,))
            t.daemon = True
            t.start()
        except Exception:
            pass
    return response


if __name__ == '__main__':
    # Use PORT environment variable when provided (Render sets $PORT)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
