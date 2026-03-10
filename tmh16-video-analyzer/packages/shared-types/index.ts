export type EvidenceStatus = 'complete' | 'incomplete' | 'review_required' | 'not_observed' | 'not_applicable';

export interface TMH16Card {
  topic: string;
  status: EvidenceStatus;
  note: string;
}
