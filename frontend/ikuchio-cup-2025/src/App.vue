<template>
  <div id="app">
    <div v-if="!user" class="login-screen">
      <h1>24時間でさようなら</h1>
      <button @click="login">入室する</button>
    </div>
    
    <div v-else class="chat-screen">
      <div class="user-id">ユーザーID: {{ user.fingerprint_id }}</div>
      
      <!-- ルームが存在しない場合 -->
      <div v-if="!roomId" class="no-room-screen">
        <div class="no-room-message">
          <h2>まだあなたの相手は見つかっていないようですよ...</h2>
          <div class="reset-timer">
            <p>リセットまでの時間: {{ timeLeft }}</p>
          </div>
        </div>
      </div>
      
      <!-- ルームが存在する場合 -->
      <div v-else>
        <div class="header">
          <h2>Room: {{ roomId }}</h2>
          <div class="timer">{{ timeLeft }}</div>
        </div>
        
        <div class="messages" ref="messagesContainer">

          
          <div v-if="messages.length === 0" class="no-messages">
            <span v-if="!isSoloRoom">まだメッセージがありません。最初のメッセージを送ってみましょう！</span>
            <span v-else>今日はひとりの時間です。思いを書いてみましょう。</span>
          </div>
          <div v-for="message in messages" :key="message.id" 
                :class="['message-wrapper', message.original_sender_id === user?.fingerprint_id ? 'own-message' : 'other-message']">
            <div class="message-bubble">
              <div class="message-content">{{ cleanMessageText(message.processed_text) }}</div>
              <div class="message-time">{{ formatTime(message.created_at) }}</div>
            </div>
          </div>
          
          <!-- AI処理中メッセージ -->
          <div v-if="sending" class="message-wrapper own-message">
            <div class="message-bubble processing">
              <div class="message-content">
                <div class="processing-indicator">
                  <span class="dots">AIが処理中</span>
                  <div class="dot-animation">
                    <span>.</span><span>.</span><span>.</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="input-area">
          <textarea 
            v-model="newMessage" 
            @keydown="handleKeydown"
            placeholder="メッセージを入力..."
            :disabled="sending"
          ></textarea>
          <button @click="sendMessage" :disabled="!newMessage.trim() || sending">
            {{ sending ? '送信中...' : '送信' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted, nextTick } from 'vue'
import { generateFingerprint } from './utils/fingerprint'

interface Message {
  id: string
  processed_text: string
  created_at: string
  original_sender_id: string
}

interface User {
  fingerprint_id: string
  room_id: string
}

// 環境に応じてAPI_BASEを自動切り替え
const getApiBase = () => {
  const hostname = window.location.hostname
  if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0') {
    return 'http://localhost:8000/api'
  }
  return 'https://ikuchio-backend-88236233617.asia-northeast1.run.app/api'
}

const API_BASE = getApiBase()

const user = ref<User | null>(null)
const roomId = ref<string>('')
const messages = ref<Message[]>([])
const newMessage = ref<string>('')
const sending = ref<boolean>(false)
const timeLeft = ref<string>('')
const messagesContainer = ref<HTMLElement>()
const isSoloRoom = ref<boolean>(false)

let timerInterval: number | null = null
let websocket: WebSocket | null = null

const login = async () => {
  let fingerprint = ''
  try {
    fingerprint = generateFingerprint()
    
    if (!fingerprint || fingerprint.length < 8) {
      alert(`フィンガープリントの生成に失敗しました。\n生成されたフィンガープリント: ${fingerprint}\nブラウザを更新して再度お試しください。`)
      return
    }
    
    const response = await fetch(`${API_BASE}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fingerprint_id: fingerprint }),
      mode: 'cors'
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: '不明なエラー' }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }
    
    const userData = await response.json()
    
    if (!userData || !userData.fingerprint_id) {
      throw new Error('ユーザーデータが無効です')
    }
    
    user.value = userData
    roomId.value = userData.room_id || ''
    
    console.log(`Debug: User logged in - ID: ${userData.fingerprint_id.slice(0, 8)}, Room: ${userData.room_id || 'None'}`)
    
    if (userData.room_id) {
      connectWebSocket()
    }
    startTimer()
    
  } catch (error) {
    console.error('Login failed:', error)
    let errorMessage = '不明なエラー'
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      errorMessage = `サーバーに接続できません。${API_BASE}にアクセスできるか確認してください。`
    } else if (error instanceof Error) {
      errorMessage = error.message
    }
    
    alert(`ログインに失敗しました: ${errorMessage}\n\nデバッグ情報:\nフィンガープリント: ${fingerprint}\nAPI URL: ${API_BASE}`)
  }
}

const refreshUserData = async () => {
  if (!user.value) return
  
  try {
    const response = await fetch(`${API_BASE}/users?fingerprint_id=${user.value.fingerprint_id}`)
    if (response.ok) {
      const userData = await response.json()
      if (userData && userData.fingerprint_id) {
        const oldRoomId = roomId.value
        user.value = userData
        roomId.value = userData.room_id || ''
        
        console.log(`Debug: User data refreshed - Room changed from ${oldRoomId || 'None'} to ${userData.room_id || 'None'}`)
        
        if (userData.room_id && userData.room_id !== oldRoomId) {
          connectWebSocket()
        }
      }
    }
  } catch (error) {
    console.error('Failed to refresh user data:', error)
  }
}

const sendMessage = async () => {
  if (!newMessage.value.trim() || sending.value || !user.value) return
  
  sending.value = true
  try {
    const response = await fetch(`${API_BASE}/room/${roomId.value}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        original_text: newMessage.value,
        sender_id: user.value.fingerprint_id
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    
    const messageText = newMessage.value
    newMessage.value = ''
    
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      const wsMessage = JSON.stringify({ type: 'message', text: messageText })
      websocket.send(wsMessage)
    }
    
    await fetchMessages()
  } catch (error) {
    console.error('Send failed:', error)
    alert('メッセージの送信に失敗しました')
  } finally {
    sending.value = false
  }
}

const fetchMessages = async () => {
  if (!roomId.value) return
  
  try {
    const response = await fetch(`${API_BASE}/room/${roomId.value}`)
    
    if (response.ok) {
      const data = await response.json()
      messages.value = Array.isArray(data) ? data : []
      
      // 1人ルームかどうかを判定（自分以外のメッセージがあるかどうか）
      const otherMessages = messages.value.filter(msg => msg.original_sender_id !== user.value?.fingerprint_id)
      isSoloRoom.value = otherMessages.length === 0 && messages.value.length > 0
      
      // メッセージがない場合はルーム情報で判定
      if (messages.value.length === 0) {
        checkIfSoloRoom()
      }
      
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    // サイレントにエラーを処理
  }
}

const checkIfSoloRoom = async () => {
  if (!roomId.value) return
  
  try {
    const response = await fetch(`${API_BASE}/rooms/${roomId.value}`)
    if (response.ok) {
      const roomData = await response.json()
      isSoloRoom.value = roomData.users && roomData.users.length === 1
    }
  } catch (error) {
    // サイレントにエラーを処理
  }
}

const connectWebSocket = () => {
  if (!roomId.value) return
  
  // WebSocket URLも環境に応じて切り替え
  const getWsUrl = () => {
    const hostname = window.location.hostname
    if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0') {
      return `ws://localhost:8000/ws/${roomId.value}`
    }
    return `wss://ikuchio-backend-88236233617.asia-northeast1.run.app/ws/${roomId.value}`
  }
  
  const wsUrl = getWsUrl()
  
  websocket = new WebSocket(wsUrl)
  
  websocket.onopen = () => {
    fetchMessages()
  }
  
  websocket.onmessage = () => {
    fetchMessages()
  }
  
  websocket.onclose = () => {
    setTimeout(() => {
      if (roomId.value) {
        connectWebSocket()
      }
    }, 3000)
  }
}

const startTimer = () => {
  updateTimer()
  timerInterval = setInterval(updateTimer, 1000)
}

const updateTimer = () => {
  const now = new Date()
  const tomorrow = new Date(now)
  tomorrow.setDate(tomorrow.getDate() + 1)
  tomorrow.setHours(0, 0, 0, 0)
  
  const diff = tomorrow.getTime() - now.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)
  
  timeLeft.value = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString('ja-JP', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const cleanMessageText = (text: string) => {
  return text.replace(/^\[[^\]]+\]:\s*/, '')
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
    event.preventDefault()
    sendMessage()
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

onUnmounted(() => {
  if (websocket) {
    websocket.close()
  }
  if (timerInterval) clearInterval(timerInterval)
})
</script>

<style scoped>
#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.login-screen {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  gap: 2rem;
}

.login-screen h1 {
  font-size: 2rem;
  margin: 0;
}

.login-screen button {
  padding: 1rem 2rem;
  font-size: 1.2rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.chat-screen {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.user-id {
  padding: 0.5rem 1rem;
  background: #f8f9fa;
  color: #999;
  font-size: 0.8rem;
  text-align: center;
  border-bottom: 1px solid #eee;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.timer {
  font-family: monospace;
  font-size: 1.2rem;
  font-weight: bold;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.message-wrapper {
  display: flex;
  width: 100%;
}

.own-message {
  justify-content: flex-end;
}

.other-message {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  padding: 0.75rem 1rem;
  border-radius: 18px;
  word-wrap: break-word;
}

.own-message .message-bubble {
  background: #007bff;
  color: white;
  border-bottom-right-radius: 4px;
}

.other-message .message-bubble {
  background: #f1f3f4;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-content {
  margin-bottom: 0.25rem;
  line-height: 1.4;
}

.message-time {
  font-size: 0.7rem;
  opacity: 0.7;
  text-align: right;
}

.other-message .message-time {
  text-align: left;
}

.no-messages {
  text-align: center;
  color: #999;
  font-style: italic;
  padding: 2rem;
}



.messages {
  position: relative;
}

.no-room-screen {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
}

.no-room-message {
  text-align: center;
  color: #666;
}

.no-room-message h2 {
  font-size: 1.5rem;
  margin-bottom: 2rem;
  color: #555;
}

.reset-timer {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.reset-timer p {
  margin: 0;
  font-size: 1.1rem;
  font-family: monospace;
  color: #007bff;
}

.input-area {
  display: flex;
  padding: 1rem;
  gap: 1rem;
  border-top: 1px solid #eee;
}

.input-area textarea {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
  min-height: 60px;
}

.input-area button {
  padding: 0.5rem 1rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.input-area button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.message-bubble.processing {
  background: #e3f2fd !important;
  border: 1px solid #2196f3;
}

.processing-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #1976d2;
  font-style: italic;
}

.dot-animation {
  display: flex;
}

.dot-animation span {
  animation: blink 1.4s infinite;
  animation-fill-mode: both;
}

.dot-animation span:nth-child(2) {
  animation-delay: 0.2s;
}

.dot-animation span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes blink {
  0%, 80%, 100% {
    opacity: 0;
  }
  40% {
    opacity: 1;
  }
}
</style>