// GENERATED FILE - do not edit by hand.
// Regenerate:  cd backend && python scripts/gen_frontend_types.py
// Source of truth: shared-contracts/schema.json -> properties.status.enum
//
// Import these instead of retyping the strings. A typo in a status literal does
// not throw anywhere - the Kanban column just silently renders empty, and
// ?status= filtering just silently returns nothing.
export const CANDIDATE_STATUSES = [
  "New",
  "Review",
  "Needs information",
  "CV passed",
  "Assessment",
  "Interview",
  "Hired",
  "Rejected",
  "Archived",
] as const;

export type CandidateStatus = (typeof CANDIDATE_STATUSES)[number];

export const DEFAULT_CANDIDATE_STATUS: CandidateStatus = "New";

/**
 * Statuses that count as "rejected". Convention: any status ending in
 * "rejected". `before_rejected_status` holds the stage the candidate was at
 * when they entered one of these, and POST /api/candidates/{id}/restore moves
 * them back to it.
 */
export const REJECTED_STATUSES: readonly CandidateStatus[] = [
  "Rejected",
];

export function isRejected(status: string): status is CandidateStatus {
  return (REJECTED_STATUSES as readonly string[]).includes(status);
}

// File/extraction lifecycle - SEPARATE from the HR pipeline status above.
// The delete/cancel button keys off this one; the dashboard badge keys off `status`.
export const UPLOAD_STATUSES = [
  "Not Uploaded",
  "Processing",
  "Done",
  "Failed",
] as const;

export type UploadStatus = (typeof UPLOAD_STATUSES)[number];

// Account roles - shared-contracts/hr-account-schema.json
export const ACCOUNT_ROLES = ["admin", "hr", "line_manager", "viewer"] as const;
export type AccountRole = (typeof ACCOUNT_ROLES)[number];

// Comment types - shared-contracts/comment-log-schema.json
export const COMMENT_TYPES = ["hr", "line_manager", "interview", "general"] as const;
export type CommentType = (typeof COMMENT_TYPES)[number];
