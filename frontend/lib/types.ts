export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  email_verified: boolean;
}

export interface MyOrganization {
  id: number;
  name: string;
  role: string;
}

export interface Chatbot {
  id: number;
  organization_id: number;
  name: string;
  public_widget_id: string;
  welcome_message: string | null;
  system_prompt: string | null;
  is_active: boolean;
  branding: Record<string, unknown> | null;
  allowed_domains: string[] | null;
  created_at: string;
  updated_at: string;
}

export type ProcessingStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed";

export interface KnowledgeSource {
  id: number;
  organization_id: number;
  chatbot_id: number | null;
  title: string;
  original_filename: string;
  file_size: number;
  content_type: string | null;
  processing_status: ProcessingStatus;
  chunk_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export type ConversationStatus =
  | "active"
  | "waiting_human"
  | "human"
  | "closed";

export interface Conversation {
  id: number;
  public_id: string;
  customer_identifier: string;
  status: ConversationStatus;
  chatbot_id: number;
  assigned_agent_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface AgentMessage {
  id: number;
  sender_type: "customer" | "ai" | "agent" | "system";
  content: string;
  is_internal: boolean;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: AgentMessage[];
}
