'use strict';

// Preload — contextBridge expose dung IPC allowlist desktop.v1.*.
// Renderer khong co Node, khong fetch sidecar, khong thay token.

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('desktop', {
  v1: {
    getModules: () => ipcRenderer.invoke('desktop.v1.getModules'),
    getStatus: () => ipcRenderer.invoke('desktop.v1.getStatus'),
    pickFiles: (opts) => ipcRenderer.invoke('desktop.v1.pickFiles', opts),
    // openPath nhan path thuan hoac FileRef {path, scope:'machine_local'}
    // — main kiem scope/ext truoc khi mo bang OS.
    openPath: (ref) => ipcRenderer.invoke('desktop.v1.openPath',
      typeof ref === 'string'
        ? { path: ref }
        : { path: ref && ref.path, scope: ref && ref.scope }),
    submitCommand: (command, payload, commandId) =>
      ipcRenderer.invoke('desktop.v1.submitCommand',
                         { command, payload, command_id: commandId }),
    getJob: (jobId) => ipcRenderer.invoke('desktop.v1.getJob', { job_id: jobId }),
    cancelJob: (jobId) =>
      ipcRenderer.invoke('desktop.v1.cancelJob', { job_id: jobId }),
    listJobs: () => ipcRenderer.invoke('desktop.v1.listJobs'),
    restartEngine: () => ipcRenderer.invoke('desktop.v1.restartEngine'),
    getDiagnostics: () => ipcRenderer.invoke('desktop.v1.getDiagnostics'),
    onJobUpdate: (cb) => {
      ipcRenderer.on('desktop.v1.jobUpdate', (_e, job) => cb(job));
    },
    onStatusUpdate: (cb) => {
      ipcRenderer.on('desktop.v1.statusUpdate', (_e, s) => cb(s));
    },
  },
});
