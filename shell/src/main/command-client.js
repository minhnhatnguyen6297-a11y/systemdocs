'use strict';

// DesktopCommand v1 client — chi Electron main dung (giu token).
// Khong import electron: test bang node --test voi fetchImpl gia.
// command_id co the do caller dua vao de retry that su idempotent (contract §5);
// khong dua thi mint moi.

const crypto = require('crypto');
const { CONTRACT_VERSION, SHELL_VERSION } = require('./config');

const TIMEOUTS = {
  healthz: 3_000,
  shutdown: 3_000,
  default: 15_000,
};

class CommandHttpError extends Error {
  constructor(httpStatus, code, message, retryable, extra = {}) {
    super(message);
    this.httpStatus = httpStatus;
    this.code = code;
    this.retryable = Boolean(retryable);
    this.next_action = extra.next_action ?? null;
    this.job_id = extra.job_id ?? null;
    this.details = extra.details ?? null;
  }
}

class CommandClient {
  constructor({ baseUrl, token, fetchImpl }) {
    this.baseUrl = baseUrl;
    this.token = token;
    this.fetch = fetchImpl || globalThis.fetch;
  }

  async _req(method, path, body, timeoutMs = TIMEOUTS.default) {
    let res;
    try {
      res = await this.fetch(this.baseUrl + path, {
        method,
        signal: AbortSignal.timeout(timeoutMs),
        headers: {
          'content-type': 'application/json',
          authorization: `Bearer ${this.token}`,
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    } catch (err) {
      const timeout = err && (err.name === 'TimeoutError' ||
                              err.name === 'AbortError');
      throw new CommandHttpError(
        0, timeout ? 'engine_timeout' : 'engine_unavailable',
        timeout ? `sidecar khong phan hoi trong ${timeoutMs}ms`
                : `khong goi duoc sidecar: ${err.message}`,
        true);
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const e = data && data.error ? data.error : {};
      throw new CommandHttpError(
        res.status, e.code || 'engine_internal_error',
        e.message || `HTTP ${res.status}`, e.retryable, e);
    }
    return data;
  }

  healthz() {
    // healthz khong can auth (contract §2)
    return this.fetch(`${this.baseUrl}/healthz`, {
      signal: AbortSignal.timeout(TIMEOUTS.healthz),
    }).then((r) => r.json());
  }

  submitCommand(command, payload, moduleId, commandId) {
    return this._req('POST', '/v1/commands', {
      contract_version: CONTRACT_VERSION,
      command_id: commandId || crypto.randomUUID(),
      command,
      payload: payload ?? null,
      client_meta: { shell_version: SHELL_VERSION, module: moduleId },
    });
  }

  getJob(jobId) {
    return this._req('GET', `/v1/jobs/${encodeURIComponent(jobId)}`,
                     undefined, 10_000);
  }

  cancelJob(jobId) {
    return this._req('POST', `/v1/jobs/${encodeURIComponent(jobId)}/cancel`,
                     undefined, 10_000);
  }

  shutdown() {
    return this._req('POST', '/shutdown', undefined, TIMEOUTS.shutdown);
  }
}

module.exports = { CommandClient, CommandHttpError, TIMEOUTS };
