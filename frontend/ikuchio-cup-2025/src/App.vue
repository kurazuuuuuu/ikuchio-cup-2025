<template>
  <div id="app">
    <div v-if="!user" class="login-screen">
      <h1>24時間でさようなら</h1>
      <button @click="login">入室する</button>
    </div>
    
    <div v-else class="chat-screen">
      <div class="user-id">ユーザーID: {{ user.firebase_uid }}</div>
      
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
                :class="['message-wrapper', message.original_sender_id === user?.firebase_uid ? 'own-message' : 'other-message']">
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
import { signInAnonymous, type FirebaseAuthResult } from './firebase/config'

interface Message {
  id: string
  processed_text: string
  created_at: string
  original_sender_id: string
}

interface User {
  firebase_uid: string
  room_id: string
}

// 環境に応じてAPI_BASEを自動切り替え
const getApiBase = () => {
  const hostname = window.location.hostname
  if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0') {
    return 'http://localhost:8000'
  }
  return 'https://ikuchio-backend-88236233617.asia-northeast1.run.app'
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
  let firebaseAuth: FirebaseAuthResult | null = null
  try {
    // Firebase匿名認証
    firebaseAuth = await signInAnonymous()
    console.log('Firebase Auth successful:', firebaseAuth.uid)
    
    const response = await fetch(`${API_BASE}/api/users`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${firebaseAuth.token}`
      },
      body: JSON.stringify({ firebase_uid: firebaseAuth.uid }),
      mode: 'cors'
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: '不明なエラー' }))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }
    
    const userData = await response.json()
    
    if (!userData || !userData.firebase_uid) {
      throw new Error('ユーザーデータが無効です')
    }
    
    user.value = userData
    roomId.value = userData.room_id || ''
    
    console.log(`Debug: User logged in - ID: ${userData.firebase_uid.slice(0, 8)}, Room: ${userData.room_id || 'None'}`)
    
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
    
    alert(`ログインに失敗しました: ${errorMessage}\n\nデバッグ情報:\nFirebase UID: ${firebaseAuth?.uid || 'None'}\nAPI URL: ${API_BASE}`)
  }
}

const refreshUserData = async () => {
  if (!user.value) return
  
  try {
    const response = await fetch(`${API_BASE}/api/users?firebase_uid=${user.value.firebase_uid}`)
    if (response.ok) {
      const userData = await response.json()
      if (userData && userData.firebase_uid) {
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
    const response = await fetch(`${API_BASE}/api/room/${roomId.value}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        original_text: newMessage.value,
        sender_id: user.value.firebase_uid
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
    const response = await fetch(`${API_BASE}/api/room/${roomId.value}`)
    
    if (response.ok) {
      const data = await response.json()
      messages.value = Array.isArray(data) ? data : []
      
      // 1人ルームかどうかを判定（自分以外のメッセージがあるかどうか）
      const otherMessages = messages.value.filter(msg => msg.original_sender_id !== user.value?.firebase_uid)
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
    const response = await fetch(`${API_BASE}/api/rooms/${roomId.value}`)
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
  
  if (diff <= 0) {
    timeLeft.value = '00:00:00'
    if (timerInterval) {
      clearInterval(timerInterval)
    }
    refreshUserData()
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const cleanMessageText = (text: string) => {
  return text.replace(/\[AI処理済み\]\s*/, '')
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('ja-JP', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

onUnmounted(() => {
  if (timerInterval) {
    clearInterval(timerInterval)
  }
  if (websocket) {
    websocket.close()
  }
})
</script>

<style scoped>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.login-screen h1 {
  font-size: 2.5rem;
  margin-bottom: 2rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.login-screen button {
  padding: 15px 30px;
  font-size: 1.2rem;
  background: rgba(255,255,255,0.2);
  color: white;
  border: 2px solid white;
  border-radius: 50px;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.login-screen button:hover {
  background: rgba(255,255,255,0.3);
  transform: translateY(-2px);
}

.chat-screen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

.user-id {
  background: #4a90e2;
  color: white;
  padding: 10px;
  font-size: 0.9rem;
  text-align: left;
}

.no-room-screen {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
}

.no-room-message {
  text-align: center;
  color: #2d3436;
}

.no-room-message h2 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.reset-timer {
  font-size: 1.2rem;
  font-weight: bold;
}

.header {
  background: #2c3e50;
  color: white;
  padding: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h2 {
  margin: 0;
  font-size: 1.2rem;
}

.timer {
  font-family: 'Courier New', monospace;
  font-size: 1.1rem;
  font-weight: bold;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #ecf0f1;
}

.no-messages {
  text-align: center;
  color: #7f8c8d;
  font-style: italic;
  margin-top: 50px;
}

.message-wrapper {
  margin-bottom: 15px;
  display: flex;
}

.message-wrapper.own-message {
  justify-content: flex-end;
}

.message-wrapper.other-message {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 18px;
  position: relative;
  word-wrap: break-word;
}

.own-message .message-bubble {
  background: #4a90e2;
  color: white;
}

.other-message .message-bubble {
  background: white;
  color: #2c3e50;
  border: 1px solid #ddd;
}

.message-bubble.processing {
  background: #95a5a6;
  color: white;
}

.message-content {
  margin-bottom: 5px;
  line-height: 1.4;
}

.message-time {
  font-size: 0.75rem;
  opacity: 0.7;
  text-align: right;
}

.processing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dot-animation {
  display: flex;
  gap: 2px;
}

.dot-animation span {
  animation: dot-blink 1.4s infinite both;
}

.dot-animation span:nth-child(2) {
  animation-delay: 0.2s;
}

.dot-animation span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dot-blink {
  0%, 80%, 100% {
    opacity: 0;
  }
  40% {
    opacity: 1;
  }
}

.input-area {
  background: white;
  padding: 15px;
  border-top: 1px solid #ddd;
  display: flex;
  gap: 10px;
}

.input-area textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 20px;
  resize: none;
  font-family: inherit;
  font-size: 14px;
  outline: none;
  max-height: 100px;
}

.input-area textarea:focus {
  border-color: #4a90e2;
}

.input-area button {
  padding: 12px 24px;
  background: #4a90e2;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s ease;
}

.input-area button:hover:not(:disabled) {
  background: #357abd;
}

.input-area button:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

/* スクロールバーのスタイリング */
.messages::-webkit-scrollbar {
  width: 6px;
}

.messages::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.messages::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.messages::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>