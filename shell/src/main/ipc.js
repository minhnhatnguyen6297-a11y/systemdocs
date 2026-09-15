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
    try {
      const job = await deps.sidecar.client.submitCommand(
        args.command, args.payload ?? null, mod.id, args.command_id);
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

module.exports = { ALLOWLIST, HANDLERS, registerIpc, validateCommandArgs };
