export type UserRole = 'staff' | 'approver-level-1' | 'approver-level-2' | 'finance';

export type RequestStatus = 'pending' | 'approved' | 'rejected';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
}

export interface PurchaseRequest {
  id: string;
  title: string;
  description: string;
  amount: number;
  status: RequestStatus;
  created_by: string;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
  proforma?: string;
  purchase_order?: string;
  receipt?: string;
  approvals: Approval[];
}

export interface Approval {
  id: string;
  request_id: string;
  approver_id: string;
  approver_name: string;
  approver_level: 1 | 2;
  status: 'pending' | 'approved' | 'rejected';
  comment?: string;
  created_at: string;
}

export interface DocumentValidation {
  is_valid: boolean;
  discrepancies: string[];
  vendor_match: boolean;
  items_match: boolean;
  price_match: boolean;
}

export interface CreateRequestPayload {
  title: string;
  description: string;
  amount: number;
  proforma: File;
}

export interface UpdateRequestPayload {
  title?: string;
  description?: string;
  amount?: number;
}

export interface ApprovalPayload {
  comment?: string;
}
