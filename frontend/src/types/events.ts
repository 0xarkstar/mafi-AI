// Server → Client events (discriminated union on "type" field)
export type ServerEvent =
  | { type: 'lobby_status'; data: { players: Array<{ name: string; player_type: string; avatar_index?: number }>; player_count: number; max_players: number } }
  | { type: 'lobby_joined'; data: { name: string; success: boolean; game_id?: string; players: string[] } }
  | { type: 'game_starting'; data: { game_id?: string; player_count: number; players: Array<{ name: string; player_type: string }> } }
  | { type: 'phase_change'; data: { phase: string; round: number; alive_agents: string[] } }
  | { type: 'agent_message'; data: { agent: string; message: string; statement_num: number } }
  | { type: 'vote_cast'; data: { voter: string; target: string } }
  | { type: 'elimination'; data: { agent: string; role?: string; reason: string; votes?: number } }
  | { type: 'game_over'; data: { winner: string; rounds: number; alive_agents: string[]; payouts: Record<string, number> } }
  | { type: 'identity_reveal'; data: { player_name: string; name: string; player_type: string; role: string; all_revealed: boolean } }
  | { type: 'odds_update'; data: { mafia_win_prob: number; citizen_win_prob: number; mafia_suspects: Record<string, number> } }
  | { type: 'balance_update'; data: { balance: number } }
  | { type: 'bet_confirmed'; data: { bet_id: string; bet_type: string; target: string; amount_usdc: number; balance?: number } }
  | { type: 'bet_rejected'; data: { reason: string } }
  | { type: 'action_request'; data: { player_name: string; action_type: string; prompt: string; options?: string[]; timeout: number; context?: Record<string, unknown> } }
  | { type: 'usdc_settlement'; data: { bet_id: string; won: boolean; payout: number } }
  | { type: 'new_lobby'; data: { message: string } }
  | { type: 'spec_chat_joined'; data: { name: string } }
  | { type: 'spec_chat_error'; data: { reason: string } }
  | { type: 'pong' }
  | { type: 'error'; message: string }
  // Broadcast event format (event_type instead of type)
  | { event_type: string; data: unknown; game_id?: string; timestamp?: string };

// Client → Server events
export type ClientEvent =
  | { type: 'join_lobby'; name: string; avatar_index?: number; wallet_address?: string }
  | { type: 'rejoin_lobby'; name: string; avatar_index?: number | null }
  | { type: 'action_response'; player_name: string; response: string }
  | { type: 'place_bet'; bet_type: string; target: string; amount_usdc: number; bet_id?: string; round?: number; wallet_address?: string }
  | { type: 'join_spec_chat'; name?: string }
  | { type: 'spec_chat'; text: string }
  | { type: 'register_wallet'; wallet_address: string }
  | { type: 'ping' };
