'use strict';
const { app, BrowserWindow, ipcMain } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const ROOT = 'D:\\systemdocs';
app.setPath('userData', path.join(__dirname, 'electron-profile'));
ipcMain.handle('audit-click', async (event, selector) => {
  const target = await event.sender.executeJavaScript(`(() => {
    const el = document.querySelector(${JSON.stringify(selector)});
    if (!el) throw Error('Missing click target');
    el.scrollIntoView({block:'center',inline:'nearest'});
    const r = el.getBoundingClientRect();
    const x = Math.round(r.x + r.width/2), y = Math.round(r.y + r.height/2);
    return { x, y, width:innerWidth,height:innerHeight,
      target:document.elementFromPoint(x,y)?.dataset?.fid || null };
  })()`);
  fs.writeFileSync(path.join(__dirname, 'last-click.json'), JSON.stringify({selector,...target},null,2));
  event.sender.sendInputEvent({ type: 'mouseDown', button: 'left', clickCount: 1, x:target.x,y:target.y });
  event.sender.sendInputEvent({ type: 'mouseUp', button: 'left', clickCount: 1, x:target.x,y:target.y });
  return target;
});
let win;
app.whenReady().then(async () => {
  win = new BrowserWindow({ show: false, width: 1280, height: 800,
    webPreferences: { nodeIntegration: true, contextIsolation: false, sandbox: false, backgroundThrottling: false, offscreen: true } });
  const report = [];
  for (const [width, height] of [[1280,800],[1366,768]]) {
    win.setContentSize(width, height);
    await win.loadFile(path.join(__dirname, 'harness.html'));
    const result = await win.webContents.executeJavaScript(
      `window.auditRoot=${JSON.stringify(ROOT)}; require(${JSON.stringify(path.join(__dirname, 'renderer-audit.cjs'))}).run()`);
    result.viewport = { width, height };
    report.push(result);
    await new Promise(resolve => setTimeout(resolve, 300));
    const screenshot = await win.webContents.capturePage();
    fs.writeFileSync(path.join(__dirname, `overlay-edit-${width}x${height}.png`), screenshot.toPNG());
  }
  fs.writeFileSync(path.join(__dirname, 'electron-result.json'), JSON.stringify(report, null, 2));
  const errorFile = path.join(__dirname, 'electron-error.txt');
  if (fs.existsSync(errorFile)) fs.writeFileSync(errorFile, 'Latest audit execution completed; see electron-result.json for acceptance failures. Historical harness setup errors resolved.\n');
  process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  app.quit();
}).catch(error => {
  fs.writeFileSync(path.join(__dirname, 'electron-error.txt'), String(error.stack || error));
  process.stderr.write(String(error.stack || error) + '\n');
  app.exit(1);
});
