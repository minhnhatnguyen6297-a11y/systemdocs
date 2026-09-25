'use strict';

// Whitelist extension cho desktop.v1.openPath (MIN-112 review): renderer
// chi duoc mo file san pham/tai lieu engine sinh ra — chan .exe/.bat/...
// qua shell.openPath. Thuan JS (khong electron) de test bang node --test.

const path = require('path');

const OPEN_PATH_EXTS = new Set([
  'docx', 'doc', 'pdf', 'txt', 'xlsx', 'xls',
  'png', 'jpg', 'jpeg', 'md', 'log', 'json',
]);

// Tra null neu ext duoc phep, hoac {code, message} de reject.
function openPathBlockReason(p) {
  const ext = path.extname(String(p || '')).slice(1).toLowerCase();
  if (!OPEN_PATH_EXTS.has(ext)) {
    return { code: 'open_failed',
             message: `loai file .${ext || '?'} khong duoc phep mo` };
  }
  return null;
}

module.exports = { OPEN_PATH_EXTS, openPathBlockReason };
