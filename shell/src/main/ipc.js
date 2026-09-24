'use strict';

// Versioned IPC allowlist — renderer chi goi duoc cac channel desktop.v1.*.
// Moi handler validate args; channel ngoai allowlist khong duoc dang ky
// (Electron tra loi "No handler registered" → rejection phia renderer).

const { listModules, moduleForCommand } = require('./registry');

const COMMAND_RE = /^[a-z0-9_]+(\.[a-z0-9_]+)+$/;
const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function validateCommandArgs(args) {
  if (args === null || typeof args !== 'object' || Array.isArray(args)) {
    return { ok: false, error: 'args phai la object' };
  }
  const { command, payload, command_id } = args;
  if (typeof command !== 'string' || !COMMAND_RE.test(command)) {
    return { ok: false, error: 'command phai namespaced snake_case' };
  }
  if (payload !== undefined && payload !== null &&
      (typeof payload !== 'object' || Array.isArray(payload))) {
    return { ok: false, error: 'payload phai la object/null' };
  }
  if (command_id !== undefined &&
      (typeof command_id !== 'string' || !UUID_RE.test(command_id))) {
    return { ok: false, error: 'command_id phai la uuid' };
  }
  return { ok: true };
}

function errEnvelope(err) {
  return {
    ok: false,
    error: {
      code: err.code || 'engine_internal_error',
      message: err.message || String(err),
      retryable: Boolean(err.retryable),
      next_action: err.next_action ?? null,
      job_id: err.job_id ?? null,
      details: err.details ?? null,
    },
  };
}

function unavailable() {
  return {
    ok: false,
    error: { code: 'engine_unavailable', message: 'sidecar chua san sang',
             retryable: true, next_action: 'retry', job_id: null,
             details: null },
  };
}

// ---------- opaque file token (MIN-112) ----------
// Renderer gui {file_token} thay cho FileRef trong payload; main resolve
// thanh FileRef that ngay truoc khi forward sidecar. Token unknown/expired
// -> validation_error va KHONG forward. Resolved node chi lay ref da luu —
// sibling keys (name/size_bytes/is_dir do renderer gui) bi bo qua de tranh
// renderer tu khai metadata file.

const TOKEN_BAD = Symbol('token_bad');

function resolveFileTokens(store, payload) {
  const walk = (v) => {
    if (Array.isArray(v)) {
      const out = [];
      for (const item of v) {
        const w = walk(item);
        if (w === TOKEN_BAD) return TOKEN_BAD;
        out.push(w);
      }
      return out;
    }
    if (v && typeof v === 'object') {
      if (typeof v.file_token === 'string') {
        const ref = store && store.resolve(v.file_token);
        if (!ref) return TOKEN_BAD;
        const out = { path: ref.path, scope: ref.scope };
        if (ref.size_bytes != null) out.size_bytes = ref.size_bytes;
        if (ref.is_dir) out.is_dir = true;
        return out;
      }
      const out = {};
      for (const [k, x] of Object.entries(v)) {
        const w = walk(x);
        if (w === TOKEN_BAD) return TOKEN_BAD;
        out[k] = w;
      }
      return out;
    }
    return v;
  };
  const res = walk(payload);
  if (res === TOKEN_BAD) {
    return { ok: false, error: { code: 'validation_error',
      message: 'file_token het han hoac khong hop le — chon lai file',
      retryable: false, next_action: null, job_id: null, details: null } };
  }
  return { ok: true, value: res };
}

// Tat ca handler nhan deps {sidecar, tracker, pickFiles, logger}.
// Tra {ok:true, data} hoac {ok:false, error:{...}}.
const HANDLERS = {
  'desktop.v1.getModules': async (deps) => ({
    ok: true,
    data: { modules: listModules(), sidecar: deps.sidecar.status() },
  }),

  'desktop.v1.getStatus': async (deps) => ({
    ok: true, data: deps.sidecar.status(),
  }),

  'desktop.v1.pickFiles': async (deps, args) => {
    const opts = args && typeof args === 'object' ? args : {};
    const files = await deps.pickFiles(opts);
    return { ok: true, data: { files } };
  },

  // Mo file san pham (Word export, export download) bang app mac dinh.
  // main.js validate: tuyet doi + ton tai + khong UNC.
  'desktop.v1.openPath': async (deps, args) => {
    if (!deps.openPath) {
      return { ok: false, error: { code: 'engine_unavailable',
        message: 'openPath chua cau hinh', retryable: false,
        next_action: null, job_id: null, details: null } };
    }
    try {
      const data = await deps.openPath(args || {});
      return { ok: true, data };
    } catch (err) {
      return errEnvelope(err);
    }
  },

  'desktop.v1.submitCommand': async (deps, args) => {
    const check = validateCommandArgs(args);
    if (!check.ok) {
      return { ok: false, error: { code: 'validation_error',
                                   message: check.error, retryable: false,
                                   next_action: null, job_id: null,
                                   details: null } };
    }
    if (!deps.sidecar.client || deps.sidecar.state !== 'ready') {
      return unavailable();
    }
    const mod = moduleForCommand(args.command);
    if (!mod || mod.status !== 'available') {
      return { ok: false, error: { code: 'command_unknown',
                                   message: `khong co module cho ${args.command}`,
                                   retryable: false, next_action: null,
                                   job_id: null, details: null } };
    }
    // Opaque file token → FileRef that (MIN-112). Bat ky node
    // {file_token} nao trong payload duoc resolve; token la/het han →
    // validation_error, khong forward sidecar.
    let payload = args.payload ?? null;
    if (deps.fileTokens) {
      const rr = resolveFileTokens(deps.fileTokens, payload);
      if (!rr.ok) return { ok: false, error: rr.error };
      payload = rr.value;
    }
    try {
      const job = await deps.sidecar.client.submitCommand(
        args.command, payload, mod.id, args.command_id);
      deps.tracker.track(job);
      return { ok: true, data: job };
    } catch (err) {
      return errEnvelope(err);
    }
  },

  'desktop.v1.getJob': async (deps, args) => {
    const jobId = args && args.job_id;
    if (typeof jobId !== 'string' || !jobId) {
      return { ok: false, error: { code: 'validation_error',
                                   message: 'thieu job_id', retryable: false,
                                   next_action: null, job_id: null,
                                   details: null } };
    }
    if (!deps.sidecar.client) return unavailable();
    try {
      const job = await deps.sidecar.client.getJob(jobId);
      deps.tracker.track(job);
      return { ok: true, data: job };
    } catch (err) {
      return errEnvelope(err);
    }
  },

  'desktop.v1.cancelJob': async (deps, args) => {
    const jobId = args && args.job_id;
    if (typeof jobId !== 'string' || !jobId) {
      return { ok: false, error: { code: 'validation_error',
                                   message: 'thieu job_id', retryable: false,
                                   next_action: null, job_id: null,
                                   details: null } };
    }
    if (!deps.sidecar.client) return unavailable();
    try {
      const job = await deps.sidecar.client.cancelJob(jobId);
      deps.tracker.track(job);
      return { ok: true, data: job };
    } catch (err) {
      return errEnvelope(err);
    }
  },

  // Renderer reload chi mat view — job van o sidecar/tracker; listJobs cho
  // phep noi lai toan bo snapshot (contract §5 reconnect).
  'desktop.v1.listJobs': async (deps) => ({
    ok: true,
    data: { jobs: [...(deps.tracker.jobs || new Map()).values()] },
  }),

  // Retry sau khi engine unavailable — chi co tac dung khi sidecar dang
  // stopped/unavailable; ready/starting thi tra status hien tai.
  'desktop.v1.restartEngine': async (deps) => {
    if (['unavailable', 'stopped'].includes(deps.sidecar.state)) {
      try {
        await deps.sidecar.start();
      } catch (err) {
        return errEnvelope(err);
      }
    }
    return { ok: true, data: deps.sidecar.status() };
  },

  // Panel diagnostics (MIN-32 §6): shell/sidecar version, helper status,
  // log da redact. diagnostics() do main cung cap (so huu log path).
  'desktop.v1.getDiagnostics': async (deps) => ({
    ok: true,
    data: {
      ...(deps.diagnostics ? deps.diagnostics() : {}),
      sidecar: deps.sidecar.status(),
      modules: listModules(),
    },
  }),

  // Dang ky file drop vao drop-zone (MIN-112): preload doc path qua
  // webUtils.getPathForFile (forge-proof), main stat + cap token — renderer
  // chi nhan {file_token, name, size_bytes, is_dir} nhu pickFiles.
  'desktop.v1.registerDroppedFile': async (deps, args) => {
    const p = args && typeof args.path === 'string' ? args.path : '';
    const unc = p.startsWith('\\\\') || /^\\\\\?\\UNC\\/i.test(p);
    if (!p || unc || !deps.registerDroppedFile) {
      return { ok: false, error: { code: 'validation_error',
        message: 'file tha vao khong hop le', retryable: false,
        next_action: null, job_id: null, details: null } };
    }
    try {
      const entry = await deps.registerDroppedFile(p);
      if (!entry) {
        return { ok: false, error: { code: 'file_not_found',
          message: 'file tha vao khong doc duoc', retryable: false,
          next_action: null, job_id: null, details: null } };
      }
      // data.file — cung shape pickFiles (data.files[]) de renderer dung
      // chung mot addEntry cho picker + drop.
      return { ok: true, data: { file: entry } };
    } catch (err) {
      return errEnvelope(err);
    }
  },

  // Dirty flag cho window-close guard (MIN-112): renderer bao moi khi
  // hasUnsaved doi; main chan close khi con nhap chua luu.
  'desktop.v1.setDirtyState': async (deps, args) => {
    const dirty = !!(args && args.dirty);
    if (deps.setDirty) deps.setDirty(dirty);
    return { ok: true, data: {} };
  },
};

const ALLOWLIST = Object.keys(HANDLERS);

function registerIpc(ipcMain, deps) {
  for (const [channel, handler] of Object.entries(HANDLERS)) {
    ipcMain.handle(channel, async (_event, args) => {
      try {
        return await handler(deps, args);
      } catch (err) {
        deps.logger.error('ipc handler loi', {
          channel, err: String(err && err.message || err) });
        return { ok: false, error: { code: 'shell_internal_error',
                                     message: 'loi noi bo shell',
                                     retryable: true, next_action: null,
                                     job_id: null, details: null } };
      }
    });
  }
}

module.exports = { ALLOWLIST, HANDLERS, registerIpc, validateCommandArgs,
                   resolveFileTokens };
