'use strict';

// Module registry theo spec §6 + taxonomy MIN-104/MIN-111.
// namespaces = command namespace sidecar ma module dung; 'shell' = xu ly
// trong Electron main (khong goi sidecar). capabilities = workflow
// versions module cong bo (contract §9.1).
// 'document-review' giu lam id ky thuat tuong thich mot chu ky — nav moi
// goi 'notary_v2' (lib.NAV_SPEC alias). 'excel-word' giu cho compat command
// word.*, khong con tren nav chinh. Namespace 'zalo' da tach (MIN-103) —
// khong con trong registry.

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
    namespaces: ['notary', 'ocr', 'file', 'diag'],
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
