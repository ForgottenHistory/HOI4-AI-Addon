// HOI4 Twitter Feed - Live Stream Integration

class TwitterFeed {
    constructor() {
        this.container = document.getElementById('tweetsContainer');
        this.tweets = [];
        this.maxTweets = 5;
        this.isDebugMode = false;
        this.eventQueue = [];
        this.isProcessing = false;
        this.lastServerUpdate = 0;
        
        // Initialize
        this.init();
        this.startPolling();
    }

    init() {
        // Check if debug mode should be enabled (you can toggle this)
        const urlParams = new URLSearchParams(window.location.search);
        this.isDebugMode = urlParams.get('debug') === 'true';
        
        if (this.isDebugMode) {
            document.body.classList.add('debug');
            console.log('Debug mode enabled');
        }

        // Load initial tweets
        this.loadSampleTweets();
    }

    startPolling() {
        // Poll for new game data every 10 seconds
        setInterval(() => {
            this.checkForUpdates();
        }, 10000);
    }

    async checkForUpdates() {
        try {
            // Check for new tweets from server
            const response = await fetch('/api/tweets');
            if (response.ok) {
                const data = await response.json();
                this.updateFromServer(data);
                return;
            }
            
            // Fallback: try to get game data directly
            const gameResponse = await fetch('/api/game_data');
            if (gameResponse.ok) {
                const gameData = await gameResponse.json();
                if (gameData.success && this.isDebugMode) {
                    console.log('Found game data from server');
                }
                return;
            }
            
            if (this.isDebugMode) {
                console.log('No server connection, using local mode');
            }
        } catch (error) {
            if (this.isDebugMode) {
                console.log('Error checking for updates:', error);
            }
        }
    }

    updateFromServer(serverData) {
        // Update tweets if server has newer data
        if (serverData.last_update > this.lastServerUpdate) {
            this.lastServerUpdate = serverData.last_update;
            
            // Clear current tweets and update with server data
            this.container.innerHTML = '';
            this.tweets = [];
            
            // Add tweets from server (server sends newest first, so newest is at index 0)
            // Render them in reverse order so newest ends up at top
            for (let i = serverData.tweets.length - 1; i >= 0; i--) {
                const tweet = serverData.tweets[i];
                this.tweets.push(tweet);
                this.renderTweetAtTop(tweet);
            }
            
            if (this.isDebugMode) {
                console.log(`Updated with ${serverData.tweets.length} tweets from server`);
            }
        }
    }

    processGameData(gameData) {
        // Process recent events and generate tweets
        if (gameData.metadata && gameData.metadata.recent_events) {
            const recentEvents = gameData.metadata.recent_events;
            
            // Check for new events since last update
            recentEvents.forEach(event => {
                if (!this.hasProcessedEvent(event)) {
                    this.generateTweetFromEvent(event);
                }
            });
        }
    }

    hasProcessedEvent(event) {
        // Simple check based on event content
        return this.tweets.some(tweet => 
            tweet.content.includes(event.title) || 
            tweet.eventId === event.id
        );
    }

    async generateTweetFromEvent(event) {
        // This would normally call your AI service
        // For now, we'll generate contextual tweets based on event type
        const tweetData = this.createTweetFromEvent(event);
        this.addTweet(tweetData);
    }

    createTweetFromEvent(event) {
        const eventType = this.categorizeEvent(event);
        const personas = this.getPersonasForEvent(eventType);
        const selectedPersona = personas[Math.floor(Math.random() * personas.length)];
        
        return {
            id: Date.now() + Math.random(),
            eventId: event.id,
            username: selectedPersona.username,
            handle: selectedPersona.handle,
            avatar: selectedPersona.avatar,
            country: selectedPersona.country,
            content: this.generateTweetContent(event, selectedPersona),
            timestamp: this.getRelativeTime(new Date()),
            isBreaking: eventType === 'war' || eventType === 'crisis'
        };
    }

    categorizeEvent(event) {
        const title = event.title.toLowerCase();
        
        if (title.includes('war') || title.includes('attack') || title.includes('invade')) {
            return 'war';
        }
        if (title.includes('focus') || title.includes('research')) {
            return 'policy';
        }
        if (title.includes('election') || title.includes('government')) {
            return 'politics';
        }
        if (title.includes('crisis') || title.includes('tension')) {
            return 'crisis';
        }
        
        return 'general';
    }

    getPersonasForEvent(eventType) {
        const personas = {
            war: [
                { username: 'Adolf Hitler', handle: '@GermanChancellor', avatar: 'leader', country: 'ger' },
                { username: 'Winston Churchill', handle: '@WChurchill_MP', avatar: 'leader', country: 'eng' },
                { username: 'Joseph Stalin', handle: '@SovietLeader', avatar: 'leader', country: 'sov' },
                { username: 'War Correspondent', handle: '@FrontlineNews', avatar: 'journalist', country: null }
            ],
            policy: [
                { username: 'Rudolf Hess', handle: '@DeputyFuhrer', avatar: 'diplomat', country: 'ger' },
                { username: 'Anthony Eden', handle: '@ForeignSec', avatar: 'diplomat', country: 'eng' },
                { username: 'Cordell Hull', handle: '@StateSecretary', avatar: 'diplomat', country: 'usa' }
            ],
            politics: [
                { username: 'Franklin D. Roosevelt', handle: '@POTUS_FDR', avatar: 'leader', country: 'usa' },
                { username: 'Political Analyst', handle: '@PolAnalyst36', avatar: 'journalist', country: null }
            ],
            crisis: [
                { username: 'League Observer', handle: '@LeagueWatch', avatar: 'diplomat', country: null },
                { username: 'European Correspondent', handle: '@EuropeNews', avatar: 'journalist', country: null }
            ],
            general: [
                { username: 'World News Today', handle: '@WorldNews1936', avatar: 'journalist', country: null },
                { username: 'Concerned Citizen', handle: '@WarriedEuropean', avatar: 'citizen', country: null }
            ]
        };

        return personas[eventType] || personas.general;
    }

    generateTweetContent(event, persona) {
        const templates = {
            war: [
                `The situation in ${this.extractLocation(event)} grows more serious by the hour. The world watches with grave concern. #WorldWar #${this.extractHashtag(event)}`,
                `Military movements reported across Europe. This correspondent has never seen tensions this high. #BreakingNews #Europe1936`,
                `Our intelligence suggests significant developments are imminent. The people must be prepared. #NationalSecurity`
            ],
            policy: [
                `New policy initiatives announced today will shape our nation's future. The people deserve transparency in these decisions. #Policy #Leadership`,
                `Diplomatic channels remain open, but patience is not infinite. We stand ready to defend our interests. #Diplomacy`,
                `The focus on ${this.extractFocus(event)} demonstrates our commitment to national priorities. #Progress #Future`
            ],
            politics: [
                `Democracy faces its greatest test in these turbulent times. We must remain united in our values. #Democracy #Unity`,
                `The political landscape shifts daily. Citizens must stay informed and engaged. #Politics #1936Election`
            ],
            crisis: [
                `🚨 URGENT: Reports coming in of ${this.extractCrisisDetails(event)}. Situation developing rapidly. #BreakingNews #Crisis`,
                `The international community must respond to these developments with measured but decisive action. #WorldAffairs`
            ],
            general: [
                `Another day brings new challenges to our troubled world. When will sanity prevail? #WorldPeace #1936`,
                `The common people suffer while leaders play their games of power. Enough is enough. #Peace #CommonSense`
            ]
        };

        const eventType = this.categorizeEvent(event);
        const availableTemplates = templates[eventType] || templates.general;
        return availableTemplates[Math.floor(Math.random() * availableTemplates.length)];
    }

    extractLocation(event) {
        // Simple extraction - you can make this more sophisticated
        const locations = ['Germany', 'France', 'Britain', 'Soviet Union', 'Poland', 'Austria', 'Czechoslovakia'];
        return locations[Math.floor(Math.random() * locations.length)];
    }

    extractHashtag(event) {
        const hashtags = ['EuropeCrisis', 'WorldTension', 'DiplomaticCrisis', 'MilitaryAlert'];
        return hashtags[Math.floor(Math.random() * hashtags.length)];
    }

    extractFocus(event) {
        const focuses = ['military modernization', 'industrial expansion', 'diplomatic relations', 'internal affairs'];
        return focuses[Math.floor(Math.random() * focuses.length)];
    }

    extractCrisisDetails(event) {
        const details = ['border tensions escalating', 'diplomatic relations deteriorating', 'military buildup detected', 'emergency sessions called'];
        return details[Math.floor(Math.random() * details.length)];
    }

    addTweet(tweetData) {
        // Add new tweet at the beginning (newest at top)
        this.tweets.unshift(tweetData);
        this.renderTweetAtTop(tweetData);

        // Remove oldest tweets if at max capacity
        while (this.tweets.length > this.maxTweets) {
            this.tweets.pop();
            const oldestTweet = this.container.lastElementChild;
            if (oldestTweet) {
                oldestTweet.remove();
            }
        }
    }

    renderTweet(tweet) {
        const tweetElement = document.createElement('div');
        tweetElement.className = `tweet ${tweet.isBreaking ? 'breaking' : ''}`;
        
        const flagClass = tweet.country ? `flag-${tweet.country}` : '';
        
        tweetElement.innerHTML = `
            <div class="tweet-header">
                <div class="tweet-avatar avatar-${tweet.avatar}">
                    ${this.getAvatarInitial(tweet.username)}
                </div>
                <div class="tweet-user">
                    <div class="tweet-username ${flagClass}">${tweet.username}</div>
                    <div class="tweet-handle">${tweet.handle}</div>
                </div>
                <div class="tweet-timestamp">${tweet.timestamp}</div>
            </div>
            <div class="tweet-content">${this.formatTweetContent(tweet.content)}</div>
            <div class="tweet-reactions">
                ${this.generateEmojiReactions(tweet)}
            </div>
        `;

        // Add to top of feed (newest at top)
        this.container.insertBefore(tweetElement, this.container.firstChild);

        // Update timestamps periodically
        this.updateTimestamps();
    }

    renderTweetAtTop(tweet) {
        // Render tweet at top of container (newest at top)
        const tweetElement = this.createTweetElement(tweet);
        this.container.insertBefore(tweetElement, this.container.firstChild);
        this.updateTimestamps();
    }

    renderTweetAtBottom(tweet) {
        // Render tweet at bottom of container
        const tweetElement = this.createTweetElement(tweet);
        this.container.appendChild(tweetElement);
        this.updateTimestamps();
    }

    createTweetElement(tweet) {
        // Create the tweet DOM element
        const tweetElement = document.createElement('div');
        tweetElement.className = `tweet ${tweet.isBreaking ? 'breaking' : ''}`;
        
        const flagClass = tweet.country ? `flag-${tweet.country}` : '';
        
        tweetElement.innerHTML = `
            <div class="tweet-header">
                <div class="tweet-avatar avatar-${tweet.avatar}">
                    ${this.getAvatarInitial(tweet.username)}
                </div>
                <div class="tweet-user">
                    <div class="tweet-username ${flagClass}">${tweet.username}</div>
                    <div class="tweet-handle">${tweet.handle}</div>
                </div>
                <div class="tweet-timestamp">${tweet.timestamp}</div>
            </div>
            <div class="tweet-content">${this.formatTweetContent(tweet.content)}</div>
            <div class="tweet-reactions">
                ${this.generateEmojiReactions(tweet)}
            </div>
        `;
        
        return tweetElement;
    }

    getAvatarInitial(username) {
        return username.split(' ').map(name => name[0]).join('').substring(0, 2);
    }

    formatTweetContent(content) {
        return content
            .replace(/#(\w+)/g, '<span class="tweet-hashtag">#$1</span>')
            .replace(/@(\w+)/g, '<span class="tweet-mention">@$1</span>');
    }

    generateEmojiReactions(tweet) {
        // Different emoji pools based on tweet type/content
        const reactions = [];
        
        if (tweet.isBreaking) {
            // Breaking news gets more intense reactions
            reactions.push(
                this.createReaction('😱', Math.floor(Math.random() * 20) + 5),
                this.createReaction('😰', Math.floor(Math.random() * 15) + 2),
                this.createReaction('😤', Math.floor(Math.random() * 12) + 1)
            );
        } else if (tweet.content.toLowerCase().includes('war') || tweet.content.toLowerCase().includes('attack')) {
            // War-related content
            reactions.push(
                this.createReaction('😨', Math.floor(Math.random() * 25) + 3),
                this.createReaction('😔', Math.floor(Math.random() * 18) + 2),
                this.createReaction('😠', Math.floor(Math.random() * 15) + 1)
            );
        } else if (tweet.content.toLowerCase().includes('focus') || tweet.content.toLowerCase().includes('policy')) {
            // Policy/focus content
            reactions.push(
                this.createReaction('🤔', Math.floor(Math.random() * 12) + 2),
                this.createReaction('👍', Math.floor(Math.random() * 20) + 1),
                this.createReaction('🤨', Math.floor(Math.random() * 8) + 1)
            );
        } else if (tweet.content.toLowerCase().includes('election') || tweet.content.toLowerCase().includes('democracy')) {
            // Political content
            reactions.push(
                this.createReaction('🗳️', Math.floor(Math.random() * 15) + 3),
                this.createReaction('🤷', Math.floor(Math.random() * 10) + 1),
                this.createReaction('😐', Math.floor(Math.random() * 8) + 1)
            );
        } else {
            // General reactions for regular tweets
            reactions.push(
                this.createReaction('😊', Math.floor(Math.random() * 15) + 1),
                this.createReaction('🤔', Math.floor(Math.random() * 12) + 1),
                this.createReaction('😐', Math.floor(Math.random() * 8) + 1)
            );
        }

        // Randomly add a 4th reaction sometimes
        if (Math.random() < 0.4) {
            const extraEmojis = ['🙄', '😅', '🤯', '👀', '😬', '🤐'];
            const randomEmoji = extraEmojis[Math.floor(Math.random() * extraEmojis.length)];
            reactions.push(this.createReaction(randomEmoji, Math.floor(Math.random() * 5) + 1));
        }

        return reactions.join('');
    }

    createReaction(emoji, count) {
        return `
            <div class="emoji-reaction" onclick="this.classList.toggle('active')">
                <span>${emoji}</span>
                <span class="reaction-count">${count}</span>
            </div>
        `;
    }

    getRelativeTime(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);

        if (diffMins < 1) return 'now';
        if (diffMins < 60) return `${diffMins}m`;
        if (diffHours < 24) return `${diffHours}h`;
        return `${Math.floor(diffHours / 24)}d`;
    }

    updateTimestamps() {
        // This would update all visible timestamps
        // Implementation depends on how you track tweet creation times
    }

    loadSampleTweets() {
        // Start with empty feed - tweets will be loaded from server
        this.tweets = [];
    }
}

// Debug functions for simulation
async function simulateEvent(eventType) {
    try {
        const response = await fetch(`/api/generate_tweet/${eventType}`);
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                console.log('Generated tweet:', result.tweet);
                // Feed will update automatically on next poll
            } else {
                console.error('Failed to generate tweet:', result.error);
            }
        }
    } catch (error) {
        console.error('Error simulating event:', error);
        
        // Fallback to local generation
        const feed = window.twitterFeed;
        if (feed) {
            const simulatedEvents = {
                focus_complete: {
                    id: Date.now(),
                    title: 'Germany completes Army Innovations focus',
                    description: 'Military modernization efforts show significant progress'
                },
                declare_war: {
                    id: Date.now(),
                    title: 'Germany declares war on Poland',
                    description: 'European tensions escalate dramatically'
                },
                election: {
                    id: Date.now(),
                    title: 'Presidential election results announced in United States',
                    description: 'Political landscape shifts in major power'
                },
                random: {
                    id: Date.now(),
                    title: 'Diplomatic crisis emerges in Eastern Europe',
                    description: 'International relations strain under pressure'
                }
            };

            const event = simulatedEvents[eventType];
            if (event) {
                feed.generateTweetFromEvent(event);
            }
        }
    }
}

function clearFeed() {
    const feed = window.twitterFeed;
    if (feed) {
        feed.container.innerHTML = '';
        feed.tweets = [];
    }
}

// Auto generation functions
function startAutoGeneration() {
    fetch('/api/auto_start')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('autoStartBtn').disabled = true;
                document.getElementById('autoStopBtn').disabled = false;
                document.getElementById('autoStatus').textContent = 'Auto generation: Running (15s interval)';
                console.log('Auto generation started');
            } else {
                alert('Failed to start auto generation: ' + (data.message || data.error));
            }
        })
        .catch(error => {
            console.error('Error starting auto generation:', error);
            alert('Error starting auto generation');
        });
}

function stopAutoGeneration() {
    fetch('/api/auto_stop')
        .then(response => response.json())
        .then(data => {
            document.getElementById('autoStartBtn').disabled = false;
            document.getElementById('autoStopBtn').disabled = true;
            document.getElementById('autoStatus').textContent = 'Auto generation: Stopped';
            console.log('Auto generation stopped');
        })
        .catch(error => {
            console.error('Error stopping auto generation:', error);
        });
}

// Check auto generation status on page load
function checkAutoStatus() {
    fetch('/api/auto_status')
        .then(response => response.json())
        .then(data => {
            if (data.running) {
                document.getElementById('autoStartBtn').disabled = true;
                document.getElementById('autoStopBtn').disabled = false;
                document.getElementById('autoStatus').textContent = 'Auto generation: Running';
            } else {
                document.getElementById('autoStartBtn').disabled = false;
                document.getElementById('autoStopBtn').disabled = true;
                document.getElementById('autoStatus').textContent = 'Auto generation: Stopped';
            }
        })
        .catch(error => {
            console.error('Error checking auto status:', error);
        });
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.twitterFeed = new TwitterFeed();
    // Check auto generation status
    checkAutoStatus();
});

// Cleanup old folder
try {
    const oldFolder = document.querySelector('[data-old-folder]');
    if (oldFolder) oldFolder.remove();
} catch (e) {
    // Ignore cleanup errors
}