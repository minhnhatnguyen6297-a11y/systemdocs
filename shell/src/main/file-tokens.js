'use strict';

// Opaque file-token store (MIN-112) — renderer khong bao gio thay native
// path tu picker/drag-drop. Main giu Map token -> FileRef that
// {path, scope:'machine_local', size_bytes, is_dir}; IPC gui cho renderer
// chi {file_token, name, size_bytes, is_dir}. Token het han cung window:
// clear() khi window closed/reload va app quit. KHONG log token hay path.

const crypto = require('crypto');
const path = require('path');

function makeFileTokenStore() {
  const map = new Map();   // file_token -> FileRef (machine_local)
  return {
    // ref: {path, scope?, size_bytes?, is_dir?} -> token uuid
    issue(ref) {
      const token = crypto.randomUUID();
      map.set(token, {
        path: ref.path,
        scope: ref.scope || 'machine_local',
        size_bytes: ref.size_bytes ?? null,
        is_dir: !!ref.is_dir,
      });
      return token;
    },
    // Tra FileRef clone hoac null (unknown/expired). Khong mutate map.
    resolve(token) {
      const ref = map.get(token);
      return ref ? { ...ref } : null;
    },
    clear() { map.clear(); },
    get size() { return map.size; },
  };
}

// Shape gui renderer tu mot path + fs.Stats: basename de hien thi,
// KHONG path/scope. st la fs.Stats (isFile()/isDirectory()/size).
function pickedEntry(store, p, st) {
  const sizeBytes = st && typeof st.isFile === 'function' && st.isFile()
    ? st.size : null;
  const isDir = !!(st && typeof st.isDirectory === 'function' &&
                   st.isDirectory());
  return {
    file_token: store.issue({
      path: p, scope: 'machine_local',
      size_bytes: sizeBytes, is_dir: isDir,
    }),
    name: path.basename(p || ''),
    size_bytes: sizeBytes,
    is_dir: isDir,
  };
}

module.exports = { makeFileTokenStore, pickedEntry };
