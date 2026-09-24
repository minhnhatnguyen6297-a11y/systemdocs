'use strict';

// Preload — contextBridge expose dung IPC allowlist desktop.v1.*.
// Renderer khong co Node, khong fetch sidecar, khong thay token.
// MIN-112: file tu drop-zone di qua webUtils.getPathForFile (path that,
// khong the forge tu renderer) roi main cap opaque token — renderer khong
// bao gio doc thuoc tinh path cua File truc tiep.

const { contextBridge, ipcRenderer, webUtils } = require('electron');

contextBridge.exposeInMainWorld('desktop', {
  v1: {
    getModules: () => ipcRenderer.invoke('desktop.v1.getModules'),
    getStatus: () => ipcRenderer.invoke('desktop.v1.getStatus'),
    pickFiles: (opts) => ipcRenderer.invoke('desktop.v1.pickFiles', opts),
    openPath: (path) => ipcRenderer.invoke('desktop.v1.openPath', { path }),
    submitCommand: (command, payload, commandId) =>
      ipcRenderer.invoke('desktop.v1.submitCommand',
                         { command, payload, command_id: commandId }),
    getJob: (jobId) => ipcRenderer.invoke('desktop.v1.getJob', { job_id: jobId }),
    cancelJob: (jobId) =>
      ipcRenderer.invoke('desktop.v1.cancelJob', { job_id: jobId }),
    listJobs: () => ipcRenderer.invoke('desktop.v1.listJobs'),
    restartEngine: () => ipcRenderer.invoke('desktop.v1.restartEngine'),
    getDiagnostics: () => ipcRenderer.invoke('desktop.v1.getDiagnostics'),
    // File tha vao drop-zone → opaque token entry (giong pickFiles).
    // Tra {ok:true,data:{file:{file_token,name,size_bytes,is_dir}}}.
    registerDroppedFile: (file) =>
      ipcRenderer.invoke('desktop.v1.registerDroppedFile',
                         { path: webUtils.getPathForFile(file) }),
    // Bao trang thai nhap chua luu len main — window-close guard.
    setDirtyState: (dirty) =>
      ipcRenderer.invoke('desktop.v1.setDirtyState', { dirty: !!dirty }),
    onJobUpdate: (cb) => {
      ipcRenderer.on('desktop.v1.jobUpdate', (_e, job) => cb(job));
    },
    onStatusUpdate: (cb) => {
      ipcRenderer.on('desktop.v1.statusUpdate', (_e, s) => cb(s));
    },
  },
});
