'use strict';

// File log xoay vong theo kich thuoc (khong import electron de test bang
// node --test). Vuot maxBytes -> doi ten file.log -> file.log.1 ... giu
// toi da `keep` ban cu. Ghi dong bo: log it, uu tien khong mat dong khi crash.
const fs = require('fs');

function makeRotatingStream(file, { maxBytes = 5 * 1024 * 1024, keep = 3 } = {}) {
  let size = 0;
  try { size = fs.statSync(file).size; } catch { size = 0; }
  const rotate = () => {
    for (let i = keep - 1; i >= 1; i--) {
      const src = `${file}.${i}`;
      if (fs.existsSync(src)) fs.renameSync(src, `${file}.${i + 1}`);
    }
    if (keep >= 1 && fs.existsSync(file)) fs.renameSync(file, `${file}.1`);
    else if (fs.existsSync(file)) fs.unlinkSync(file);
    size = 0;
  };
  return {
    path: file,
    write(s) {
      const buf = Buffer.from(String(s), 'utf8');
      try {
        if (size > 0 && size + buf.length > maxBytes) rotate();
        fs.appendFileSync(file, buf);
        size += buf.length;
      } catch { /* log khong duoc thi bo qua, khong lam sap app */ }
    },
  };
}

module.exports = { makeRotatingStream };
