import type { FixtureDescriptor } from '../../contract/types'
import { isVerificationReport as isSavedReport } from './verificationReport'
export { ANSWER_LIMIT, isVerificationReport as isSavedReport } from './verificationReport'

const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value)
const string = (value: unknown): value is string => typeof value === 'string'
const oneOf = (value: unknown, options: string[]) => string(value) && options.includes(value)

const files = import.meta.glob(['../../fixtures/*.json', '!../../fixtures/manifest.json'], { import: 'default' })
const manifests = import.meta.glob('../../fixtures/manifest.json', { eager: true, import: 'default' })
const manifestPath = '../../fixtures/manifest.json'
const isDescriptor = (item: unknown): item is FixtureDescriptor =>
  record(item) && string(item.id) && string(item.label) && string(item.note)
  && oneOf(item.kind, ['synthetic', 'saved_live', 'offline_replay'])
  && string(item.report_file) && item.report_file !== 'manifest.json'
  && Object.prototype.hasOwnProperty.call(files, '../../fixtures/' + item.report_file)

const manifest = manifests[manifestPath]
export const savedDemos: FixtureDescriptor[] = Array.isArray(manifest) ? manifest.filter(isDescriptor) : []

export async function loadSavedReport(demo: FixtureDescriptor, expectedAnswer?: string) {
  const load = files['../../fixtures/' + demo.report_file]
  const report = await load?.()
  if (!isSavedReport(report) || !report.original_answer?.trim()) throw new Error('Invalid saved report')
  if (expectedAnswer !== undefined && report.original_answer !== expectedAnswer) throw new Error('Saved answer mismatch')
  return report
}

export function citationUrl(value: string) {
  try {
    const url = new URL(value)
    return url.protocol === 'https:' && !url.username && !url.password ? url.href : null
  } catch {
    return null
  }
}
