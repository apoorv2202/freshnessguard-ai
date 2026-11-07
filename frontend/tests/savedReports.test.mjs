import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'
import { createServer } from 'vite'

let vite
let reports
before(async () => {
  vite = await createServer({
    configFile: false,
    server: { middlewareMode: true, hmr: false, ws: false, watch: null },
    optimizeDeps: { noDiscovery: true, include: [] },
    appType: 'custom',
  })
  reports = await vite.ssrLoadModule('/src/lib/savedReports.ts')
})
after(async () => { await vite?.close() })

test('all saved demos load with the recorded verdicts, score and provenance', async () => {
  const expected = {
    mixed: { kind: 'synthetic', verdicts: ['outdated', 'supported', 'not_checked'], score: 50 },
    'saved-live': { kind: 'saved_live', verdicts: ['uncertain'], score: null },
    replay: { kind: 'offline_replay', verdicts: ['outdated'], score: 0 },
    unavailable: { kind: 'synthetic', verdicts: [], score: null },
  }
  assert.equal(reports.savedDemos.length, 4)
  for (const demo of reports.savedDemos) {
    const report = await reports.loadSavedReport(demo)
    assert.equal(demo.kind, expected[demo.id].kind)
    assert.deepEqual(report.claims.map((claim) => claim.verdict), expected[demo.id].verdicts)
    assert.equal(report.freshness_score, expected[demo.id].score)
    if (demo.id === 'unavailable') assert.equal(report.status, 'unavailable')
  }
})

test('a saved report cannot be attached to an edited or unrelated answer', async () => {
  const demo = reports.savedDemos[0]
  const report = await reports.loadSavedReport(demo)
  await assert.rejects(reports.loadSavedReport(demo, 'Different pasted answer'), /mismatch/)
  await assert.rejects(reports.loadSavedReport(demo, report.original_answer + ' '), /mismatch/)
  assert.equal(await reports.loadSavedReport(demo, report.original_answer), report)
})

test('malformed reports and invented quote text are refused', async () => {
  const report = await reports.loadSavedReport(reports.savedDemos.find((demo) => demo.id === 'replay'))
  assert.equal(reports.isSavedReport({ ...report, status: 'invented' }), false)
  const changed = structuredClone(report)
  changed.claims[0].quotes[0].text = 'Invented evidence'
  assert.equal(reports.isSavedReport(changed), false)
})

test('only HTTPS citation URLs without credentials become links', () => {
  for (const value of ['javascript:alert(1)', 'http://example.com', 'https://user:pw@example.com', 'not a URL']) {
    assert.equal(reports.citationUrl(value), null)
  }
  assert.equal(reports.citationUrl('https://www.python.org/downloads/'), 'https://www.python.org/downloads/')
})
