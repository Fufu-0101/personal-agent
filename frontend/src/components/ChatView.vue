<template>
  <div class="chat-view">
    <div class="header">
      <h1>🤖 Personal Agent</h1>
    </div>

    <div class="messages" ref="messagesContainer">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message', msg.role]"
      >
        <div class="message-content">
          <div class="role-label">{{ msg.role === 'user' ? '👤 你' : '🤖 助手' }}</div>
          <div class="text">{{ msg.content }}</div>
          <div class="timestamp">{{ formatTime(msg.timestamp) }}</div>
        </div>
      </div>

      <div v-if="isTyping" class="message assistant">
        <div class="message-content">
          <div class="role-label">🤖 助手</div>
          <div class="text typing">思考中...</div>
        </div>
      </div>
    </div>

    <div class="input-area">
      <textarea
        v-model="inputMessage"
        @keydown.enter.exact.prevent="sendMessage"
        @keydown.shift.enter.exact="inputMessage += '\n'"
        placeholder="输入消息... (Enter 发送，Shift+Enter 换行)"
        :disabled="isTyping"
        rows="1"
        ref="textarea"
      ></textarea>
      <button
        @click="sendMessage"
        :disabled="!inputMessage.trim() || isTyping"
      >
        发送
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { chatAPI } from '../api/client'

const messages = ref([])
const inputMessage = ref('')
const isTyping = ref(false)
const conversationId = ref(null)
const messagesContainer = ref(null)
const textarea = ref(null)

// Load conversation from localStorage on mount
onMounted(() => {
  const saved = localStorage.getItem('conversation_id')
  if (saved) {
    conversationId.value = saved
    loadHistory()
  }
})

async function loadHistory() {
  try {
    const data = await chatAPI.getHistory(conversationId.value)
    messages.value = data.messages
    await scrollToBottom()
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

async function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text || isTyping.value) return

  // Add user message
  messages.value.push({
    role: 'user',
    content: text,
    timestamp: Date.now()
  })

  // Clear input
  inputMessage.value = ''
  await scrollToBottom()

  // Set typing state
  isTyping.value = true

  try {
    const response = await chatAPI.send(text, conversationId.value)

    // Update conversation ID
    if (response.conversation_id) {
      conversationId.value = response.conversation_id
      localStorage.setItem('conversation_id', response.conversation_id)
    }

    // Add assistant response
    messages.value.push({
      role: 'assistant',
      content: response.message,
      timestamp: Date.now()
    })
  } catch (error) {
    console.error('Failed to send message:', error)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，出错了：' + error.message,
      timestamp: Date.now()
    })
  } finally {
    isTyping.value = false
    await scrollToBottom()
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// Auto-resize textarea
watch(inputMessage, async () => {
  if (textarea.value) {
    textarea.value.style.height = 'auto'
    textarea.value.style.height = Math.min(textarea.value.scrollHeight, 120) + 'px'
  }
})
</script>

<style scoped>
.chat-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  overflow: hidden;
}

.header {
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f9fafb;
}

.message {
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user .message-content {
  background: #667eea;
  color: white;
  margin-left: auto;
  max-width: 70%;
}

.message.assistant .message-content {
  background: white;
  border: 1px solid #e5e7eb;
  margin-right: auto;
  max-width: 70%;
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.role-label {
  font-size: 12px;
  opacity: 0.8;
  margin-bottom: 4px;
}

.text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
}

.typing {
  color: #6b7280;
  font-style: italic;
}

.timestamp {
  font-size: 11px;
  opacity: 0.6;
  margin-top: 8px;
}

.input-area {
  display: flex;
  gap: 10px;
  padding: 20px;
  background: white;
  border-top: 1px solid #e5e7eb;
}

textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  resize: none;
  font-family: inherit;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

textarea:focus {
  border-color: #667eea;
}

button {
  padding: 0 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

button:hover:not(:disabled) {
  opacity: 0.9;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
