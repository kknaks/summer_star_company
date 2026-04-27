// 백엔드 Pydantic 스키마와 1:1 대응.
// 백엔드 SSOT: docs/spec/backend-api.

export interface UserPublic {
  id: string;
  name: string;
  role: string;
}

export interface User extends UserPublic {
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserListItem extends User {
  card_count: number;
  last_access_at: string | null;
}

export interface Card {
  id: string;
  uid: string;
  user_id: string;
  label: string | null;
  active: boolean;
  registered_at: string;
  created_at: string;
  updated_at: string;
}

export interface AccessLog {
  id: number;
  occurred_at: string;
  received_at: string;
  uid: string;
  card_id: string | null;
  user_id: string | null;
  allowed: boolean;
}

export interface AccessLogList {
  items: AccessLog[];
  next_cursor: string | null;
}

export interface DailyStat {
  date: string;
  first_in: string;
  last_out: string;
  duration_minutes: number;
}

export interface MonthlyStat {
  month: string;
  work_days: number;
  avg_first_in: string;
  avg_last_out: string;
  avg_duration_minutes: number;
}

export interface LoginResponse {
  token: string;
  user: UserPublic;
}
