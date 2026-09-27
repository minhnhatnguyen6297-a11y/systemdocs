/* ==========================================================================
   data.js — DỮ LIỆU GIẢ cho bản mẫu MIN-126. Không backend, không persist.
   Toàn bộ tên/ngày/số liệu là tưởng tượng — KHÔNG phải mặc định nghiệp vụ
   (ràng buộc "không sample-data hóa" của MIN-123 áp cho code thật; ở đây dữ
   liệu giả là bắt buộc, nhưng phải hiểu là trang trí).
   ========================================================================== */
'use strict';

window.P_DATA = (() => {

  /* ---------- helpers ---------- */
  let _uid = 0;
  const uid = (p) => `${p}${(++_uid).toString(36)}`;

  const HO = ['Nguyễn','Trần','Lê','Phạm','Hoàng','Vũ','Đặng','Bùi','Đỗ','Võ',
              'Đinh','Phan','Trương','Hà','Lưu','Ngô'];
  const DEM = ['Văn','Thị','Minh','Hồng','Ngọc','Xuân','Quốc','Gia','Thanh',
               'Hữu','Thu','Kim','Anh','Bích','Hoài'];
  const TEN = ['An','Bình','Lan','Đức','Hà','Nam','Mai','Bảo','Hùng','Dũng',
               'Hải','Thảo','Linh','Khánh','Phúc','Tâm','Trang','Sơn','Tú',
               'Oanh','Cường','Duyên','Giang','Hiếu','Khoa','Loan','My'];
  const genName = (i) =>
    `${HO[i % HO.length]} ${DEM[(i * 3 + 1) % DEM.length]} ${TEN[(i * 7 + 2) % TEN.length]}`;

  const person = (name, birth, death, giayto, diachi) => ({
    id: uid('p'), ho_ten: name, ngay_sinh: birth || '', ngay_mat: death || '',
    so_giay_to: giayto || '', dia_chi: diachi || '',
  });

  const asset = (serial, vaoso, thua, to, diachi, parcels, primary) => ({
    id: uid('a'), is_primary: !!primary,
    so_serial: serial || '', so_vao_so: vaoso || '',
    so_thua_dat: thua || '', so_to_ban_do: to || '', dia_chi: diachi || '',
    parcels: parcels || [],       // [{loai_dat, dien_tich, thoi_han}]
  });

  const LAND_TYPES = ['ONT','CLN','LUC','DGT','BHK','NTS','ONT+CLN','Đất ở đô thị'];
  const LAND_TERMS = ['Lâu dài','31/12/2040','15/10/2043','31/12/2050','20 năm'];

  const parcels = (list) => list.map(([l, s, t]) => ({
    loai_dat: l, dien_tich: s, thoi_han: t,
  }));

  /* ---------- kịch bản Notary ---------- */

  function notaryStd() {
    const people = [
      person('Nguyễn Văn An',  '12/03/1955', '08/06/2021', '012345000001'),
      person('Trần Thị Lan',   '20/10/1960', '',           '012345000002'),
      person('Nguyễn Minh Đức','25/07/1982', '',           '012345000003'),
      person('Nguyễn Thu Hà',  '14/11/1985', '',           '012345000004'),
      person('Nguyễn Hoàng Nam','03/02/1990','',           '012345000005'),
      person('Lê Thị Mai',     '09/09/1988', '',           '012345000006'),
      person('Nguyễn Gia Bảo', '17/04/2011', '',           '012345000007'),
      person('Trần Văn Bình',  '30/01/1963', '',           '012345000008'),
    ];
    const assets = [
      asset('AB 012345','01234','125','12','18 Lê Lợi', parcels([
        ['ONT','120','Lâu dài'], ['CLN','350','15/10/2043'], ['LUC','200','15/10/2043']]), true),
      asset('CD 067890','005678','208','15','42 Trần Phú', parcels([
        ['CLN','480','31/12/2050'], ['ONT','96','Lâu dài']])),
      asset('EF 024681','009876','316','22','06 Nguyễn Du', parcels([
        ['DGT','52','31/12/2040']])),
    ];
    const nodes = [
      { id:'n1', gen:0, order:0, personId:people[0].id, parents:[], spouse:'n2', chu:[1], nhan:[1] },
      { id:'n2', gen:0, order:1, personId:people[1].id, parents:[], spouse:'n1', chu:[1], nhan:[1] },
      { id:'n3', gen:1, order:0, personId:people[2].id, parents:['n1','n2'], spouse:null, chu:[], nhan:[1] },
      { id:'n4', gen:1, order:1, personId:people[3].id, parents:['n1','n2'], spouse:null, chu:[], nhan:[2] },
      { id:'n5', gen:1, order:2, personId:people[4].id, parents:['n1','n2'], spouse:null, chu:[], nhan:[3] },
      { id:'n6', gen:1, order:3, personId:null,        parents:[], spouse:null, chu:[], nhan:[] },
    ];
    // Hai bên: 30 chỗ — một vài chỗ trống ở giữa để thấy trạng thái
    const slots = {};
    for (let i = 1; i <= 30; i++) slots[i] = null;
    slots[1] = people[0].id; slots[2] = people[1].id; slots[5] = people[7].id;
    slots[16] = people[2].id; slots[17] = people[3].id; slots[18] = people[4].id;
    slots[22] = people[5].id;
    return { people, assets, nodes, slots };
  }

  function notaryEmpty() {
    return {
      people: [],
      assets: [asset('','','','','',[],true)],
      nodes: [], slots: Object.fromEntries(Array.from({length:30},(_,i)=>[i+1,null])),
    };
  }

  // Cây thừa kế tổng hợp: gen0 = cặp chủ đất; gen1 = con (+ vợ/chồng con);
  // gen2 = cháu. Trả về {people, nodes} với `total` người.
  function genTree(total, assetCount) {
    const people = [];
    const nodes = [];
    let p = 0;
    const mk = (gen, order, opts) => {
      const pers = person(
        genName(p), `${((p % 28) + 1).toString().padStart(2,'0')}/${((p * 5) % 12 + 1).toString().padStart(2,'0')}/${1948 + (p % 70)}`,
        gen === 0 ? `${((p % 27) + 1).toString().padStart(2,'0')}/02/202${p % 6}` : '',
        `012345${String(100000 + p)}`);
      people.push(pers);
      const node = Object.assign({
        id: uid('n'), gen, order, personId: pers.id,
        parents: [], spouse: null,
        chu: [], nhan: [],
      }, opts || {});
      nodes.push(node);
      p++;
      return node;
    };

    if (total === 0) return { people, nodes };
    // gen0: vợ chồng chủ
    const o1 = mk(0, 0, { chu:[1], nhan:[1] });
    if (total === 1) return { people, nodes };
    const o2 = mk(0, 1, { chu:[1], nhan:[1] });
    o1.spouse = 'x'; o2.spouse = 'x'; // spouse đánh dấu bằng order kề — layout xử lý
    o1.spouse = o2.id; o2.spouse = o1.id;

    // phân bổ phần còn lại: ~45% gen1 (con + dâu/rể), ~55% gen2 (cháu)
    const rest = total - 2;
    const gen1Count = Math.max(2, Math.round(rest * 0.45));
    const gen2Count = rest - gen1Count;
    const gen1 = [];
    for (let i = 0; i < gen1Count; i++) {
      const isSpouse = i % 3 === 2 && gen1.length; // cứ 3 người: 1 vợ/chồng
      const n = mk(1, i, {
        parents: isSpouse ? [] : [o1.id, o2.id],
        nhan: [ (i % assetCount) + 1 ],
      });
      if (isSpouse) {
        n.spouse = gen1[gen1.length - 1].id;
        gen1[gen1.length - 1].spouse = n.id;
      }
      gen1.push(n);
    }
    const gen1Parents = gen1.filter(n => n.parents.length);
    for (let i = 0; i < gen2Count; i++) {
      const par = gen1Parents.length ? [gen1Parents[i % gen1Parents.length].id] : [o1.id, o2.id];
      mk(2, i, { parents: par, nhan: [ ((i + 1) % assetCount) + 1 ] });
    }
    return { people, nodes };
  }

  function notaryN(n) {
    const assets = [
      asset('AB 012345','01234','125','12','18 Lê Lợi', parcels([
        ['ONT','120','Lâu dài'], ['CLN','350','15/10/2043']]), true),
      asset('CD 067890','005678','208','15','42 Trần Phú', parcels([
        ['CLN','480','31/12/2050']])),
      asset('EF 024681','009876','316','22','06 Nguyễn Du', parcels([
        ['LUC','200','15/10/2043'], ['BHK','140','31/12/2050'], ['NTS','88','Lâu dài']])),
    ];
    const { people, nodes } = genTree(n, assets.length);
    const slots = {};
    for (let i = 1; i <= 30; i++) slots[i] = null;
    // hai bên: xếp dồn từ chỗ 1 (đủ 30 thì đầy), chừa vài chỗ trống giữa
    const ids = people.map(x => x.id);
    for (let i = 0; i < Math.min(ids.length, 30); i++) {
      const pos = i < 15 ? i + 1 : i + 2; // chừa chỗ 16 trống ở giữa (demo "chỗ trống ở giữa")
      if (pos <= 30) slots[pos] = ids[i];
    }
    return { people, assets, nodes, slots };
  }

  function notaryLong() {
    const people = [
      person('Nguyễn Thị Hoàng Phương Anh Đào Quỳnh Như', '05/05/1952', '11/11/2020', '012345678901234'),
      person('Nguyễn Văn An', '12/03/1955', '08/06/2021', '012345000001'),
      person('Nguyễn Văn An', '02/09/1979', '', '079123000456'),
      person('Nguyễn Văn An', '22/12/2001', '', '001201999887'),
      person('Trần Văn Đường Sơn Hải', '15/07/1975', '', '074123987'),
      person('Lê Mai', '30/03/1980', '', '012366000321'),
      person('Đặng Thị Thuỳ Dương', '01/01/1983', '', '012377000654'),
    ];
    const assets = [
      asset('AB 0123456789 MỞ RỘNG','01234/2024/ĐK','1254','12/45',
        'Số 18 đường Lê Lợi, khu phố 7, phường Bến Thành, quận 1, thành phố Hồ Chí Minh',
        parcels([['ONT','120','Lâu dài'],['CLN','350','15/10/2043'],['LUC','200','15/10/2043'],
                 ['DGT','76','31/12/2040'],['BHK','55','31/12/2050'],['NTS','30','Lâu dài'],
                 ['ONT+CLN','410','15/10/2043'],['Đất ở đô thị','64','31/12/2050']]), true),
      asset('CD 067890','005678','208','15','42 Trần Phú', parcels([['CLN','480','31/12/2050']])),
      asset('EF 024681','009876','316','22','06 Nguyễn Du', parcels([['LUC','200','15/10/2043']])),
    ];
    const nodes = [
      { id:'n1', gen:0, order:0, personId:people[0].id, parents:[], spouse:'n2', chu:[1], nhan:[1] },
      { id:'n2', gen:0, order:1, personId:people[1].id, parents:[], spouse:'n1', chu:[1], nhan:[1] },
      { id:'n3', gen:1, order:0, personId:people[2].id, parents:['n1','n2'], spouse:null, chu:[], nhan:[1] },
      { id:'n4', gen:1, order:1, personId:people[3].id, parents:['n1','n2'], spouse:null, chu:[], nhan:[2] },
      { id:'n5', gen:1, order:2, personId:people[4].id, parents:['n1','n2'], spouse:null, chu:[], nhan:[3] },
    ];
    const slots = Object.fromEntries(Array.from({length:30},(_,i)=>[i+1,null]));
    slots[1]=people[0].id; slots[3]=people[1].id; slots[16]=people[2].id; slots[29]=people[3].id;
    return { people, assets, nodes, slots };
  }

  /* ---------- kịch bản Upload ---------- */

  const RNG_PATHS = [
    'D:\\HoSo\\2024\\Scan\\HS_0012_2024.pdf',
    'D:\\HoSo\\2024\\Scan\\HS_0013_2024.pdf',
    'D:\\HoSo\\2024\\Scan\\So_07\\HS_0021_2024.pdf',
    'D:\\HoSo\\2024\\Scan\\trang_phuc_full\\HS_0245_2024_NGUYEN_VAN_AN_THOA_THUAN_PHAN_CHIA_TAI_SAN_CHUNG_VO_CHONG_TRANG_01_DEN_14_BAN_DAY_DU.pdf',
    'D:\\HoSo\\2024\\Scan\\So_07\\HS_0030_2024.pdf',
    'D:\\HoSo\\2024\\Scan\\So_08\\HS_0044_2024_CAM_KET_SU_DUNG_DAT_RIENG_LE_THI_MAI_VA_TRAN_VAN_BINH_SCAN_MAU_600DPI.pdf',
    'E:\\Du_lieu_quet\\2025\\Nam_Dinh\\ho_so_da_chinh_sua_lan_2\\HS_2025_000031_MAY_A.pdf',
    'D:\\HoSo\\2024\\Scan\\HS_0058_2024.pdf',
  ];

  function queueRows(n, mode) {
    const rows = [];
    const states = ['ok','ok','ok','ok','filled','review','saved','reconcile','err','ok'];
    const notes = {
      ok: 'hợp lệ', filled: 'Đã điền sẵn', review: 'Đang chờ kiểm tra',
      saved: 'Đã lưu trên web', reconcile: 'Cần đối chiếu', err: 'Sai năm sổ',
    };
    for (let i = 0; i < n; i++) {
      let st = states[i % states.length];
      if (mode === 'states') st = states[(i * 3) % states.length];
      rows.push({
        id: `r${i}`, stt: i + 1,
        ngay: `${(i % 27 + 1).toString().padStart(2,'0')}/${((i % 6) + 7).toString().padStart(2,'0')}/2024`,
        so: `0${(120 + i * 3)}/2024`,
        note: notes[st], state: st,
        path: RNG_PATHS[i % RNG_PATHS.length],
        sel: st === 'ok' || st === 'filled',
      });
    }
    return rows;
  }

  function uploadData(mode) {
    const empty = mode === 'empty';
    return {
      website: 'Nam Định', websiteUrl: 'https://congchungnamdinh.ninhbinh.gov.vn',
      loggedIn: !empty,
      fromDate: '01/01/2024', toDate: '31/12/2024',
      excelPath: empty ? '' : 'D:\\Download\\so_cong_chung_nam_dinh_2024_ban_tai_ve_ngay_28_09_2026.xlsx',
      kpi: empty ? null : { loaded: 1240, valid: 1187, missing: 18, err: 14 },
      missing: empty ? [] : Array.from({length: 18}, (_, i) => ({
        stt: i + 1, ngay: `${(i % 27 + 1).toString().padStart(2,'0')}/08/2024`,
        so: `0${(331 + i)}/2024`,
        note: i % 5 === 2 ? 'chưa có trong sổ' : '',
      })),
      errs: empty ? [] : Array.from({length: 14}, (_, i) => ({
        stt: i + 1, ngay: i % 4 === 0 ? '' : `${(i % 27 + 1).toString().padStart(2,'0')}/09/2024`,
        so: `0${(410 + i)}/2024`,
        note: ['trùng số công chứng','sai format','thiếu ngày','sai năm sổ'][i % 4],
      })),
      folder: empty ? '' : 'D:\\HoSo\\2024\\Scan',
      ccv: 'Nguyễn Thị Hoa', thuky: 'Trần Quốc Tuấn',
      tabsPerBatch: 10,
      queue: empty ? [] : queueRows(mode === 'states' ? 46 : 46, mode),
      scanPct: empty ? 0 : 100,
      prepPct: empty ? 0 : (mode === 'states' ? 38 : 100),
    };
  }

  const NOTARY_SCENARIOS = {
    'std':       notaryStd,
    'one-asset': () => { const d = notaryStd(); d.assets = [d.assets[0]]; return d; },
    'empty':     notaryEmpty,
    'n30':       () => notaryN(30),
    'n60':       () => notaryN(60),
    'longnames': notaryLong,
  };

  return { uid, person, asset, parcels, LAND_TYPES, LAND_TERMS,
           NOTARY_SCENARIOS, uploadData, genName };
})();
