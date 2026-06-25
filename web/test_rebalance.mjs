import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';

const htmlPath = path.join('web', 'template_index.html');

console.log('--- 리밸런싱 테스트 하니스 실행 ---');

let html;
try {
  html = fs.readFileSync(htmlPath, 'utf8');
} catch (e) {
  console.error(`template_index.html 읽기 실패: ${e.message}`);
  process.exit(1);
}

// Extract window.__computeRebalance using brace matching
const searchStr = 'window.__computeRebalance =';
const startIndex = html.indexOf(searchStr);

if (startIndex === -1) {
  console.log('⚠️ [SKIP] window.__computeRebalance 함수가 template_index.html에 구현되어 있지 않습니다. (구현 대기 상태)');
  console.log('0/0 passed');
  process.exit(0);
}

const funcStartIndex = html.indexOf('function', startIndex);
const braceStartIndex = html.indexOf('{', funcStartIndex);

if (braceStartIndex === -1) {
  console.error('❌ [FAIL] function 키워드 또는 시작 중괄호({)를 찾을 수 없습니다.');
  process.exit(1);
}

let braceCount = 1;
let index = braceStartIndex + 1;
while (braceCount > 0 && index < html.length) {
  if (html[index] === '{') braceCount++;
  else if (html[index] === '}') braceCount--;
  index++;
}

const functionBody = html.substring(funcStartIndex, index);
const evalCode = `
  const window = {};
  window.__computeRebalance = ${functionBody};
  globalThis.__computeRebalance = window.__computeRebalance;
`;

const sandbox = { globalThis: {} };
try {
  vm.createContext(sandbox);
  vm.runInContext(evalCode, sandbox);
} catch (e) {
  console.error(`❌ [FAIL] 함수 추출 및 컴파일 에러: ${e.message}`);
  process.exit(1);
}

const computeRebalance = sandbox.globalThis.__computeRebalance;
if (typeof computeRebalance !== 'function') {
  console.error('❌ [FAIL] 추출된 객체가 함수가 아닙니다.');
  process.exit(1);
}

console.log('✅ 함수 추출 성공! 테스트를 시작합니다.');

let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    passed++;
    console.log(`  [PASS] ${message}`);
  } else {
    failed++;
    console.log(`  [FAIL] ${message}`);
  }
}

function approx(val1, val2, tolerance = 0.01) {
  return Math.abs(val1 - val2) <= tolerance;
}

const prices = { SOXL: 20, QLD: 100, SOXX: 200 };

// 1. ON 기본
try {
  const journal = [{ id: 1, date: '2026-06-25', type: 'buy', ticker: 'SOXL', price: 20, qty: 300 }];
  const res = computeRebalance(journal, prices, 'ON');
  assert(res && res.base === 6000, 'ON 기본: base = 6000');
  assert(res && res.holdings.SOXL === 300 && res.holdings.QLD === 0, 'ON 기본: holdings SOXL=300, QLD=0');
  assert(res && res.value.SOXL === 6000 && res.value.QLD === 0, 'ON 기본: value SOXL=6000, QLD=0');
  assert(res && approx(res.currentPct.SOXL, 1.0) && approx(res.currentPct.QLD, 0.0), 'ON 기본: currentPct SOXL=1.0, QLD=0.0');
  assert(res && approx(res.targetPct.SOXL, 0.6) && approx(res.targetPct.QLD, 0.4), 'ON 기본: targetPct SOXL=0.6, QLD=0.4');
  assert(res && res.cashTargetPct === 0, 'ON 기본: cashTargetPct = 0');
  assert(res && res.effectiveState === 'ON', 'ON 기본: effectiveState = ON');
  assert(res && res.actions.SOXL.side === 'sell' && approx(res.actions.SOXL.usd, 2400) && approx(res.actions.SOXL.shares, 120), 'ON 기본: SOXL sell $2400 (120 shares)');
  assert(res && res.actions.QLD.side === 'buy' && approx(res.actions.QLD.usd, 2400) && approx(res.actions.QLD.shares, 24), 'ON 기본: QLD buy $2400 (24 shares)');
} catch (e) {
  failed++;
  console.log(`  [FAIL] ON 기본 에러: ${e.message}`);
}

// 2. OFF
try {
  const journal = [{ id: 1, date: '2026-06-25', type: 'buy', ticker: 'SOXL', price: 20, qty: 300 }];
  const res = computeRebalance(journal, prices, 'OFF');
  assert(res && res.base === 6000, 'OFF: base = 6000');
  assert(res && approx(res.targetPct.SOXL, 0.0) && approx(res.targetPct.QLD, 0.4), 'OFF: targetPct SOXL=0.0, QLD=0.4');
  assert(res && approx(res.cashTargetPct, 0.6), 'OFF: cashTargetPct = 0.6');
  assert(res && res.effectiveState === 'OFF', 'OFF: effectiveState = OFF');
  assert(res && res.actions.SOXL.side === 'sell' && approx(res.actions.SOXL.usd, 6000) && approx(res.actions.SOXL.shares, 300), 'OFF: SOXL sell $6000 (300 shares)');
  assert(res && res.actions.QLD.side === 'buy' && approx(res.actions.QLD.usd, 2400) && approx(res.actions.QLD.shares, 24), 'OFF: QLD buy $2400 (24 shares)');
} catch (e) {
  failed++;
  console.log(`  [FAIL] OFF 에러: ${e.message}`);
}

// 3. NEUTRAL 보유중 (NEUTRAL_HELD)
try {
  const journal = [{ id: 1, date: '2026-06-25', type: 'buy', ticker: 'SOXL', price: 20, qty: 100 }];
  const res = computeRebalance(journal, prices, 'NEUTRAL');
  assert(res && res.base === 2000, 'NEUTRAL HELD: base = 2000');
  assert(res && res.effectiveState === 'NEUTRAL_HELD', 'NEUTRAL HELD: effectiveState = NEUTRAL_HELD');
  assert(res && approx(res.targetPct.SOXL, 0.6) && approx(res.targetPct.QLD, 0.4), 'NEUTRAL HELD: targetPct SOXL=0.6, QLD=0.4');
  assert(res && res.actions.SOXL.side === 'sell' && approx(res.actions.SOXL.usd, 800) && approx(res.actions.SOXL.shares, 40), 'NEUTRAL HELD: SOXL sell $800 (40 shares)');
  assert(res && res.actions.QLD.side === 'buy' && approx(res.actions.QLD.usd, 800) && approx(res.actions.QLD.shares, 8), 'NEUTRAL HELD: QLD buy $800 (8 shares)');
} catch (e) {
  failed++;
  console.log(`  [FAIL] NEUTRAL HELD 에러: ${e.message}`);
}

// 4. NEUTRAL 미보유 (NEUTRAL_FLAT)
try {
  const journal = [{ id: 1, date: '2026-06-25', type: 'buy', ticker: 'QLD', price: 100, qty: 50 }];
  const res = computeRebalance(journal, prices, 'NEUTRAL');
  assert(res && res.base === 5000, 'NEUTRAL FLAT: base = 5000');
  assert(res && res.effectiveState === 'NEUTRAL_FLAT', 'NEUTRAL FLAT: effectiveState = NEUTRAL_FLAT');
  assert(res && approx(res.targetPct.SOXL, 0.0) && approx(res.targetPct.QLD, 0.4) && approx(res.cashTargetPct, 0.6), 'NEUTRAL FLAT: targetPct SOXL=0.0, QLD=0.4, cash=0.6');
  assert(res && res.actions.QLD.side === 'sell' && approx(res.actions.QLD.usd, 3000) && approx(res.actions.QLD.shares, 30), 'NEUTRAL FLAT: QLD sell $3000 (30 shares)');
} catch (e) {
  failed++;
  console.log(`  [FAIL] NEUTRAL FLAT 에러: ${e.message}`);
}

// 5. dust
try {
  const journal = [
    { id: 1, date: '2026-06-25', type: 'buy', ticker: 'SOXL', price: 20, qty: 0.0001 },
    { id: 2, date: '2026-06-25', type: 'buy', ticker: 'QLD', price: 100, qty: 50 }
  ];
  const res = computeRebalance(journal, prices, 'NEUTRAL');
  assert(res && res.effectiveState === 'NEUTRAL_FLAT', 'dust: effectiveState = NEUTRAL_FLAT (qty 0.0001 treated as flat)');
} catch (e) {
  failed++;
  console.log(`  [FAIL] dust 에러: ${e.message}`);
}

// 6. 수량 미입력 (Missing qty)
try {
  const journal = [{ id: 1, date: '2026-06-25', type: 'buy', ticker: 'SOXL', price: 20, qty: undefined }];
  const res = computeRebalance(journal, prices, 'ON');
  assert(res && Array.isArray(res.warnings) && res.warnings.length > 0, '수량 미입력: warnings list exists');
  assert(res && res.warnings.some(w => w.includes('수량')), '수량 미입력: warnings contain qty warning');
} catch (e) {
  failed++;
  console.log(`  [FAIL] 수량 미입력 에러: ${e.message}`);
}

// 7. 보유 0 (Zero holdings)
try {
  const journal = [];
  const res = computeRebalance(journal, prices, 'ON');
  assert(res && res.base === 0, '보유 0: base = 0');
  assert(res && res.holdings.SOXL === 0 && res.holdings.QLD === 0, '보유 0: holdings 0');
} catch (e) {
  failed++;
  console.log(`  [FAIL] 보유 0 에러: ${e.message}`);
}

// 8. 음수 보유 (Negative holdings)
try {
  const journal = [
    { id: 1, date: '2026-06-25', type: 'buy', ticker: 'SOXL', price: 20, qty: 10 },
    { id: 2, date: '2026-06-25', type: 'sell', ticker: 'SOXL', price: 22, qty: 20 }
  ];
  const res = computeRebalance(journal, prices, 'ON');
  assert(res && res.holdings.SOXL === 0, '음수 보유: holdings clamped to 0');
  assert(res && Array.isArray(res.warnings) && res.warnings.length > 0, '음수 보유: warnings list exists');
} catch (e) {
  failed++;
  console.log(`  [FAIL] 음수 보유 에러: ${e.message}`);
}

console.log(`\n--- 테스트 종료: ${passed + failed} run, ${passed} passed, ${failed} failed ---`);
process.exit(failed > 0 ? 1 : 0);
