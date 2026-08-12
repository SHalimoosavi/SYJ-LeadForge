/**
 * Types mirroring `backend/schemas.py` field-for-field, so the dashboard
 * stays a faithful client of the API rather than inventing its own shape
 * for the same data.
 */

export interface Business {
  id: number;
  name: string;
  category: string;
  city: string;
  state: string;
  country: string;
  phone: string;
  website: string;
  rating: number;
  review_count: number;
  notes: string;
}

export interface AuditResult {
  business_id: number;
  url: string;
  reachable: boolean;
  status_code: number | null;
  https: boolean;
  response_time_ms: number | null;
  redirect_count: number;
  has_title: boolean;
  has_meta_description: boolean;
  has_viewport_meta: boolean;
  has_favicon: boolean;
  has_h1: boolean;
  image_count: number;
  images_missing_alt: number;
  has_whatsapp_link: boolean;
  has_contact_info: boolean;
  has_ssl_valid: boolean;
  html_lang_present: boolean;
  error: string;
  performance_score: number;
  design_score: number;
  seo_score: number;
  accessibility_score: number;
  trust_score: number;
  overall_score: number;
  issues: string[];
}

export type Tier = 'Excluded' | 'Very Low' | 'Low' | 'Medium' | 'High' | 'Very High';

export interface LeadScore {
  business_id: number;
  opportunity_score: number;
  stars: number;
  estimated_value_low: number;
  estimated_value_high: number;
  currency: string;
  tier: Tier;
  reasons: string[];
}

export interface Lead {
  id: number;
  name: string;
  category: string;
  city: string;
  state: string;
  country: string;
  phone: string;
  website: string;
  rating: number;
  review_count: number;
  score: LeadScore | null;
  audit: AuditResult | null;
}

export interface ImportResult {
  imported: number;
  businesses: Business[];
}

export interface AuditRunResult {
  audited: number;
  results: AuditResult[];
}

export interface ScoreRunResult {
  scored: number;
  results: LeadScore[];
}

export interface Stats {
  total_businesses: number;
  audited: number;
  scored: number;
  tier_breakdown: Record<string, number>;
  average_score: number;
}

export const TIER_ORDER: Tier[] = ['Very High', 'High', 'Medium', 'Low', 'Very Low', 'Excluded'];
