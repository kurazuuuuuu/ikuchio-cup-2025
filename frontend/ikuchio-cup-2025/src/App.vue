<template>
  <div id="app">
    <div v-if="!user" class="login-screen">
      <h1>{{ animatedTitle }}</h1>
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
              <div class="message-content">
                {{ animatedMessages.find(m => m.id === message.id)?.text || cleanMessageText(message.processed_text) }}
              </div>
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
import { ref, onUnmounted, nextTick, watch } from 'vue'
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

const titleText = '24時間でさようなら'
const animatedTitle = ref('')

async function typeTitle(text: string) {
  animatedTitle.value = ''
  for (let i = 0; i < text.length; i++) {
    animatedTitle.value += text[i]
    await new Promise(res => setTimeout(res, 140)) // ← 速さを遅く
  }
}

typeTitle(titleText)

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

// タイプアニメーション用
const animatedMessages = ref<{ id: string, text: string }[]>([])

watch(messages, async (newMessages: Message[]) => {
  // 新しいメッセージが来たらアニメーション開始
  animatedMessages.value = []
  for (const msg of newMessages) {
    const cleanText = cleanMessageText(msg.processed_text)
    await typeText(msg.id, cleanText)
  }
})

async function typeText(id: string, text: string) {
  let display = ''
  for (let i = 0; i < text.length; i++) {
    display += text[i]
    animatedMessages.value = [
      ...animatedMessages.value.filter(m => m.id !== id),
      { id, text: display }
    ]
    await new Promise(res => setTimeout(res, 20)) // 速さ調整
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
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #181818;
  font-family: 'Press Start 2P', monospace;
  color: #00ff00;
  letter-spacing: 1px;
}

.login-screen {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  gap: 2rem;
  background: #181818;
}

.login-screen h1 {
  font-size: 1.2rem;
  margin: 0;
  color: #00ff00;
  text-shadow: 0 0 2px #00ff00, 0 0 8px #222;
}

.login-screen button {
  padding: 0.5rem 1rem;
  font-size: 1rem;
  background: #222;
  color: #00ff00;
  border: 2px solid #00ff00;
  border-radius: 0;
  cursor: pointer;
  font-family: inherit;
  box-shadow: none;
  letter-spacing: 1px;
}

.user-id {
  padding: 0.25rem 0.5rem;
  background: #222;
  color: #00ff00;
  font-size: 0.7rem;
  text-align: left;
  border-bottom: 2px solid #00ff00;
  font-family: inherit;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  border-bottom: 2px solid #00ff00;
  background: #222;
  color: #00ff00;
  font-size: 0.9rem;
}

.timer {
  font-family: inherit;
  font-size: 1rem;
  font-weight: bold;
  color: #00ff00;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  background: #181818;
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
  max-width: 80%;
  padding: 0.5rem 0.7rem;
  border-radius: 0;
  word-wrap: break-word;
  background: #222;
  color: #00ff00;
  font-family: inherit;
  border: 2px solid #00ff00;
  box-shadow: none;
  font-size: 0.8rem;
}

.own-message .message-bubble {
  background: #181818;
  color: #00ff00;
  border: 2px solid #00ff00;
}

.other-message .message-bubble {
  background: #222;
  color: #00ff00;
  border: 2px solid #00ff00;
}

.message-content {
  margin-bottom: 0.1rem;
  line-height: 1.2;
  font-family: inherit;
}

.message-time {
  font-size: 0.6rem;
  opacity: 0.7;
  text-align: right;
  color: #00ff00;
  font-family: inherit;
}

.other-message .message-time {
  text-align: left;
}

.no-messages {
  text-align: center;
  color: #00ff00;
  font-style: italic;
  padding: 1rem;
  font-family: inherit;
  font-size: 0.8rem;
}

.messages {
  position: relative;
}

.no-room-screen {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem;
  background: #181818;
}

.no-room-message {
  text-align: center;
  color: #00ff00;
  font-size: 0.8rem;
}

.no-room-message h2 {
  font-size: 1rem;
  margin-bottom: 1rem;
  color: #00ff00;
}

.reset-timer {
  background: #222;
  padding: 0.5rem;
  border-radius: 0;
  border: 2px solid #00ff00;
  font-size: 0.8rem;
}

.reset-timer p {
  margin: 0;
  font-size: 0.8rem;
  font-family: inherit;
  color: #00ff00;
}

.input-area {
  display: flex;
  padding: 0.5rem;
  gap: 0.5rem;
  border-top: 2px solid #00ff00;
  background: #222;
}

.input-area textarea {
  flex: 1;
  padding: 0.3rem;
  border: 2px solid #00ff00;
  border-radius: 0;
  resize: none;
  min-height: 40px;
  background: #181818;
  color: #00ff00;
  font-family: inherit;
  font-size: 0.8rem;
  letter-spacing: 1px;
}

.input-area button {
  padding: 0.3rem 0.7rem;
  background: #181818;
  color: #00ff00;
  border: 2px solid #00ff00;
  border-radius: 0;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.8rem;
  letter-spacing: 1px;
}

.input-area button:disabled {
  border: 2px solid #00ff0055;
  color: #00ff0055 !important;
}

.message-bubble.processing {
  background: #222 !important;
  border: 2px dashed #00ff00;
  color: #00ff00;
}

.processing-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #00ff00;
  font-style: italic;
  font-family: inherit;
  font-size: 0.8rem;
}

.dot-animation {
  display: flex;
}

.dot-animation span {
  animation: blink 1.4s infinite;
  animation-fill-mode: both;
  color: #00ff00;
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

/* スクロールバーもドット風に */
.messages::-webkit-scrollbar {
  width: 8px;
  background: #222;
}
.messages::-webkit-scrollbar-thumb {
  background: #00ff00;
  border-radius: 0;
}
</style>