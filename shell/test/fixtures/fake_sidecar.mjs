// Fake sidecar cho lifecycle test — hanh vi dieu khien bang env FAKE_MODE:
//   ok       : http server tra healthz hop le, /shutdown exit(0)
//   exit     : thoat ngay (exit-before-health)
//   badver   : healthz tra supported_versions sai
//   envdump  : ghi env da chon ra FAKE_DUMP roi serve healthz nhu 'ok'
//   neverup  : khong mo port nao (healthz timeout path — khong dung trong test
//              vi timeout 30s; giu cho debug)
import http from 'node:http';
import fs from 'node:fs';

// node --test discover ca file nay — exit khi khong phai dang duoc spawn
if (!process.env.SIDECAR_PORT) process.exit(0);

const mode = process.env.FAKE_MODE || 'ok';

if (mode === 'envdump') {
  // F3/F4: kiem env ma spawn packaged/dev thuc su truyen cho sidecar.
  fs.writeFileSync(process.env.FAKE_DUMP, JSON.stringify({
    pythonpath: process.env.PYTHONPATH ?? null,
    pythonhome: process.env.PYTHONHOME ?? null,
    pythonstartup: process.env.PYTHONSTARTUP ?? null,
    notary_data: process.env.G1_NOTARY_DATA_DIR ?? null,
    upload_data: process.env.G1_UPLOAD_DATA_DIR ?? null,
    output: process.env.G1_OUTPUT_DIR ?? null,
    engine_dir: process.env.G1_ENGINE_DIR ?? null,
    build_label: process.env.G1_BUILD_LABEL ?? null,
  }));
}

if (mode === 'exit') {
  process.exit(1);
}

if (mode !== 'neverup') {
  const body = mode === 'badver'
    ? { ok: true, supported_versions: ['v999'], engine_instance_id: 'x',
        engine_version: 'fake/0' }
    : { ok: true, supported_versions: ['desktopcommand.v1'],
        engine_instance_id: `fake-${process.pid}`, engine_version: 'fake/0' };
  http.createServer((req, res) => {
    if (req.url === '/shutdown') {
      res.end('{}');
      setTimeout(() => process.exit(0), 10);
      return;
    }
    res.setHeader('content-type', 'application/json');
    res.end(JSON.stringify(body));
  }).listen(Number(process.env.SIDECAR_PORT), '127.0.0.1');
}
