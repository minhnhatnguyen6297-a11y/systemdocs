'use strict';

// Module registry theo spec §6 — 7 muc, office la placeholder.
// namespaces = command namespace sidecar ma module dung; 'shell' = xu ly
// trong Electron main (khong goi sidecar). capabilities = workflow
// versions module cong bo (contract §9.1).

const MODULES = [
  {
    id: 'upload',
    title: 'upload_lab',
    namespaces: ['upload', 'file', 'diag'],
    // Contract §9.1: consumer kiem upload.workflow.v1 qua
    // hasWorkflowCapability truoc khi gui payload versioned.
    capabilities: ['upload.workflow.v1'],
    kind: 'engine',
    status: 'available',
  },
  {
    id: 'document-review',
    title: 'notary_v2',
    namespaces: ['notary', 'ocr', 'zalo', 'file', 'diag'],
    kind: 'engine',
    status: 'available',
  },
  {
    id: 'excel-word',
    title: 'Excel → Word',
    namespaces: ['word'],
    kind: 'engine',
    status: 'available',
  },
  {
    id: 'search',
    title: 'Tra cứu',
    namespaces: [],
    kind: 'shell',
    status: 'available',
  },
  {
    id: 'status',
    title: 'Trạng thái',
    namespaces: [],
    kind: 'shell',
    status: 'available',
  },
  {
    id: 'settings',
    title: 'Cài đặt',
    namespaces: [],
    kind: 'shell',
    status: 'available',
  },
  {
    id: 'office',
    title: 'notaryoffice',
    namespaces: [],
    kind: 'placeholder',
    status: 'unavailable',
    reason: 'not_implemented',
  },
];

function listModules() {
  return MODULES.map((m) => ({ ...m }));
}

function moduleForCommand(command) {
  const ns = String(command).split('.')[0];
  return MODULES.find((m) => m.namespaces.includes(ns)) || null;
}

module.exports = { MODULES, listModules, moduleForCommand };
