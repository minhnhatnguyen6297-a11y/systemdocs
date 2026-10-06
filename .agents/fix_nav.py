# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("D:/systemdocs/shell/test/notary-case-drafting-view.test.mjs")
t = p.read_text(encoding="utf-8")

old1 = """  const saved = globalThis.navigator;
  const copied = [];
  globalThis.navigator = { clipboard: { writeText: async (t) => {
    copied.push(t); } } };
"""
new1 = """  const copied = [];
  Object.defineProperty(globalThis, 'navigator',
    { value: { clipboard: { writeText: async (t) => { copied.push(t); } } },
      configurable: true });
"""
assert old1 in t
t = t.replace(old1, new1, 1)

old2 = """  } finally {
    if (saved === undefined) delete globalThis.navigator;
    else globalThis.navigator = saved;
  }
});

test('TASK-4: Copy loi bao loi, khong bao da copy', async () => {
  const saved = globalThis.navigator;
  globalThis.navigator = { clipboard: { writeText: async () => {
    throw new Error('denied'); } } };
"""
new2 = """  } finally {
    delete globalThis.navigator;
  }
});

test('TASK-4: Copy loi bao loi, khong bao da copy', async () => {
  Object.defineProperty(globalThis, 'navigator',
    { value: { clipboard: { writeText: async () => {
      throw new Error('denied'); } } }, configurable: true });
"""
assert old2 in t
t = t.replace(old2, new2, 1)

old3 = """    assert.ok(box.textContent.includes('Copy thất bại'));
  } finally {
    if (saved === undefined) delete globalThis.navigator;
    else globalThis.navigator = saved;
  }
});
"""
new3 = """    assert.ok(box.textContent.includes('Copy thất bại'));
  } finally {
    delete globalThis.navigator;
  }
});
"""
assert old3 in t
t = t.replace(old3, new3, 1)
p.write_text(t, encoding="utf-8")
print("navigator stub fixed")
