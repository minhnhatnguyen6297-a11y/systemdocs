'use strict';

// JobTracker — theo doi job phia main; poll jobs/{id} (contract §2 poll,
// khong SSE). Khi engine_instance_id doi (sidecar restart) → job non-terminal
// thanh failed{engine_restarted} (contract §5); khi restart can →
// failed{engine_unavailable}. Renderer crash chi mat view — job van o sidecar,
// noi lai duoc bang job_id/command_id.

const { EventEmitter } = require('events');
const { JOB_POLL_MS } = require('./config');

const TERMINAL = new Set(['succeeded', 'failed', 'canceled', 'partial']);
const MAX_TRACKED = 500;

class JobTracker extends EventEmitter {
  constructor({ sidecar, logger }) {
    super();
    this.sidecar = sidecar;
    this.log = logger;
    this.jobs = new Map();   // job_id -> snapshot
    this.instanceId = null;
    this.timer = null;
    this._polling = false;
    sidecar.on('instance', (id) => this._onInstance(id));
    sidecar.on('unavailable', (reason) => this._failAll(
      (reason && reason.code) || 'engine_unavailable',
      'engine khong khoi dong lai duoc; job co the chay lai'));
  }

  track(job) {
    if (!job || !job.job_id) return;
    const prev = this.jobs.get(job.job_id);
    if (prev && TERMINAL.has(prev.status) && !TERMINAL.has(job.status)) {
      // Terminal cuc bo la bat bien (contract §5): mot snapshot
      // non-terminal tre den (stale/poll lo thu tu) khong bao gio duoc
      // mo lai job da ket thuc.
      this.log.warn('bo qua snapshot non-terminal cho job da terminal',
                    { job_id: job.job_id, status: job.status });
      return;
    }
    this.jobs.set(job.job_id, job);
    if (!prev || prev.updated_at !== job.updated_at ||
        prev.status !== job.status) {
      this.emit('job', job);
    }
    this._evict();
    this._ensurePolling();
  }

  _markTerminal(job, code, message) {
    const failed = {
      ...job,
      status: 'failed',
      waiting_on: null,
      error: {
        code,
        message,
        retryable: true,
        next_action: 'retry',
        job_id: job.job_id,
        details: null,
      },
      updated_at: new Date().toISOString(),
    };
    this.jobs.set(job.job_id, failed);
    this.emit('job', failed);
  }

  _failAll(code, message) {
    const marked = [];
    for (const job of this.jobs.values()) {
      if (!TERMINAL.has(job.status)) {
        this._markTerminal(job, code, message);
        marked.push(job.job_id);
      }
    }
    return marked;
  }

  _onInstance(newId) {
    const old = this.instanceId;
    this.instanceId = newId;
    if (old === null || old === newId) return;
    // Sidecar restart: job non-terminal chet theo process cu — danh dau
    // engine_restarted cuc bo ngay (contract §5). Main KHONG bao gio tu
    // phat lai handler — retry co chu y la command moi (command_id moi).
    const stale = this._failAll(
      'engine_restarted',
      'engine khoi dong lai giua chung; job co the chay lai');
    // Sidecar moi giu journal ben (T5): job da terminal TRUOC khi chet
    // van tra snapshot that qua getJob — reconnect theo job_id de nhan
    // dung ket qua (vd. succeeded/partial ngay sat luc restart) thay vi
    // giu engine_restarted cuc bo sai.
    for (const jobId of stale) this._resync(jobId);
  }

  async _resync(jobId) {
    try {
      if (this.sidecar.client) {
        this.track(await this.sidecar.client.getJob(jobId));
      }
    } catch {
      // Instance moi chua san / job khong con trong journal — giu danh
      // dau cuc bo (engine_restarted) lam ket luan an toan.
    }
  }

  _evict() {
    if (this.jobs.size <= MAX_TRACKED) return;
    for (const [id, job] of this.jobs) {
      if (this.jobs.size <= MAX_TRACKED) break;
      if (TERMINAL.has(job.status)) this.jobs.delete(id);
    }
  }

  _ensurePolling() {
    if (this.timer) return;
    this.timer = setInterval(() => this._pollOnce(), JOB_POLL_MS);
    this.timer.unref();
  }

  async _pollOnce() {
    if (this._polling) return;                 // chong overlap
    if (!this.sidecar.client || this.sidecar.state !== 'ready') return;
    const active = [...this.jobs.values()].filter(
      (j) => !TERMINAL.has(j.status));
    if (active.length === 0) return;
    this._polling = true;
    try {
      for (const job of active) {
        try {
          this.track(await this.sidecar.client.getJob(job.job_id));
        } catch (err) {
          // loi mang tam thoi: giu snapshot cu, poll lai vong sau;
          // restart that su duoc phat hien qua 'instance'/'unavailable'
          this.log.warn('poll job loi', { job_id: job.job_id,
                                          err: String(err.code || err) });
        }
      }
    } finally {
      this._polling = false;
    }
  }

  listActive() {
    return [...this.jobs.values()].filter((j) => !TERMINAL.has(j.status));
  }

  stop() {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }
}

module.exports = { JobTracker, TERMINAL };
