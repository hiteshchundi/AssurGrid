import { baseUrl, requestTimeout } from './config';
export interface Rule { id: string; control_definition_id: string; control_key: string; control_name: string; control_active: boolean; frequency_months: number; due_soon_days: number; mandatory: boolean; evidence_requirement: string | null }
export interface Policy { id: string; policy_key: string; name: string }
export interface Version { id: string; version_number: number; effective_from: string; effective_to: string | null; gxp_classification: string; criticality: string; change_reason: string; rules: Rule[] }
export interface History extends Policy { versions: Version[] }
export interface PolicyPage { items: Policy[]; page: number; page_size: number; has_more: boolean }
export interface Candidate { policy_id: string; policy_key: string; policy_name: string; policy_version_id: string; version_number: number; effective_from: string; effective_to: string | null }
export interface Resolution { application_id: string; as_of: string; timezone: string; configuration: 'Resolved' | 'Missing Configuration' | 'Conflicting Configuration'; explanation: string; candidates: Candidate[]; rules: Rule[] }
export class PolicyError extends Error { constructor(message: string, public status?: number) { super(message); } }
function record(v: unknown): v is Record<string, unknown> { return typeof v === 'object' && v !== null; }
function strings(v: Record<string, unknown>, keys: string[]) { return keys.every((k) => typeof v[k] === 'string'); }
function integer(v: unknown): v is number { return typeof v === 'number' && Number.isInteger(v); }
function nullableString(v: unknown) { return v === null || typeof v === 'string'; }
function isPolicy(v: unknown): v is Policy { return record(v) && strings(v, ['id', 'policy_key', 'name']); }
function isRule(v: unknown): v is Rule { return record(v) && strings(v, ['id', 'control_definition_id', 'control_key', 'control_name']) && typeof v.control_active === 'boolean' && integer(v.frequency_months) && v.frequency_months > 0 && integer(v.due_soon_days) && v.due_soon_days >= 0 && typeof v.mandatory === 'boolean' && nullableString(v.evidence_requirement); }
function isVersion(v: unknown): v is Version { return record(v) && strings(v, ['id', 'effective_from', 'gxp_classification', 'criticality', 'change_reason']) && nullableString(v.effective_to) && integer(v.version_number) && Array.isArray(v.rules) && v.rules.every(isRule); }
function isCandidate(v: unknown): v is Candidate { return record(v) && strings(v, ['policy_id','policy_key','policy_name','policy_version_id','effective_from']) && integer(v.version_number) && nullableString(v.effective_to); }
async function request(path: string, signal: AbortSignal): Promise<unknown> {
  let response: Response;
  try { response = await fetch(`${baseUrl}/api/v1${path}`, { credentials: 'include', cache: 'no-store', signal: AbortSignal.any([signal, AbortSignal.timeout(requestTimeout)]) }); }
  catch (error) { if (signal.aborted) throw error; throw new PolicyError('Policy data could not be reached. Please try again.'); }
  if (!response.ok) {
    if (response.status === 401) window.dispatchEvent(new Event('assurgrid-session-expired'));
    throw new PolicyError(response.status === 403 ? 'Policy administration is available to Admin and Quality roles.' :
      response.status === 404 ? 'This policy or application was not found in your authorized scope.' :
      response.status === 422 ? 'The policy date or address is invalid.' :
      response.status === 401 ? 'Your session has ended. Please sign in again.' : 'Policy configuration is unavailable. Please try again.', response.status);
  }
  try { return await response.json(); } catch { throw new PolicyError('The API returned unexpected policy data.'); }
}
export async function getPolicies(page: number, signal: AbortSignal): Promise<PolicyPage> {
  const v = await request(`/policies?page=${page}&page_size=20`, signal);
  if (record(v) && Array.isArray(v.items) && v.items.every(isPolicy) && integer(v.page) && integer(v.page_size) && typeof v.has_more === 'boolean') return { items: v.items, page: v.page, page_size: v.page_size, has_more: v.has_more };
  throw new PolicyError('The API returned unexpected policy data.');
}
export async function getHistory(id: string, signal: AbortSignal): Promise<History> {
  const v = await request(`/policies/${encodeURIComponent(id)}`, signal);
  if (isPolicy(v) && record(v) && Array.isArray(v.versions) && v.versions.every(isVersion)) return { id: v.id, name: v.name, policy_key: v.policy_key, versions: v.versions };
  throw new PolicyError('The API returned unexpected policy data.');
}
export async function getResolution(id: string, day: string, signal: AbortSignal): Promise<Resolution> {
  const v = await request(`/applications/${encodeURIComponent(id)}/policy?as_of=${encodeURIComponent(day)}`, signal);
  if (record(v) && strings(v, ['application_id','as_of','timezone','explanation']) &&
      (v.configuration === 'Resolved' || v.configuration === 'Missing Configuration' || v.configuration === 'Conflicting Configuration') && Array.isArray(v.candidates) && v.candidates.every(isCandidate) && Array.isArray(v.rules) && v.rules.every(isRule)) {
    return { application_id: v.application_id as string, as_of: v.as_of as string, timezone: v.timezone as string, explanation: v.explanation as string, configuration: v.configuration, candidates: v.candidates, rules: v.rules };
  }
  throw new PolicyError('The API returned unexpected policy data.');
}
