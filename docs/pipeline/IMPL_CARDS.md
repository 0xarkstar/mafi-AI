# Implementation Report: Player Cards Visual Polish

**Agent**: p-impl-cards
**Team**: visual-polish
**Date**: 2026-02-16

## Summary

Successfully rewrote PlayerCard.tsx with full portrait images, chat bubbles, emote animations, and vote overlay. Updated GameBoard.tsx to wire new store props, and created EmoteMenu.tsx component.

## Files Modified

### 1. PlayerCard.tsx (~180 lines)
**Status**: ✅ COMPLETE REWRITE

**New Features**:
- **Portrait Images**: Full card-size avatar images using `AVATAR_IMAGES[avatarIndex]`
- **Chat Bubbles**: AnimatePresence with gold-bordered speech bubbles above cards, fade in/out
- **Emote Overlay**: Spring animation (scale 0.5→1.2), positioned top-right, glow drop-shadow
- **Vote Overlay**: Red hover overlay with Target icon (only when `showVoteUI && isAlive`)
- **Vote Count Badge**: Red pill badge top-right with scale-in animation
- **Speaking Glow**: Gold border with shadow when `isSpeaking && isAlive`
- **Role Badge**: Colored circle with icon (Sword/Eye/Shield) top-left
- **Dead Overlay**: Black/50 with backdrop-blur + Skull icon

**Implementation Details**:
- Used GlassCard wrapper with click handler div (GlassCard doesn't support onClick directly)
- Bottom gradient overlay for text readability
- Proper z-index layering: chat bubble (60) → emote (70) → vote hover (20) → badges (30)
- All animations use framer-motion with spring physics
- Removed old PlayerAvatar CSS-art component

**Props Interface**:
```typescript
interface PlayerCardProps {
  player: Player
  chatMessage?: string         // from chatBubbles[player.name]
  activeEmote?: string         // from activeEmotes[player.name]?.emoji
  votesReceived?: number       // from voteCounts[player.name]
  showVoteUI?: boolean         // from store
  onVote?: (name: string) => void
}
```

### 2. GameBoard.tsx (~90 lines)
**Status**: ✅ UPDATED

**Changes**:
- Wire up store selectors: `chatBubbles`, `voteCounts`, `activeEmotes`, `showVoteUI`, `setSelectedVoteTarget`
- Pass new props to all PlayerCard instances (desktop 4+3 grid, mobile 3+2+2 grid)
- Added `@ts-expect-error` comments for store fields being added by p-impl-enhance concurrently
- Uses optional chaining (`??`) for safe fallbacks

**Store Dependencies** (added by p-impl-enhance):
- `chatBubbles: Record<string, string>`
- `voteCounts: Record<string, number>`
- `showVoteUI: boolean`
- `selectedVoteTarget: string | null`
- `setSelectedVoteTarget: (target: string | null) => void`
- `activeEmotes` (already exists)

### 3. EmoteMenu.tsx (~50 lines)
**Status**: ✅ CREATED NEW

**Features**:
- AnimatePresence with backdrop + menu overlay
- 8 emotes in 4x4 grid: 👍 👎 😂 😡 🤔 😱 👻 💀
- Positioned `bottom-full` (above trigger)
- Glassmorphism styling (bg-[#1e293b]/95 + backdrop-blur-xl)
- Hover states + active scale animation
- Click outside to close

**Props Interface**:
```typescript
interface EmoteMenuProps {
  isOpen: boolean
  onSelect: (emote: string) => void
  onClose: () => void
}
```

## Verification

### TypeScript Compilation
```bash
cd /Users/arkstar/Projects/mafia-ai/frontend && npx tsc --noEmit
```
✅ **PASS** — No errors in PlayerCard.tsx, GameBoard.tsx, or EmoteMenu.tsx

### Code Quality
- ✅ Immutability: No mutations, all React best practices
- ✅ File Size: PlayerCard ~180 lines, GameBoard ~90 lines, EmoteMenu ~50 lines (all within limits)
- ✅ Imports: All Lucide icons, framer-motion, constants properly imported
- ✅ Accessibility: Click handlers, hover states, semantic HTML

## Branch Reference

Ported features from `MAFI_AI_FRONT` branch `GamePlayerCard` component:
- ✅ Full card avatar images
- ✅ Chat bubble with AnimatePresence and pointer arrow
- ✅ Emote overlay with spring animation
- ✅ Vote hover overlay with Target icon
- ✅ Vote count badge with scale-in animation
- ✅ Speaking glow effect
- ✅ Role badge with colored icons
- ✅ Dead overlay with backdrop-blur

## Handoff

### Attempted
- Rewrote PlayerCard.tsx with portrait images, chat bubbles, emotes, vote UI
- Updated GameBoard.tsx to wire store props
- Created EmoteMenu.tsx component
- Verified TypeScript compilation

### Worked
- ✅ All visual features implemented as specified
- ✅ TypeScript compilation clean (no errors in owned files)
- ✅ Proper framer-motion animations (spring physics, AnimatePresence)
- ✅ Z-index layering correct (chat bubble above card, emote above chat)
- ✅ Store integration ready (uses optional chaining for concurrent store updates)
- ✅ GlassCard wrapper pattern (click handler on outer div)

### Failed
- None. All implementation goals achieved.

### Remaining
- **EmoteMenu Integration**: EmoteMenu.tsx component created but not yet integrated into any parent component (e.g., GameBoard, PlayerCard). The component is ready to use but needs a trigger button and state management.
- **Store Fields**: TypeScript shows `@ts-expect-error` for store fields (`chatBubbles`, `voteCounts`, `showVoteUI`, `setSelectedVoteTarget`) — these will be resolved when p-impl-enhance completes.
- **WebSocket Wiring**: Chat bubbles and vote counts need WebSocket events to populate (handled by p-impl-enhance).
- **Testing**: No tests written (out of scope for this task).

### Notes for Next Phase
- EmoteMenu.tsx needs to be integrated with a trigger button (suggestion: add to PlayerCard or GameBoard)
- Once p-impl-enhance completes, remove `@ts-expect-error` comments from GameBoard.tsx
- Consider adding keyboard shortcuts for emote selection (accessibility)
- Vote overlay might need adjustment based on UX testing (Target icon size, hover opacity)
