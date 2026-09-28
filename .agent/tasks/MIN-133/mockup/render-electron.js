// Render mockup bằng Electron có sẵn trong shell/node_modules (không cài gì mới).
// Dùng:  D:\systemdocs\shell\node_modules\electron\dist\electron.exe render-electron.js
// Viewport = content size chính xác; ảnh PNG + metrics-<size>.json cạnh file này.
const { app, BrowserWindow } = require('electron');
const path = require('path');
const fs = require('fs');

const SIZES = [[1440, 775], [1920, 1080], [1366, 768]];
const DIR = __dirname;

app.disableHardwareAcceleration();
app.on('window-all-closed', () => {});
app.whenReady().then(async () => {
  for (const [w, h] of SIZES) {
    const win = new BrowserWindow({
      show: false, width: w, height: h, useContentSize: true,
      frame: false, webPreferences: { offscreen: false, zoomFactor: 1 },
    });
    win.setContentSize(w, h);
    await win.loadFile(path.join(DIR, 'mockup.html'));
    let metrics = '';
    for (let i = 0; i < 50 && !metrics; i++) {
      await new Promise((r) => setTimeout(r, 100));
      metrics = await win.webContents.executeJavaScript(
        "document.getElementById('metrics').textContent");
    }
    await new Promise((r) => setTimeout(r, 300));
    const img = await win.webContents.capturePage();
    fs.writeFileSync(path.join(DIR, `mockup-${w}x${h}.png`), img.toPNG());
    fs.writeFileSync(path.join(DIR, `metrics-${w}x${h}.json`), metrics);
    console.log(`== ${w}x${h} png=${img.getSize().width}x${img.getSize().height}`);
    console.log(metrics);
    win.destroy();
  }
  app.quit();
});
