// AI Assistant Module
class AIAssistantController {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.isTyping = false;
    }

    init() {
        console.log('AIAssistantController initialized');
        this.bindEvents();
    }

    bindEvents() {
        const assistantBtn = document.getElementById('ai-assistant-btn');
        const closeBtn = document.querySelector('.ai-assistant-close');
        const sendBtn = document.getElementById('ai-chat-send');
        const input = document.getElementById('ai-chat-input');

        if (assistantBtn) {
            assistantBtn.addEventListener('click', () => this.togglePanel());
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closePanel());
        }

        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }

        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
            });
        }

        console.log('AI Assistant events bound');
    }

    togglePanel() {
        const panel = document.getElementById('ai-assistant-panel');
        if (panel) {
            this.isOpen = !this.isOpen;
            panel.classList.toggle('hidden', !this.isOpen);
        }
    }

    closePanel() {
        const panel = document.getElementById('ai-assistant-panel');
        if (panel) {
            this.isOpen = false;
            panel.classList.add('hidden');
        }
    }

    async sendMessage() {
        const input = document.getElementById('ai-chat-input');
        if (!input || !input.value.trim()) return;

        const message = input.value.trim();
        input.value = '';

        this.addMessage('user', message);
        this.showTyping();

        try {
            // This would connect to your AI service
            const response = await apiService.chatWithAI({ message });
            this.hideTyping();
            this.addMessage('assistant', response.message || 'I\'m here to help with your CRM needs!');
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTyping();
            this.addMessage('assistant', 'Sorry, I\'m having trouble connecting right now. Please try again later.');
        }
    }

    addMessage(sender, content) {
        const messagesContainer = document.getElementById('ai-chat-messages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ai-message-${sender}`;
        messageDiv.innerHTML = `
            <div class="ai-message-content">${content}</div>
            <div class="ai-message-time">${new Date().toLocaleTimeString()}</div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showTyping() {
        this.isTyping = true;
        this.addMessage('assistant', '<div class="typing-indicator">...</div>');
    }

    hideTyping() {
        this.isTyping = false;
        const messagesContainer = document.getElementById('ai-chat-messages');
        if (messagesContainer) {
            const typingIndicator = messagesContainer.querySelector('.typing-indicator');
            if (typingIndicator) {
                typingIndicator.parentElement.parentElement.remove();
            }
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.aiAssistantController = new AIAssistantController();
    window.aiAssistantController.init();
});
