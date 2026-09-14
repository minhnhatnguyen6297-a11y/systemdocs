'use strict';

// Diagnostics redaction theo spec §2.3 — khong credential/cookie/raw-document/
// username trong log. Thuan JS: khong import electron de test bang node --test.

const SENSITIVE_KEY =
  /password|passwd|secret|token|credential|cookie|auth|session|storage_state|api_key|bearer/i;

const REDACTED = '<redacted>';

function redactString(s) {
  if (typeof s !== 'string') return s;
  let out = s;
  // Bearer <token> -> Bearer <redacted>
  out = out.replace(/bearer\s+\S+/gi, 'Bearer ' + REDACTED);
  // C:\Users\<name>\... -> C:\Users\<user>\...
  out = out.replace(
    /([A-Za-z]:[\\/]+Users[\\/]+)([^\\/]+)/g, '$1<user>');
  // token=... / "token": "..." / token: ... trong chuoi
  out = out.replace(
    /((?:token|session|cookie|password|passwd|secret|api_key|bearer|credential|storage_state|auth(?:orization)?)["']?\s*[:=]\s*["']?)([^\s&,"'\]}]+)/gi,
    '$1' + REDACTED);
  return out;
}

function redactObject(obj) {
  if (obj === null || typeof obj !== 'object') {
    return typeof obj === 'string' ? redactString(obj) : obj;
  }
  if (Array.isArray(obj)) return obj.map(redactObject);
  const out = {};
  for (const [k, v] of Object.entries(obj)) {
    out[k] = SENSITIVE_KEY.test(k) ? REDACTED : redactObject(v);
  }
  return out;
}

function makeLogger(stream = process.stderr) {
  const write = (level, msg, meta) => {
    const line = {
      ts: new Date().toISOString(),
      level,
      msg: redactString(String(msg)),
      ...(meta ? { meta: redactObject(meta) } : {}),
    };
    stream.write(JSON.stringify(line) + '\n');
  };
  return {
    info: (m, meta) => write('info', m, meta),
    warn: (m, meta) => write('warn', m, meta),
    error: (m, meta) => write('error', m, meta),
  };
}

module.exports = { SENSITIVE_KEY, redactString, redactObject, makeLogger };
