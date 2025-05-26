/**
 * AI Chat functionality for Portfolio Management System - Enhanced Version
 */
document.addEventListener('DOMContentLoaded', function() {
    const aiChatButton = document.getElementById('aiChatButton');
    const aiChatPopup = document.getElementById('aiChatPopup');
    const minimizeChat = document.getElementById('minimizeChat');
    const closeChat = document.getElementById('closeChat');
    const chatForm = document.getElementById('chatForm');
    const userMessage = document.getElementById('userMessage');
    const chatMessages = document.getElementById('chatMessages');
    const suggestedItems = document.querySelectorAll('.suggested-item');
    const chatContainer = document.getElementById('chatContainer');
    const suggestedQuestionsSection = document.getElementById('suggestedQuestions');
    
    // Biến để lưu tên người dùng
    let currentUsername = "bạn";
    
    // Lấy tên người dùng từ thẻ meta khi trang được tải
    const usernameMetaTag = document.querySelector('meta[name="username"]');
    const fullNameMetaTag = document.querySelector('meta[name="user-full-name"]');
    
    if (fullNameMetaTag) {
        const fullName = fullNameMetaTag.getAttribute('content');
        if (fullName && fullName.trim() !== '') {
            currentUsername = fullName;
            console.log("Đã tìm thấy tên đầy đủ của người dùng:", currentUsername);
        }
    } else if (usernameMetaTag) {
        const metaUsername = usernameMetaTag.getAttribute('content');
        if (metaUsername && metaUsername.trim() !== '') {
            currentUsername = metaUsername;
            console.log("Không tìm thấy tên đầy đủ, sử dụng username:", currentUsername);
        }
    } else {
        console.log("Không tìm thấy thông tin người dùng, sử dụng giá trị mặc định:", currentUsername);
    }
    
    let chatHistory = [];
    let isFirstInteraction = true;
    let hasUsedSuggestedQuestion = false; // Biến để theo dõi xem đã dùng gợi ý chưa
    let emojis = ['👍', '✨', '🎉', '🚀', '💡', '🔥', '⭐', '😊'];
    
    // Lưu trữ câu trả lời gần đây để tránh lặp lại
    let recentResponses = [];
    const MAX_RECENT_RESPONSES = 3;
    
    // Thêm biến cho việc lưu trữ lịch sử chat
    const CHAT_HISTORY_KEY = 'astrobot_chat_history';
    
    // Tải lịch sử chat từ localStorage khi trang được tải
    if (localStorage.getItem(CHAT_HISTORY_KEY)) {
        try {
            chatHistory = JSON.parse(localStorage.getItem(CHAT_HISTORY_KEY));
            
            // Khôi phục tin nhắn từ lịch sử chat khi mở chat
            document.addEventListener('DOMContentLoaded', function() {
                // Đảm bảo chat messages đã được tạo
                if (chatMessages) {
                    // Hiển thị lại tin nhắn từ lịch sử (tối đa 10 tin nhắn gần nhất)
                    const messagesToShow = chatHistory.slice(-20); // Lấy 20 tin nhắn gần nhất
                    messagesToShow.forEach(msg => {
                        if (msg.role === 'user' || msg.role === 'assistant') {
                            addMessageFromHistory(msg.content, msg.role === 'user' ? 'user' : 'ai');
                        }
                    });
                }
            });
        } catch (e) {
            console.error('Lỗi khi tải lịch sử chat:', e);
            chatHistory = [];
        }
    }
    
    // Add pulse animation to chat button
    aiChatButton.classList.add('pulse-animation');
    
    // Đảm bảo nút chat hiển thị đúng cách
    aiChatButton.style.display = 'flex';
    aiChatPopup.style.display = 'none';
      // Toggle chat popup with enhanced animations
    aiChatButton.addEventListener('click', function() {
        console.log("Chat button clicked");
        aiChatPopup.style.display = 'flex';
        
        // Add animation after display is set - changed to 5ms for faster response
        setTimeout(() => {
            aiChatPopup.classList.add('show-animation');
            // Stop pulse animation after first click
            if (isFirstInteraction) {
                aiChatButton.classList.remove('pulse-animation');
                isFirstInteraction = false;
            }
        }, 5);
        
        aiChatButton.style.display = 'none';
        
        // Welcome message if first time
        if (chatHistory.length === 0) {
            console.log("Hiển thị tin nhắn chào mừng lần đầu");
            setTimeout(() => {
                // Thiết lập khung vai trò cho AI
                chatHistory.push({
                    role: 'system',
                    content: 'Bạn hãy giải đáp mọi thứ về Tài chính, Kinh tế và quản lí danh mục đầu tư, và các vấn đề liên quan đến tài chính cho tôi. Hãy trả lời một cách tự nhiên nhất nhé, không ràng buộc cứng nhắt.'
                });
                
                // Hiển thị tin nhắn chào mừng đầu tiên với tên người dùng
                const welcomeMessage = `Xin chào ${currentUsername}! Tôi là trợ lý AstroBot chuyên về tài chính và đầu tư. Tôi có thể giúp bạn giải đáp các thắc mắc về chứng khoán, quản lý danh mục đầu tư, và các vấn đề kinh tế tài chính. Bạn cần hỗ trợ gì hôm nay?`;
                addMessage(welcomeMessage, 'ai');
                recentResponses.push(welcomeMessage);
                
                // Lưu lịch sử chat
                saveHistory();
            }, 500);
        } else if (chatMessages.children.length === 0) {
            // Nếu chatHistory có dữ liệu nhưng không có tin nhắn hiển thị
            // (có thể xảy ra khi localStorage có dữ liệu nhưng không hiển thị)
            console.log("Hiển thị lại tin nhắn chào mừng");
            setTimeout(() => {
                const welcomeMessage = `Xin chào ${currentUsername}! Tôi là trợ lý AstroBot chuyên về tài chính và đầu tư. Tôi có thể tiếp tục giúp bạn giải đáp các thắc mắc về tài chính và đầu tư. Bạn cần hỗ trợ gì hôm nay?`;
                addMessage(welcomeMessage, 'ai');
            }, 500);
        }
        
        // Scroll to the bottom of the chat messages
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Focus the input field
        setTimeout(() => {
            userMessage.focus();
        }, 300);
    });
    
    // Minimize chat with animation
    minimizeChat.addEventListener('click', function() {
        minimizeChatWithAnimation();
    });
    
    // Close chat with animation
    closeChat.addEventListener('click', function() {
        minimizeChatWithAnimation();
    });
    
    // Thêm sự kiện double-click cho nút đóng chat để xóa lịch sử
    closeChat.addEventListener('dblclick', function() {
        console.log("Đang xóa lịch sử chat...");
        // Xóa lịch sử từ localStorage
        localStorage.removeItem(CHAT_HISTORY_KEY);
        // Xóa lịch sử từ bộ nhớ
        chatHistory = [];
        // Xóa tin nhắn hiển thị
        chatMessages.innerHTML = '';
        
        // Hiển thị thông báo
        alert("Lịch sử chat đã được xóa. Lần sau khi bạn mở chat, bạn sẽ thấy tin nhắn chào mừng mới.");
        
        // Đóng chat
        minimizeChatWithAnimation();
    });
      function minimizeChatWithAnimation() {
        console.log("Minimizing chat");
        // First remove the animation class
        aiChatPopup.classList.remove('show-animation');
        
        // Then hide after animation completes - reduced from 300ms to 200ms
        setTimeout(() => {
            aiChatPopup.style.display = 'none';
            
            // Animate the chat button appearing again
            aiChatButton.style.display = 'flex';
            aiChatButton.style.transform = 'scale(0.8)';
            setTimeout(() => {
                aiChatButton.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    aiChatButton.style.transform = '';
                }, 150); // changed from 200ms to 150ms
            }, 80); // changed from 100ms to 80ms
            
        }, 200); // changed from 300ms to 200ms
    }
    
    // Thêm sự kiện chạm/nhấn cho thiết bị di động
    aiChatButton.addEventListener('touchstart', function(e) {
        e.preventDefault();
        aiChatButton.click();
    });
    
    // Handle suggested questions with enhanced interaction
    suggestedItems.forEach(item => {
        item.addEventListener('click', function() {
            const question = this.getAttribute('data-question');
            userMessage.value = question;
            
            // Đánh dấu đã sử dụng gợi ý
            hasUsedSuggestedQuestion = true;
            
            // Add ripple effect
            createRippleEffect(this);
            
            // Hide the suggested questions section
            if (suggestedQuestionsSection) {
                suggestedQuestionsSection.style.display = 'none';
            }
            
            // Submit the form
            const event = new Event('submit', {
                'bubbles': true,
                'cancelable': true
            });
            chatForm.dispatchEvent(event);
        });
    });
    
    function createRippleEffect(element) {
        const ripple = document.createElement('span');
        ripple.classList.add('ripple');
        
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        
        ripple.style.width = ripple.style.height = `${size}px`;
        ripple.style.left = `${event.clientX - rect.left - size/2}px`;
        ripple.style.top = `${event.clientY - rect.top - size/2}px`;
        
        element.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }
    
    // Handle sending messages with emoji reactions
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = userMessage.value.trim();
        if (message) {
            // Kiểm tra xem đây có phải tin nhắn đầu tiên và không dùng gợi ý không
            if (chatHistory.length <= 1 && !hasUsedSuggestedQuestion) {
                // Ẩn phần gợi ý vì người dùng tự nhập tin nhắn
                if (suggestedQuestionsSection) {
                    suggestedQuestionsSection.classList.add('hidden');
                    suggestedQuestionsSection.style.display = 'none';
                }
            }
            
            // Add user message to chat
            addMessage(message, 'user');
            userMessage.value = '';
            
            // Show random emoji reaction
            showEmojiReaction();
            
            // Show enhanced typing indicator
            showEnhancedTypingIndicator();
            
            // Call API
            callGeminiAPI(message);
        }
    });
    
    // Thêm auto-resize cho textarea
    function autoResizeTextarea() {
        userMessage.style.height = 'auto';
        userMessage.style.height = Math.min(userMessage.scrollHeight, 80) + 'px';
    }
    
    // Xử lý sự kiện nhấn phím Enter để gửi tin nhắn (Shift+Enter để xuống dòng)
    userMessage.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
    
    function showEmojiReaction() {
        const randomEmoji = emojis[Math.floor(Math.random() * emojis.length)];
        const emojiEl = document.createElement('div');
        emojiEl.className = 'emoji-reaction';
        emojiEl.textContent = randomEmoji;
        
        // Position the emoji near the send button
        const rect = chatForm.getBoundingClientRect();
        emojiEl.style.left = `${rect.right - 40}px`;
        emojiEl.style.top = `${rect.top}px`;
        
        document.body.appendChild(emojiEl);
        
        // Remove after animation
        setTimeout(() => {
            emojiEl.remove();
        }, 1500);
    }
    
    function addMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-container ${sender === 'user' ? 'user-container' : 'ai-container'}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (sender === 'ai') {
            // Xử lý Markdown cho tin nhắn AI
            const formattedContent = parseMarkdown(message);
            messageContent.innerHTML = formattedContent;
            messageContent.classList.add(sender + '-message');
        } else {
            // Đối với tin nhắn người dùng, hiển thị text thông thường
            const messageParagraph = document.createElement('p');
            messageParagraph.textContent = message;
            messageContent.appendChild(messageParagraph);
            messageContent.classList.add(sender + '-message');
        }
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // Add to chat history
        chatHistory.push({
            role: sender === 'user' ? 'user' : 'assistant',
            content: message
        });
        
        // Lưu lịch sử chat
        saveHistory();
        
        // Scroll to bottom with smooth animation
        smoothScrollToBottom(chatMessages);
    }
    
    // Hàm thêm tin nhắn vào chatbox khi khôi phục từ lịch sử
    function addMessageFromHistory(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-container ${sender === 'user' ? 'user-container' : 'ai-container'}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (sender === 'ai') {
            // Xử lý Markdown cho tin nhắn AI
            const formattedContent = parseMarkdown(message);
            messageContent.innerHTML = formattedContent;
            messageContent.classList.add(sender + '-message');
        } else {
            // Đối với tin nhắn người dùng, hiển thị text thông thường
            const messageParagraph = document.createElement('p');
            messageParagraph.textContent = message;
            messageContent.appendChild(messageParagraph);
            messageContent.classList.add(sender + '-message');
        }
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
    }
    
    // Lưu lịch sử chat vào localStorage
    function saveHistory() {
        try {
            // Giới hạn lịch sử chat ở 50 tin nhắn gần nhất để tránh lỗi localStorage
            const limitedHistory = chatHistory.slice(-50);
            localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(limitedHistory));
        } catch (e) {
            console.error('Lỗi khi lưu lịch sử chat:', e);
        }
    }
    
    // Phân tích cú pháp Markdown đơn giản
    function parseMarkdown(text) {
        let result = text;
        
        // Thêm class highlight cho các từ khóa quan trọng trong dấu ==
        result = result.replace(/==(.*?)==/g, '<span class="highlight">$1</span>');
        
        // Xử lý số liệu với định dạng [số]
        result = result.replace(/\[([0-9.,]+)\]/g, '<span class="number">$1</span>');
        
        // Xử lý đậm (bold) - hỗ trợ cả **text** và __text__
        result = result.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        result = result.replace(/__(.*?)__/g, '<strong>$1</strong>');
        
        // Xử lý nghiêng (italic) - hỗ trợ cả *text* và _text_
        result = result.replace(/\*([^\*]+)\*/g, '<em>$1</em>');
        result = result.replace(/_([^_]+)_/g, '<em>$1</em>');
        
        // Xử lý tiêu đề - thêm styles cho tiêu đề
        result = result.replace(/^### (.*?)$/gm, '<h3 class="markdown-heading">$1</h3>');
        result = result.replace(/^## (.*?)$/gm, '<h2 class="markdown-heading">$1</h2>');
        result = result.replace(/^# (.*?)$/gm, '<h1 class="markdown-heading">$1</h1>');
        
        // Xử lý danh sách không thứ tự với hiệu ứng đẹp hơn
        result = result.replace(/^\* (.*?)$/gm, '<li class="markdown-list-item">$1</li>');
        result = result.replace(/^- (.*?)$/gm, '<li class="markdown-list-item">$1</li>');
        
        // Bọc danh sách trong thẻ <ul> với class
        result = result.replace(/<li class="markdown-list-item">(.*?)<\/li>(?:\s*<li class="markdown-list-item">.*?<\/li>)*/g, '<ul class="markdown-list">$&</ul>');
        
        // Xử lý danh sách có thứ tự với counter
        result = result.replace(/^\d+\. (.*?)$/gm, '<li class="markdown-list-item-ordered">$1</li>');
        
        // Bọc danh sách có thứ tự trong thẻ <ol> với class
        result = result.replace(/<li class="markdown-list-item-ordered">(.*?)<\/li>(?:\s*<li class="markdown-list-item-ordered">.*?<\/li>)*/g, '<ol class="markdown-list-ordered">$&</ol>');
        
        // Xử lý đoạn trích dẫn với hiệu ứng đẹp
        result = result.replace(/^> (.*?)$/gm, '<blockquote class="markdown-blockquote">$1</blockquote>');
        
        // Xử lý đoạn code với styles
        result = result.replace(/`(.*?)`/g, '<code class="markdown-code">$1</code>');
        
        // Xử lý bảng đơn giản
        // Nhận dạng toàn bộ bảng
        const tableRegex = /^\|(.*)\|[\r\n]\|([-|:]*)[\r\n]((?:\|.*\|[\r\n]?)*)/gm;
        result = result.replace(tableRegex, function(match, headerRow, separatorRow, bodyRows) {
            // Xử lý header
            const headers = headerRow.split('|').map(cell => cell.trim()).filter(Boolean);
            let headerHTML = '<tr>';
            headers.forEach(header => {
                headerHTML += `<th>${header}</th>`;
            });
            headerHTML += '</tr>';
            
            // Xử lý body
            const rows = bodyRows.trim().split('\n');
            let bodyHTML = '';
            rows.forEach(row => {
                if (row.trim() === '') return;
                const cells = row.split('|').map(cell => cell.trim()).filter(Boolean);
                bodyHTML += '<tr>';
                cells.forEach(cell => {
                    bodyHTML += `<td>${cell}</td>`;
                });
                bodyHTML += '</tr>';
            });
            
            return `<table><thead>${headerHTML}</thead><tbody>${bodyHTML}</tbody></table>`;
        });
        
        // Xử lý liên kết với hiệu ứng hover
        result = result.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" class="markdown-link">$1</a>');
        
        // Xử lý xuống dòng với padding
        result = result.replace(/\n\n/g, '<div class="markdown-paragraph-break"></div>');
        result = result.replace(/\n/g, '<br>');
        
        // Xử lý card thông tin
        result = result.replace(/\[info\](.*?)\[\/info\]/gs, '<div class="card-info">$1</div>');
        result = result.replace(/\[warning\](.*?)\[\/warning\]/gs, '<div class="card-warning">$1</div>');
        result = result.replace(/\[success\](.*?)\[\/success\]/gs, '<div class="card-success">$1</div>');
        
        return result;
    }
    
    function smoothScrollToBottom(element) {
        const start = element.scrollTop;
        const end = element.scrollHeight - element.clientHeight;
        const duration = 300; // ms
        const startTime = performance.now();
        
        function scrollStep(timestamp) {
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = 0.5 - Math.cos(progress * Math.PI) / 2;
            
            element.scrollTop = start + (end - start) * easeProgress;
            
            if (elapsed < duration) {
                window.requestAnimationFrame(scrollStep);
            }
        }
        
        window.requestAnimationFrame(scrollStep);
    }
    
    function showEnhancedTypingIndicator() {
        // Remove any existing typing indicators
        removeTypingIndicator();
        
        const typingContainer = document.createElement('div');
        typingContainer.className = 'message-container ai-container';
        typingContainer.id = 'typingIndicator';
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai-message typing-message';
        
        // Create modern animated dots for typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        
        // Add three animated dots
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            dot.className = 'typing-dot';
            typingIndicator.appendChild(dot);
        }
        
        typingDiv.appendChild(typingIndicator);
        typingContainer.appendChild(typingDiv);
        chatMessages.appendChild(typingContainer);
        
        // Scroll to the typing indicator
        smoothScrollToBottom(chatMessages);
    }
    
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Hàm gọi API để lấy phản hồi từ mô hình AI
    async function callGeminiAPI(message) {
        // Hiển thị typing indicator
        showEnhancedTypingIndicator();
        
        try {
            // Chuẩn bị dữ liệu cho API
            const requestData = {
                message: message,
                history: chatHistory
            };
            
            // Thực hiện cuộc gọi API đến backend
            const response = await fetch('/api/ai-chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            // Kiểm tra nếu cuộc gọi thành công
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            // Lấy dữ liệu từ API
            const data = await response.json();
            
            // Xóa typing indicator
            removeTypingIndicator();
            
            // Hiển thị câu trả lời từ API
            addMessage(data.response, 'ai');
            
        } catch (error) {
            console.error('Error calling AI API:', error);
            
            // Xóa typing indicator
            removeTypingIndicator();
            
            // Hiển thị thông báo lỗi cho người dùng
            addMessage("Rất tiếc, đã có lỗi xảy ra khi kết nối với AI. Vui lòng thử lại sau.", 'ai');
        }
    }
    
    // Ẩn phần gợi ý khi người dùng bắt đầu nhập tin nhắn đầu tiên
    userMessage.addEventListener('input', function() {
        // Auto-resize textarea
        autoResizeTextarea();
        
        // Chỉ ẩn khi là tin nhắn đầu tiên và chưa dùng gợi ý
        if (chatHistory.length <= 1 && !hasUsedSuggestedQuestion) {
            if (this.value.trim() !== '') {
                if (suggestedQuestionsSection && !suggestedQuestionsSection.classList.contains('hidden')) {
                    suggestedQuestionsSection.style.opacity = '0.5';
                    suggestedQuestionsSection.style.pointerEvents = 'none';
                }
            } else {
                if (suggestedQuestionsSection && !suggestedQuestionsSection.classList.contains('hidden')) {
                    suggestedQuestionsSection.style.opacity = '1';
                    suggestedQuestionsSection.style.pointerEvents = 'auto';
                }
            }
        }
    });
}); 