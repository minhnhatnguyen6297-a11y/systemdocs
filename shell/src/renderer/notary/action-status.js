'use strict';

/* action-status.js — trạng thái thao tác dùng chung (R14).
 *
 * Mục đích: thay toast chữ "thành công" bằng tín hiệu trực quan tại chỗ:
 *   - đang chạy  → spinner + aria-busy trên chính nút thao tác;
 *   - thành công → dấu tích xanh ngắn rồi tự trở về trạng thái thường;
 *   - lỗi        → bỏ spinner, đánh dấu lỗi trên nút; nội dung lỗi do
 *                  R13 hiển thị ở đúng ô/card/dòng sơ đồ (không toast dài).
 *
 * Nút có thể bị dựng lại giữa lúc chạy (view rebuild sau emit). Vì vậy
 * thao tác được đăng ký theo (selector, root); sync(root) áp lại trạng
 * thái busy lên node mới sau mỗi lần render.
 *
 * Export UMD: window.G1_NOTARY_ACTION_STATUS + module.exports.
 */

const DEFAULT_OK_MS = 1100;
const DEFAULT_ERR_MS = 1800;

function createActionStatus(opts) {
  const o = opts || {};
  const okMs = o.successMs || DEFAULT_OK_MS;
  const errMs = o.errorMs || DEFAULT_ERR_MS;
  const active = new Set();          // {selector, root}
  const disabledBefore = new WeakMap();
  const timers = new WeakMap();

  function resolve(entry) {
    const root = entry.root;
    if (!root || typeof root.querySelector !== 'function') return null;
    try { return root.querySelector(entry.selector); } catch (e) { return null; }
  }

  function clearTimer(el) {
    const t = timers.get(el);
    if (t) { clearTimeout(t); timers.delete(el); }
  }

  function removeMark(el) {
    const spin = el.querySelector && el.querySelector('.act-spin');
    if (spin) spin.remove();
    const check = el.querySelector && el.querySelector('.act-check');
    if (check) check.remove();
  }

  function decorate(el, state) {
    if (!el || !el.classList) return;
    clearTimer(el);
    el.classList.remove('is-busy', 'is-ok', 'is-error');
    removeMark(el);
    if (state === 'busy') {
      el.classList.add('is-busy');
      el.setAttribute('aria-busy', 'true');
      if (!disabledBefore.has(el)) disabledBefore.set(el, el.disabled);
      el.disabled = true;
      const doc = el.ownerDocument ||
        (typeof document !== 'undefined' ? document : null);
      if (doc && typeof doc.createElement === 'function') {
        const spin = doc.createElement('span');
        spin.className = 'act-spin';
        spin.setAttribute('aria-hidden', 'true');
        el.append(spin);
      }
      return;
    }
    el.removeAttribute('aria-busy');
    if (disabledBefore.has(el)) {
      el.disabled = disabledBefore.get(el);
      disabledBefore.delete(el);
    }
    if (state === 'ok') {
      el.classList.add('is-ok');
      const doc = el.ownerDocument ||
        (typeof document !== 'undefined' ? document : null);
      if (doc && typeof doc.createElement === 'function') {
        const check = doc.createElement('span');
        check.className = 'act-check';
        check.setAttribute('aria-hidden', 'true');
        check.textContent = '✓';
        el.append(check);
      }
      timers.set(el, setTimeout(() => {
        timers.delete(el);
        if (!el.classList) return;
        el.classList.remove('is-ok');
        removeMark(el);
      }, okMs));
    } else if (state === 'error') {
      el.classList.add('is-error');
      timers.set(el, setTimeout(() => {
        timers.delete(el);
        if (el.classList) el.classList.remove('is-error');
      }, errMs));
    }
  }

  // run(selector, root, task, {ok}) — bọc một thao tác dài.
  // `ok(result)` quyết định thành công; mặc định result.ok !== false.
  async function run(selector, root, task, options) {
    const entry = { selector, root };
    const first = resolve(entry);
    active.add(entry);
    if (first) decorate(first, 'busy');
    let result;
    let threw = null;
    try {
      result = await task();
    } catch (e) {
      threw = e;
    } finally {
      active.delete(entry);
    }
    const okFn = options && options.ok;
    const ok = threw ? false
      : (typeof okFn === 'function' ? !!okFn(result)
                                    : !(result && result.ok === false));
    decorate(resolve(entry) || first, ok ? 'ok' : 'error');
    if (threw) throw threw;
    return result;
  }

  // sync(root) — áp lại spinner lên node hiện tại sau mỗi lần rebuild.
  function sync(root) {
    for (const entry of active) {
      if (root && entry.root !== root) continue;
      const el = resolve(entry);
      if (el && !el.classList.contains('is-busy')) decorate(el, 'busy');
    }
  }

  function isBusy() { return active.size > 0; }

  return { run, sync, isBusy };
}

const G1_NOTARY_ACTION_STATUS = { createActionStatus };

if (typeof window !== 'undefined') {
  window.G1_NOTARY_ACTION_STATUS = G1_NOTARY_ACTION_STATUS;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = G1_NOTARY_ACTION_STATUS;
}
