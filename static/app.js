document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('uploadForm');
  const status = document.getElementById('status');

  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    status.textContent = 'Uploading...';
    const submitBtn = form.querySelector('button[type=submit]');
    submitBtn.disabled = true;

    const input = document.getElementById('files');
    if (!input.files.length) {
      status.textContent = 'Aucun fichier sélectionné.';
      submitBtn.disabled = false;
      return;
    }

    const fd = new FormData();
    for (const f of input.files) fd.append('files', f);
    const merge = document.getElementById('merge').checked;
    if (merge) fd.append('merge', 'on');

    try {
      const resp = await fetch('/convert', { method: 'POST', body: fd });

      // If server returned JSON error (even with 200), try to parse
      const contentType = resp.headers.get('Content-Type') || '';
      if (!resp.ok || contentType.includes('application/json')) {
        const j = await resp.json().catch(()=>null);
        status.textContent = 'Erreur: ' + (j && j.error ? j.error : resp.statusText || 'Erreur serveur');
        submitBtn.disabled = false;
        return;
      }

      // Otherwise treat as binary file
      const blob = await resp.blob();

      // Try to extract filename from Content-Disposition header
      let filename = null;
      const cd = resp.headers.get('Content-Disposition') || resp.headers.get('content-disposition');
      if (cd) {
        const m = cd.match(/filename\*?=(?:UTF-8'')?"?([^";\n]+)/i);
        if (m && m[1]) filename = m[1].replace(/"/g, '');
      }
      if (!filename) {
        // fallback: if single upload and not merge, use original name
        if (!merge && input.files.length === 1) filename = input.files[0].name.replace(/\.playscore$/i, '.musicxml');
        else filename = merge ? 'merged.musicxml' : 'outputs.zip';
      }

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      status.textContent = 'Téléchargement prêt.';
    } catch (e) {
      console.error(e);
      status.textContent = 'Erreur lors de l’envoi.';
    } finally {
      submitBtn.disabled = false;
    }
  });

  // register service worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/service-worker.js').catch(()=>{});
  }
});
