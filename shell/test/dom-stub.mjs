// Minimal DOM stub cho view tests (node --test, khong framework).
// Chi gom dac tinh renderer dung: createElement/classList/dataset/
// querySelector([attr="v"], .cls, tag, comma)/activeElement/dispatch.
// Tai su dung giua cac test file — khong phai DOM day du.

function matchOne(el, sel) {
  // Ho tro: tag | .cls | [attr] | [attr="v"] | tag.cls | .cls.cls2 |
  // [data-fid="v"] (map dataset camelCase). Khong ho tro combinator.
  const m = sel.trim().match(
    /^([a-zA-Z][\w-]*)?((?:\.[\w-]+)*)(\[[^\]]+\])?$/);
  if (!m) return false;
  const [, tag, clsPart, attrPart] = m;
  if (tag && el.tagName !== tag.toUpperCase()) return false;
  if (clsPart) {
    for (const c of clsPart.split('.').filter(Boolean)) {
      if (!el.classList.contains(c)) return false;
    }
  }
  if (attrPart) {
    const inner = attrPart.slice(1, -1);
    const eq = inner.indexOf('=');
    const name = eq < 0 ? inner : inner.slice(0, eq);
    let val = eq < 0 ? undefined
      : inner.slice(eq + 1).replace(/^["']|["']$/g, '');
    if (name.startsWith('data-')) {
      const key = name.slice(5)
        .replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      if (!(key in el.dataset)) return false;
      if (val !== undefined && el.dataset[key] !== val) return false;
    } else {
      const v = el.getAttribute(name) ??
        (name in el ? String(el[name]) : null);
      if (v == null) return false;
      if (val !== undefined && v !== val) return false;
    }
  }
  return true;
}

function matches(el, selector) {
  return selector.split(',').some((s) => matchOne(el, s));
}

export function collect(root, pred, out = []) {
  if (!root || !root.children) return out;
  for (const c of root.children) {
    if (pred(c)) out.push(c);
    collect(c, pred, out);
  }
  return out;
}

export function makeDom() {
  const doc = {
    _ev: {},
    activeElement: null,
    createElement: (t) => new El(t),
    createElementNS: (ns, t) => new El(t),
    addEventListener(t, f) { (this._ev[t] ||= []).push(f); },
    removeEventListener(t, f) {
      const a = this._ev[t];
      if (a) this._ev[t] = a.filter((x) => x !== f);
    },
    dispatch(t, ev) {
      for (const f of this._ev[t] || []) f(ev);
    },
  };

  class El {
    constructor(tag) {
      this.tagName = String(tag).toUpperCase();
      this.children = [];
      this.parentElement = null;
      this.attributes = {};
      this.dataset = {};
      this.style = {};
      this._ev = {};
      this._cls = '';
      this._text = '';
      this.value = '';
      this.disabled = false;
      this.hidden = false;
      this.checked = false;
      this.selected = false;
      this.draggable = false;
      this.onclick = null;
      this.oninput = null;
      this.onchange = null;
      this.scrollTop = 0;
      this.selectionStart = null;
      this.selectionEnd = null;
      this._classListInit();
    }
    _classListInit() {
      const el = this;
      el.classList = {
        add(...cs) {
          const s = new Set(el._cls.split(/\s+/).filter(Boolean));
          for (const c of cs) s.add(c);
          el._cls = [...s].join(' ');
        },
        remove(...cs) {
          const s = new Set(el._cls.split(/\s+/).filter(Boolean));
          for (const c of cs) s.delete(c);
          el._cls = [...s].join(' ');
        },
        toggle(c, force) {
          const s = new Set(el._cls.split(/\s+/).filter(Boolean));
          const on = force === undefined ? !s.has(c) : force;
          if (on) s.add(c); else s.delete(c);
          el._cls = [...s].join(' ');
          return on;
        },
        contains(c) {
          return el._cls.split(/\s+/).includes(c);
        },
      };
    }
    get className() { return this._cls; }
    set className(v) { this._cls = String(v || ''); }
    get textContent() {
      return this._text +
        this.children.map((c) => c.textContent).join('');
    }
    set textContent(v) {
      this._text = String(v);
      this.children.length = 0;
    }
    get childElementCount() { return this.children.length; }
    get firstChild() { return this.children[0] || null; }
    get isConnected() {
      let n = this;
      while (n.parentElement) n = n.parentElement;
      return n === doc.body || n === doc;
    }
    set innerHTML(v) {
      if (v === '' || v == null) this.replaceChildren();
    }
    get innerHTML() { return ''; }
    append(...cs) { for (const c of cs) { if (c != null) this.appendChild(c); } }
    appendChild(c) {
      if (c.parentElement) c.parentElement.removeChild(c);
      this.children.push(c);
      c.parentElement = this;
      return c;
    }
    prepend(c) {
      if (c.parentElement) c.parentElement.removeChild(c);
      this.children.unshift(c);
      c.parentElement = this;
      return c;
    }
    removeChild(c) {
      const i = this.children.indexOf(c);
      if (i >= 0) this.children.splice(i, 1);
      c.parentElement = null;
      return c;
    }
    replaceChildren(...cs) {
      for (const c of [...this.children]) this.removeChild(c);
      this.append(...cs);
    }
    remove() {
      if (this.parentElement) this.parentElement.removeChild(this);
    }
    contains(other) {
      let n = other;
      while (n) { if (n === this) return true; n = n.parentElement; }
      return false;
    }
    setAttribute(k, v) { this.attributes[k] = String(v); }
    getAttribute(k) { return k in this.attributes ? this.attributes[k] : null; }
    hasAttribute(k) { return k in this.attributes; }
    removeAttribute(k) { delete this.attributes[k]; }
    addEventListener(t, fn) { (this._ev[t] ||= []).push(fn); }
    removeEventListener(t, fn) {
      const a = this._ev[t];
      if (a) this._ev[t] = a.filter((x) => x !== fn);
    }
    dispatch(t, ev) {
      const e = ev || { target: this, preventDefault() {} };
      for (const f of this._ev[t] || []) f(e);
    }
    click() {
      if (this.onclick) return this.onclick({ target: this });
      this.dispatch('click', { target: this });
    }
    focus() { doc.activeElement = this; }
    blur() { if (doc.activeElement === this) doc.activeElement = null; }
    setSelectionRange(a, b) {
      this.selectionStart = a; this.selectionEnd = b;
    }
    getBoundingClientRect() {
      return { top: 0, left: 0, right: 120, bottom: 36,
               width: 120, height: 36 };
    }
    querySelector(sel) {
      return this.querySelectorAll(sel)[0] || null;
    }
    querySelectorAll(sel) {
      const out = [];
      collect(this, (e) => e !== this && matches(e, sel), out);
      return out;
    }
  }

  doc.body = new El('body');
  return { document: doc, El };
}
