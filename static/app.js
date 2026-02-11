// WebSocket connection and game state management
const AGENTS = ['Viktor', 'Luna', 'Rex', 'Sage', 'Nova', 'Iris', 'Blaze'];
const AGENT_COLORS = {
    Viktor: '#3b82f6',
    Luna: '#ec4899',
    Rex: '#ef4444',
    Sage: '#a855f7',
    Nova: '#f59e0b',
    Iris: '#06b6d4',
    Blaze: '#f97316'
};

let ws = null;
let gameState = {
    phase: 'lobby',
    alive: new Set(AGENTS),
    round: 0,
    votes: {}
};
let selectedBetAmount = 50;
let chipBalance = 1000;
let isPlayer = false;
let myPlayerName = null;

/**
 * Initialize WebSocket connection with auto-reconnect
 */
function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => {
        console.log('WebSocket connected');
        updateStatus('Connected', true);
        initAgentCards();
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('Received event:', data);
            handleEvent(data);
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('Connection error', false);
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateStatus('Disconnected - Reconnecting...', false);
        // Auto-reconnect after 2 seconds
        setTimeout(connect, 2000);
    };
}

/**
 * Update connection status badge
 */
function updateStatus(message, isConnected) {
    const statusEl = document.getElementById('game-status');
    statusEl.textContent = message;
    statusEl.style.borderColor = isConnected ? '#00ff88' : '#ff4444';
    statusEl.style.background = isConnected
        ? 'rgba(0, 255, 136, 0.1)'
        : 'rgba(255, 68, 68, 0.1)';
}

/**
 * Initialize agent cards on the board
 */
function initAgentCards() {
    const container = document.getElementById('agent-cards');
    container.innerHTML = '';

    AGENTS.forEach(name => {
        const card = document.createElement('div');
        card.className = 'agent-card';
        card.id = `agent-${name}`;
        card.innerHTML = `
            <div class="agent-name" style="color: ${AGENT_COLORS[name]}">${name}</div>
            <div class="agent-trait"></div>
            <div class="agent-role" style="display:none"></div>
            <div class="agent-status">Alive</div>
        `;
        container.appendChild(card);
    });
}

/**
 * Route incoming WebSocket events to handlers
 */
function handleEvent(event) {
    if (!event) {
        console.warn('Invalid event received:', event);
        return;
    }

    // Support both event_type (broadcast WSEvents) and type (direct responses)
    const eventType = event.event_type || event.type;
    if (!eventType) {
        console.warn('Invalid event received (no event_type or type):', event);
        return;
    }

    const handlers = {
        phase_change: handlePhaseChange,
        agent_message: handleAgentMessage,
        vote_cast: handleVoteCast,
        elimination: handleElimination,
        odds_update: handleOddsUpdate,
        game_over: handleGameOver,
        bet_placed: handleBetPlaced,
        bet_confirmed: handleBetConfirmed,
        bet_rejected: handleBetRejected,
        lobby_joined: handleLobbyJoined,
        lobby_status: handleLobbyStatus,
        game_starting: handleGameStarting,
        action_request: handleActionRequest,
        identity_reveal: handleIdentityReveal,
        pong: () => console.log('pong received')  // Handle pong silently
    };

    const handler = handlers[eventType];
    if (handler) {
        handler(event.data);
    } else {
        console.warn('Unknown event type:', eventType);
    }
}

/**
 * Handle phase change events
 */
function handlePhaseChange(data) {
    if (!data || !data.phase) {
        console.warn('Invalid phase_change data:', data);
        return;
    }

    gameState.phase = data.phase;
    gameState.round = data.round || 0;

    const banner = document.getElementById('phase-banner');
    const phaseText = document.getElementById('phase-text');

    // Remove old phase classes
    banner.className = '';
    banner.classList.add(data.phase);

    const phaseNames = {
        night: '🌙 NIGHT',
        day_discussion: '☀️ DAY DISCUSSION',
        day_vote: '🗳️ DAY VOTE',
        game_over: '🏆 GAME OVER'
    };

    const phaseName = phaseNames[data.phase] || data.phase.toUpperCase();
    phaseText.textContent = `${phaseName} — Round ${gameState.round}`;

    // Clear votes on new phase
    if (data.phase !== 'day_vote') {
        gameState.votes = {};
        document.getElementById('vote-list').innerHTML = '';
    }

    addSystemMessage(`Phase: ${phaseName} (Round ${gameState.round})`);
}

/**
 * Handle agent message events (chat/actions)
 */
function handleAgentMessage(data) {
    if (!data || !data.agent || !data.message) {
        console.warn('Invalid agent_message data:', data);
        return;
    }

    const { agent, message } = data;

    // Highlight speaking agent
    document.querySelectorAll('.agent-card').forEach(card => {
        card.classList.remove('speaking');
    });

    const card = document.getElementById(`agent-${agent}`);
    if (card) {
        card.classList.add('speaking');
        // Remove highlight after 3 seconds
        setTimeout(() => {
            card.classList.remove('speaking');
        }, 3000);
    }

    // Add message with typing animation
    addChatMessage(agent, message, true);
}

/**
 * Handle vote cast events
 */
function handleVoteCast(data) {
    if (!data || !data.voter || !data.target) {
        console.warn('Invalid vote_cast data:', data);
        return;
    }

    const { voter, target } = data;
    gameState.votes[voter] = target;

    const voteList = document.getElementById('vote-list');

    // Check if vote already exists and update it
    const existingVote = voteList.querySelector(`[data-voter="${voter}"]`);
    if (existingVote) {
        existingVote.remove();
    }

    const entry = document.createElement('div');
    entry.className = 'vote-entry';
    entry.dataset.voter = voter;
    entry.innerHTML = `
        <span style="color: ${AGENT_COLORS[voter]}">${voter}</span>
        <span>→</span>
        <span style="color: ${AGENT_COLORS[target]}">${target}</span>
    `;
    voteList.appendChild(entry);

    addSystemMessage(`${voter} votes for ${target}`);
}

/**
 * Handle elimination events
 */
function handleElimination(data) {
    if (!data || !data.agent) {
        console.warn('Invalid elimination data:', data);
        return;
    }

    const { agent, role, reason } = data;
    gameState.alive.delete(agent);

    // Mark card as dead
    const card = document.getElementById(`agent-${agent}`);
    if (card) {
        card.classList.add('dead');
        card.classList.remove('speaking');
        card.querySelector('.agent-status').textContent = '💀 Dead';

        if (role) {
            const roleDiv = card.querySelector('.agent-role');
            roleDiv.style.display = 'block';
            roleDiv.innerHTML = `<span class="role-badge ${role.toLowerCase()}">${role.toUpperCase()}</span>`;
        }
    }

    const reasonText = reason === 'killed_at_night' ? 'killed by the mafia' : 'voted out';
    const roleText = role ? ` (was ${role})` : '';
    addSystemMessage(`💀 ${agent} was ${reasonText}${roleText}!`, 'elimination');
}

/**
 * Handle odds update events (betting)
 */
function handleOddsUpdate(data) {
    if (!data) {
        console.warn('Invalid odds_update data:', data);
        return;
    }

    const display = document.getElementById('odds-display');

    if (data.mafia_win_prob !== undefined && data.citizen_win_prob !== undefined) {
        display.innerHTML = `
            <div class="odds-row" style="border-left-color: #ff4444">
                <span>😈 Mafia Win:</span>
                <strong class="odds-value">${(data.mafia_win_prob * 100).toFixed(1)}%</strong>
            </div>
            <div class="odds-row" style="border-left-color: #00ff88">
                <span>🎉 Citizens Win:</span>
                <strong class="odds-value">${(data.citizen_win_prob * 100).toFixed(1)}%</strong>
            </div>
        `;

        // Animate odds change
        document.querySelectorAll('.odds-value').forEach(el => {
            el.classList.add('pulse-once');
            setTimeout(() => el.classList.remove('pulse-once'), 600);
        });
    }
}

/**
 * Handle game over events
 */
function handleGameOver(data) {
    if (!data || !data.winner) {
        console.warn('Invalid game_over data:', data);
        return;
    }

    const { winner, rounds, alive_agents } = data;
    const banner = document.getElementById('phase-banner');
    banner.className = 'game_over';

    const emoji = winner === 'mafia' ? '😈' : '🎉';
    const winnerText = winner.toUpperCase();
    document.getElementById('phase-text').textContent =
        `${emoji} ${winnerText} WINS! (${rounds} rounds)`;

    addSystemMessage(`🏆 Game Over! ${winnerText} wins after ${rounds} rounds!`, 'game-over');

    if (alive_agents && alive_agents.length > 0) {
        addSystemMessage(`Survivors: ${alive_agents.join(', ')}`, 'game-over');
    }

    // Show claim button if blockchain mode
    if (typeof isBlockchainMode !== 'undefined' && isBlockchainMode) {
        document.getElementById('blockchain-claim').style.display = 'block';
    }
}

/**
 * Handle bet placed events
 */
function handleBetPlaced(data) {
    if (!data) {
        console.warn('Invalid bet_placed data:', data);
        return;
    }

    // Update chip balance if provided
    if (data.new_balance !== undefined) {
        chipBalance = data.new_balance;
        updateChipDisplay();
    }

    if (data.bet_type && data.amount) {
        addSystemMessage(`Bet placed: ${data.amount} chips on ${data.bet_type}`);
    }
}

/**
 * Handle bet confirmed events
 */
function handleBetConfirmed(data) {
    if (!data) {
        console.warn('Invalid bet_confirmed data:', data);
        return;
    }

    chipBalance = data.new_balance;
    updateChipDisplay();

    const targetName = data.target === 'mafia' ? '😈 Mafia' : '🎉 Citizens';
    addSystemMessage(`✅ Bet confirmed: ${data.amount} chips on ${targetName} (${data.weight}x weight)`, 'game-over');

    // Add to bet history
    addBetToHistory(data);
}

/**
 * Handle bet rejected events
 */
function handleBetRejected(data) {
    if (!data) {
        console.warn('Invalid bet_rejected data:', data);
        return;
    }

    if (data.balance !== undefined) {
        chipBalance = data.balance;
        updateChipDisplay();
    }

    addSystemMessage(`❌ Bet rejected: ${data.reason}`, 'elimination');
}

/**
 * Place a bet via WebSocket
 */
function placeBet(betType, target) {
    // On-chain betting if blockchain mode active and wallet connected
    if (typeof isBlockchainMode !== 'undefined' && isBlockchainMode && typeof contract !== 'undefined' && contract && typeof signer !== 'undefined' && signer) {
        const amount = selectedBetAmount === 'all' ? 0.1 : selectedBetAmount / 1000;
        const betMafia = target === 'mafia';
        placeBetOnChain(betMafia, amount);
        return;
    }

    // Fallback to WebSocket chip betting
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        addSystemMessage('❌ Not connected to server', 'elimination');
        return;
    }

    const amount = selectedBetAmount === 'all' ? chipBalance : selectedBetAmount;

    if (amount > chipBalance) {
        addSystemMessage('❌ Insufficient chips', 'elimination');
        return;
    }

    ws.send(JSON.stringify({
        type: 'place_bet',
        bet_type: betType,
        target: target,
        amount: amount,
        round: gameState.round
    }));

    console.log('Bet sent:', { betType, target, amount, round: gameState.round });
}

/**
 * Select bet amount
 */
function selectBetAmount(amount) {
    selectedBetAmount = amount;

    // Update button states
    document.querySelectorAll('.bet-amount').forEach(btn => {
        btn.classList.remove('selected');
    });

    const selectedBtn = document.querySelector(`.bet-amount[data-amount="${amount}"]`);
    if (selectedBtn) {
        selectedBtn.classList.add('selected');
    }
}

/**
 * Update chip balance display
 */
function updateChipDisplay() {
    document.getElementById('chip-balance').textContent = `💰 ${chipBalance} chips`;
}

/**
 * Add bet to history display
 */
function addBetToHistory(bet) {
    const history = document.getElementById('bet-history');
    const entry = document.createElement('div');
    entry.className = 'bet-history-entry';
    entry.innerHTML = `
        <span>${bet.amount} chips</span>
        <span>→</span>
        <span>${bet.target === 'mafia' ? '😈' : '🎉'} ${bet.target}</span>
    `;
    history.appendChild(entry);

    // Keep only last 5 bets
    while (history.children.length > 5) {
        history.removeChild(history.firstChild);
    }
}

/**
 * Add a chat message with optional typing animation
 */
function addChatMessage(agent, message, animate = false) {
    const log = document.getElementById('chat-log');
    const div = document.createElement('div');
    div.className = 'chat-message';
    div.style.borderLeftColor = AGENT_COLORS[agent] || '#333';

    const nameSpan = `<strong style="color: ${AGENT_COLORS[agent]}">${agent}:</strong>`;

    if (animate) {
        div.innerHTML = `${nameSpan} <span class="msg-text"></span><span class="typing-cursor"></span>`;
        log.appendChild(div);
        log.scrollTop = log.scrollHeight;

        // Typing animation
        const textSpan = div.querySelector('.msg-text');
        const cursor = div.querySelector('.typing-cursor');
        let i = 0;
        const typingSpeed = Math.max(10, Math.min(30, 1000 / message.length)); // Adaptive speed

        const interval = setInterval(() => {
            if (i < message.length) {
                textSpan.textContent += message[i];
                i++;
                log.scrollTop = log.scrollHeight;
            } else {
                clearInterval(interval);
                if (cursor) cursor.remove();
            }
        }, typingSpeed);
    } else {
        div.innerHTML = `${nameSpan} ${escapeHtml(message)}`;
        log.appendChild(div);
        log.scrollTop = log.scrollHeight;
    }
}

/**
 * Add a system message to the chat log
 */
function addSystemMessage(text, type = '') {
    const log = document.getElementById('chat-log');
    const div = document.createElement('div');
    div.className = `chat-message system ${type}`;
    div.style.borderLeftColor = type === 'elimination' ? '#ff4444' :
                                 type === 'game-over' ? '#00ff88' : '#8b5cf6';
    div.innerHTML = `<em>${escapeHtml(text)}</em>`;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Join lobby as human player
 */
function joinLobby() {
    const nameInput = document.getElementById('player-name-input');
    const name = nameInput.value.trim();
    if (!name) {
        alert('Please enter your name');
        return;
    }
    ws.send(JSON.stringify({ type: 'join_lobby', name }));
}

/**
 * Submit action response
 */
function submitAction() {
    const statementInput = document.getElementById('statement-input');
    const voteSelect = document.getElementById('vote-select');
    let response = '';

    if (statementInput.style.display !== 'none') {
        response = statementInput.value.trim();
    } else if (voteSelect.style.display !== 'none') {
        const selectEl = voteSelect.querySelector('select');
        response = selectEl ? selectEl.value : '';
    }

    if (!response) {
        alert('Please provide a response');
        return;
    }

    ws.send(JSON.stringify({
        type: 'action_response',
        player_name: myPlayerName,
        response
    }));

    // Hide action input
    document.getElementById('action-input-section').style.display = 'none';
    statementInput.value = '';
}

/**
 * Handle lobby joined response
 */
function handleLobbyJoined(data) {
    if (!data || !data.name) return;

    if (data.success) {
        isPlayer = true;
        myPlayerName = data.name;

        // Hide lobby controls
        document.getElementById('lobby-controls').style.display = 'none';

        // Show joined message
        const lobbyStatus = document.getElementById('lobby-status');
        lobbyStatus.textContent = `Joined as ${data.name}`;
        lobbyStatus.style.color = '#00ff88';

        addSystemMessage(`You joined the lobby as ${data.name}`);
    } else {
        alert('Failed to join lobby');
    }
}

/**
 * Handle lobby status update
 */
function handleLobbyStatus(data) {
    if (!data) return;

    const players = data.players || [];
    const count = data.count || 0;
    const ready = data.ready || false;

    // Update lobby players display
    const lobbyPlayers = document.getElementById('lobby-players');
    lobbyPlayers.innerHTML = players.map(name =>
        `<div class="lobby-player-card">${name}</div>`
    ).join('');

    // Update status
    if (!isPlayer) {
        const lobbyStatus = document.getElementById('lobby-status');
        lobbyStatus.textContent = `Waiting for players... (${count}/7)`;
        if (ready) {
            lobbyStatus.textContent = 'Lobby full! Game starting soon...';
            lobbyStatus.style.color = '#00ff88';
        }
    }
}

/**
 * Handle game starting event
 */
function handleGameStarting(data) {
    // Hide lobby section
    document.getElementById('lobby-section').style.display = 'none';

    // Show game UI
    document.querySelector('main').style.display = 'grid';

    addSystemMessage('Game is starting!', 'game-over');
}

/**
 * Handle action request for human player
 */
function handleActionRequest(data) {
    if (!data || !isPlayer) return;

    const actionSection = document.getElementById('action-input-section');
    const promptEl = document.getElementById('action-prompt');
    const statementInput = document.getElementById('statement-input');
    const voteSelect = document.getElementById('vote-select');
    const timerEl = document.getElementById('action-timer');

    promptEl.textContent = data.prompt || 'Your action required';

    if (data.action_type === 'statement') {
        statementInput.style.display = 'block';
        voteSelect.style.display = 'none';
    } else if (data.action_type === 'vote') {
        statementInput.style.display = 'none';
        voteSelect.style.display = 'block';

        // Build vote dropdown
        const options = data.options || [];
        voteSelect.innerHTML = `
            <select>
                ${options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
            </select>
        `;
    }

    // Show timer
    const timeout = data.timeout || 60;
    timerEl.textContent = `${timeout}s`;
    let remaining = timeout;
    const timerId = setInterval(() => {
        remaining--;
        timerEl.textContent = `${remaining}s`;
        if (remaining <= 0) {
            clearInterval(timerId);
            // Auto-submit empty response
            submitAction();
        }
    }, 1000);

    actionSection.style.display = 'block';
}

/**
 * Handle identity reveal event
 */
function handleIdentityReveal(data) {
    if (!data || !data.player_name) return;

    const revealSection = document.getElementById('reveal-section');
    const revealCards = document.getElementById('reveal-cards');

    revealSection.style.display = 'block';

    const card = document.createElement('div');
    card.className = `reveal-card ${data.player_type || 'ai'}`;
    card.innerHTML = `
        <div class="reveal-name">${data.player_name}</div>
        <div class="reveal-type">${data.player_type === 'human' ? '👤 Human' : '🤖 AI'}</div>
        <div class="reveal-role">${data.role || 'Unknown'}</div>
    `;
    revealCards.appendChild(card);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('MafiaAI Dashboard initializing...');
    connect();

    // Setup bet amount selectors
    document.querySelectorAll('.bet-amount').forEach(btn => {
        btn.addEventListener('click', () => {
            const amount = btn.dataset.amount;
            selectBetAmount(amount === 'all' ? 'all' : parseInt(amount));
        });
    });

    // Select default amount (50)
    selectBetAmount(50);

    // Initialize blockchain if server provides config
    fetch('/api/blockchain-config')
        .then(r => r.json())
        .then(config => {
            if (config.enabled && config.contract_address) {
                initBlockchain(config.contract_address, config.game_id);
            }
        })
        .catch(() => console.log('Blockchain config not available — using chip betting'));
});
