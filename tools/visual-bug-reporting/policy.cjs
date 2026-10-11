'use strict';
const NOTE_MAX = 240;
const SELECTOR = /^html(?: > [a-z][a-z0-9]*:nth-child\([1-9][0-9]{0,4}\)){1,40}$/;
function enabled(packaged, flag) { return !packaged && flag === '1'; }
function validate(event, win, url, input) {
  if (event.sender !== win.webContents || event.senderFrame !== win.webContents.mainFrame ||
      event.senderFrame.url !== url) throw new Error('sender_denied');
  if (!input || JSON.stringify(input).length > 8192 ||
      typeof input.selector !== 'string' || !SELECTOR.test(input.selector) ||
      typeof input.note !== 'string' || input.note.length === 0 || input.note.length > NOTE_MAX ||
      !Array.isArray(input.sourceIds) || input.sourceIds.length > 40 ||
      !input.sourceIds.every(s => typeof s === 'string' && s.length <= 100)) {
    throw new Error('invalid_payload');
  }
  // Schema v2 control identity: optional, structure only. fid/ownId are ids
  // (no values); classes are exact classList tokens; moduleRoot is a fixed set.
  const classOk = t => typeof t === 'string' && /^[a-z0-9-]{1,40}$/i.test(t);
  const idOk = t => typeof t === 'string' && /^[a-z0-9:_-]{1,100}$/i.test(t);
  if (input.fid !== undefined && input.fid !== null && !idOk(input.fid)) throw new Error('invalid_payload');
  if (input.ownId !== undefined && input.ownId !== null && !idOk(input.ownId)) throw new Error('invalid_payload');
  if (input.classes !== undefined) {
    if (!Array.isArray(input.classes) || input.classes.length > 20 || !input.classes.every(classOk)) {
      throw new Error('invalid_payload');
    }
  }
  if (input.tableTokens !== undefined) {
    if (!Array.isArray(input.tableTokens) || input.tableTokens.length > 12 || !input.tableTokens.every(classOk)) {
      throw new Error('invalid_payload');
    }
  }
  if (input.cellLike !== undefined && input.cellLike !== null && typeof input.cellLike !== 'boolean') {
    throw new Error('invalid_payload');
  }
  if (input.moduleRoot !== undefined && input.moduleRoot !== null &&
      !['cd-root', 'upload-lab'].includes(input.moduleRoot)) throw new Error('invalid_payload');
  return {
    selector: input.selector, note: input.note, sourceIds: input.sourceIds,
    fid: input.fid ?? null, ownId: input.ownId ?? null,
    classes: Array.isArray(input.classes) ? input.classes : [],
    tableTokens: Array.isArray(input.tableTokens) ? input.tableTokens : [],
    cellLike: input.cellLike === true,
    moduleRoot: input.moduleRoot ?? null,
  };
}
module.exports = { NOTE_MAX, SELECTOR, enabled, validate };
