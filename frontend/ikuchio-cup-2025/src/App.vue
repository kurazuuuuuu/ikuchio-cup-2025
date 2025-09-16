<template>
  <div id="app">
    <div class="mouse-noise" :style="{ left: mouseX + 'px', top: mouseY + 'px' }"></div>
    <div v-if="!user" class="login-screen">
      <h1 class="typewriter">24時間でさようなら</h1>
      <button @click="login">Login</button>
    </div>
    
    <div v-else class="chat-screen" :class="{ 'loading-completed': loadingCompleted }">
      <div v-if="!loading" class="top-bar">
        <div class="user-info">
          <div class="user-id">ユーザーID： {{ user.firebase_uid }}</div>
        </div>
        <div class="controls">
          <div class="timer">{{ timeLeft }}</div>
          <button @click="logout" class="logout-btn">EXIT</button>
        </div>
      </div>
      
      <!-- ローディング中 -->
      <div v-if="loading" class="loading-screen">
        <div class="linux-loading">
          <div class="loading-line typewriter-line line1">[ OK ] Get User#{{ user.firebase_uid }}...</div>
          <div class="loading-line typewriter-line line2">[ OK ] Connecting to server...</div>
          <div class="loading-line typewriter-line line3">[ OK ] Initializing user session...</div>
          <div class="loading-line typewriter-line line4 current">[ .. ] Loading chat interface Room#{{ roomId || 'None' }}<span class="cursor">_</span></div>
        </div>
      </div>
      
      <!-- ルームが存在しない場合 -->
      <div v-else-if="!roomId" class="no-room-screen">
        <div class="no-room-message">
          <h2>まだあなたの相手は見つかっていないようですよ...</h2>
          <div class="reset-timer">
            <p>次のペアリングまで: {{ timeLeft }}</p>
          </div>
        </div>
      </div>
      
      <!-- ルームが存在する場合 -->
      <div v-else class="chat-container">
        
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
      </div>
      
      <div v-if="roomId && !loading" class="input-area">
        <textarea 
          v-model="newMessage" 
          @keydown="handleKeydown"
          placeholder="メッセージを入力..."
          :disabled="sending"
        ></textarea>
        <div class="send-button-container">
          <div class="tutorial-text">Cmd+Enter: 送信 | Enter: 改行</div>
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
const loading = ref<boolean>(false)
const loadingCompleted = ref<boolean>(false)
const mouseX = ref<number>(0)
const mouseY = ref<number>(0)

let timerInterval: number | null = null
let websocket: WebSocket | null = null

const login = async () => {
  loading.value = true
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
    
    // 5秒間のローディング演出
    await new Promise(resolve => setTimeout(resolve, 5000))
    
  } catch (error) {
    console.error('Login failed:', error)
    let errorMessage = '不明なエラー'
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      errorMessage = `サーバーに接続できません。${API_BASE}にアクセスできるか確認してください。`
    } else if (error instanceof Error) {
      errorMessage = error.message
    }
    
    alert(`ログインに失敗しました: ${errorMessage}\n\nデバッグ情報:\nFirebase UID: ${firebaseAuth?.uid || 'None'}\nAPI URL: ${API_BASE}`)
  } finally {
    // 走査アニメーションを先に開始
    loadingCompleted.value = true
    
    // 少し待ってからローディングを終了
    setTimeout(() => {
      loading.value = false
    }, 100)
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
  
  // 次の15分区切りの時刻を計算
  const nextReset = new Date(now)
  const currentMinutes = now.getMinutes()
  const nextMinutes = Math.ceil((currentMinutes + 1) / 15) * 15
  
  if (nextMinutes >= 60) {
    nextReset.setHours(now.getHours() + 1, 0, 0, 0)
  } else {
    nextReset.setMinutes(nextMinutes, 0, 0)
  }
  
  const diff = nextReset.getTime() - now.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)
  
  timeLeft.value = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  
  if (diff <= 0) {
    timeLeft.value = '00:00'
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
  if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
    event.preventDefault()
    sendMessage()
  }
}

const logout = () => {
  if (timerInterval) {
    clearInterval(timerInterval)
  }
  if (websocket) {
    websocket.close()
  }
  user.value = null
  roomId.value = ''
  messages.value = []
}

let mouseThrottle = false
const handleMouseMove = (event: MouseEvent) => {
  if (mouseThrottle) return
  mouseThrottle = true
  setTimeout(() => { mouseThrottle = false }, 50)
  mouseX.value = event.clientX
  mouseY.value = event.clientY
}

// マウス移動イベントリスナーを追加
if (typeof window !== 'undefined') {
  window.addEventListener('mousemove', handleMouseMove)
}

onUnmounted(() => {
  if (timerInterval) {
    clearInterval(timerInterval)
  }
  if (websocket) {
    websocket.close()
  }
  if (typeof window !== 'undefined') {
    window.removeEventListener('mousemove', handleMouseMove)
  }
})
</script>

<style scoped>
#app {
  font-family: 'DotGothic16', monospace;
  background: linear-gradient(135deg, #0a0a0a 0%, #0d0f0d 100%);
  color: #00ff00;
  height: 100vh;
  display: flex;
  flex-direction: column;
  text-shadow: 0 0 5px #00ff00;
  position: relative;
  overflow: hidden;
  filter: contrast(1.1) brightness(1.05);
}

#app::after {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(ellipse at center, transparent 50%, rgba(0, 0, 0, 0.3) 100%),
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 1px,
      rgba(0, 255, 0, 0.08) 1px,
      rgba(0, 255, 0, 0.08) 3px
    );
  pointer-events: none;
  z-index: 9999;
  animation: flicker 0.3s infinite linear alternate, scanline 16s linear infinite;
  border-radius: 15px;
  box-shadow: inset 0 0 100px rgba(0, 0, 0, 0.8);
  will-change: opacity, filter;
  transform: translateZ(0);
}

#app .mouse-noise {
  content: '';
  position: fixed;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  pointer-events: none;
  z-index: 10000;
  background: 
    radial-gradient(circle, 
      rgba(255, 255, 255, 0.1) 0%, 
      rgba(0, 255, 0, 0.05) 30%, 
      transparent 70%
    );
  animation: mouseNoise 0.2s infinite linear;
  transform: translate(-50%, -50%) translateZ(0);
  will-change: opacity, filter;
}

@keyframes mouseNoise {
  0% { opacity: 0.8; filter: blur(0.5px); }
  25% { opacity: 0.6; filter: blur(1px); }
  50% { opacity: 0.9; filter: blur(0.3px); }
  75% { opacity: 0.7; filter: blur(0.8px); }
  100% { opacity: 0.8; filter: blur(0.5px); }
}

@keyframes flicker {
  0% { opacity: 0.95; }
  100% { opacity: 1; }
}

@keyframes scanline {
  0% { background-position: 0 0; }
  100% { background-position: 0 100vh; }
}

.chat-screen, .login-screen {
  will-change: transform;
  transform: translateZ(0);
}

#app::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #0a0a0a;
  z-index: 1000;
  animation: scanReveal 2s ease-out forwards;
}

@keyframes scanReveal {
  from {
    clip-path: inset(0 0 0 0);
  }
  to {
    clip-path: inset(100% 0 0 0);
  }
}

.login-screen {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #0a0a0a 0%, #0d0f0d 100%);
  color: #00ff00;
  position: relative;
}

.login-screen::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 255, 0, 0.03) 2px,
    rgba(0, 255, 0, 0.03) 4px
  );
  pointer-events: none;
}

.login-screen h1 {
  font-size: 2rem;
  margin-bottom: 2rem;
  text-shadow: 0 0 10px #00ff00;
  font-weight: 700;
  letter-spacing: 2px;
}

.typewriter {
  font-family: 'DotGothic16', monospace;
  display: inline-block;
  position: relative;
}

.typewriter::after {
  content: '_';
  color: #00ff00;
  animation: blink 1s infinite;
  position: absolute;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.login-screen button {
  padding: 12px 24px;
  font-size: 1rem;
  background: transparent;
  color: #00ff00;
  border: 2px solid #00ff00;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'DotGothic16', monospace;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.login-screen button:hover {
  background: #00ff00;
  color: #0a0a0a;
  box-shadow: 0 0 20px #00ff00;
}

.chat-screen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #0a0a0a 0%, #0d0f0d 100%);
  position: relative;
}

.chat-screen::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 255, 0, 0.03) 2px,
    rgba(0, 255, 0, 0.03) 4px
  );
  pointer-events: none;
  z-index: 1;
}

.chat-screen.loading-completed::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #0a0a0a;
  z-index: 1000;
  animation: scanRevealChat 1s ease-out 0.1s forwards;
  pointer-events: none;
}

@keyframes scanRevealChat {
  from {
    clip-path: inset(0 0 0 0);
  }
  to {
    clip-path: inset(100% 0 0 0);
  }
}

.top-bar {
  background: #001100;
  color: #00ff00;
  padding: 8px 10px;
  border-bottom: 1px solid #00ff00;
  z-index: 2;
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-family: 'DotGothic16', monospace;
}

.user-id, .room-id {
  font-size: 0.8rem;
  text-align: left;
  font-family: 'DotGothic16', monospace;
  line-height: 1.2;
  margin: 0;
  padding: 0;
}

.controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.timer {
  font-family: 'DotGothic16', monospace;
  font-size: 1rem;
  font-weight: 700;
  color: #ffff00;
  text-shadow: 0 0 10px #ffff00;
}

.logout-btn {
  padding: 6px 12px;
  background: transparent;
  color: #ff4444;
  border: 1px solid #ff4444;
  cursor: pointer;
  font-size: 0.7rem;
  font-family: 'DotGothic16', monospace;
  text-transform: uppercase;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  background: #ff4444;
  color: #0a0a0a;
  box-shadow: 0 0 10px #ff4444;
}

.loading-screen {
  flex: 1;
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
  z-index: 2;
  position: relative;
  padding: 40px 20px;
}

.linux-loading {
  font-family: 'DotGothic16', monospace;
  color: #00ff00;
  font-size: 0.9rem;
  line-height: 1.6;
}

.loading-line {
  margin-bottom: 8px;
  overflow: hidden;
  white-space: nowrap;
  width: 0;
}

.loading-line.current {
  color: #ffff00;
  text-shadow: 0 0 5px #ffff00;
}

.line1 {
  animation: typewriter 1.2s steps(15, end) 0s forwards;
}

.line2 {
  animation: typewriter 1.0s steps(12, end) 1.2s forwards;
}

.line3 {
  animation: typewriter 1.1s steps(14, end) 2.2s forwards;
}

.line4 {
  animation: typewriter 1.2s steps(14, end) 3.3s forwards;
}

@keyframes typewriter {
  from {
    width: 0;
    opacity: 0.7;
  }
  to {
    width: 100%;
    opacity: 0.7;
  }
}

.line4 {
  animation: typewriter 0.8s steps(35, end) 2.1s forwards;
}

.line4.current {
  animation: typewriter-current 1.2s steps(14, end) 3.3s forwards;
}

@keyframes typewriter-current {
  from {
    width: 0;
    opacity: 1;
  }
  to {
    width: 100%;
    opacity: 1;
  }
}

.cursor {
  animation: blink 1s infinite;
}

.loading-info {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #004400;
}

.info-line {
  font-size: 0.8rem;
  color: #00aa00;
  margin-bottom: 5px;
  opacity: 0.8;
}

.no-room-screen {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2;
  position: relative;
}

.no-room-message {
  text-align: center;
  color: #00ff00;
  border: 2px solid #00ff00;
  padding: 2rem;
  background: rgba(0, 17, 0, 0.8);
}

.no-room-message h2 {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  text-shadow: 0 0 10px #00ff00;
}

.reset-timer {
  font-size: 1rem;
  font-weight: 700;
  color: #ffff00;
  text-shadow: 0 0 10px #ffff00;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  padding-bottom: 100px;
  background: transparent;
  z-index: 2;
  position: relative;
}

.no-messages {
  text-align: center;
  color: #00aa00;
  font-style: italic;
  margin-top: 50px;
  border: 1px dashed #00aa00;
  padding: 20px;
  background: rgba(0, 17, 0, 0.3);
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
  position: relative;
  word-wrap: break-word;
  border: 1px solid;
  background: rgba(0, 17, 0, 0.8);
}

.own-message .message-bubble {
  border-color: #00ff00;
  color: #00ff00;
}

.other-message .message-bubble {
  border-color: #0088ff;
  color: #0088ff;
  text-shadow: 0 0 5px #0088ff;
}

.message-bubble.processing {
  border-color: #ffaa00;
  color: #ffaa00;
  text-shadow: 0 0 5px #ffaa00;
}

.message-content {
  margin-bottom: 5px;
  line-height: 1.4;
  font-size: 0.9rem;
}

.message-time {
  font-size: 0.7rem;
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
  background: #001100;
  padding: 15px;
  border-top: 1px solid #00ff00;
  display: flex;
  gap: 10px;
  z-index: 2;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
}

.input-area textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #00ff00;
  background: #0a0a0a;
  color: #00ff00;
  resize: none;
  font-family: 'DotGothic16', monospace;
  font-size: 0.9rem;
  outline: none;
  max-height: 100px;
}

.input-area textarea::placeholder {
  color: #006600;
}

.input-area textarea:focus {
  border-color: #00ff00;
  box-shadow: 0 0 10px rgba(0, 255, 0, 0.3);
}

.input-area button {
  padding: 12px 24px;
  background: transparent;
  color: #00ff00;
  border: 1px solid #00ff00;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  font-family: 'DotGothic16', monospace;
  text-transform: uppercase;
}

.input-area button:hover:not(:disabled) {
  background: #00ff00;
  color: #0a0a0a;
  box-shadow: 0 0 15px #00ff00;
}

.input-area button:disabled {
  border-color: #003300;
  color: #003300;
  cursor: not-allowed;
}

.send-button-container {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.tutorial-text {
  font-size: 0.6rem;
  color: #00aa00;
  opacity: 0.9;
  font-family: 'DotGothic16', monospace;
  white-space: nowrap;
  z-index: 10;
  position: relative;
  text-shadow: 0 0 3px #00aa00;
}

.messages::-webkit-scrollbar {
  width: 8px;
}

.messages::-webkit-scrollbar-track {
  background: #001100;
}

.messages::-webkit-scrollbar-thumb {
  background: #00ff00;
  border-radius: 4px;
}

.messages::-webkit-scrollbar-thumb:hover {
  background: #00aa00;
}

/* レスポンシブ対応 */
@media (max-width: 768px) {
  .login-screen h1 {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
  }
  
  .typewriter {
    animation: typing 3s steps(11, end), blink-caret 0.75s step-end infinite;
  }
  
  .login-screen button {
    padding: 10px 20px;
    font-size: 0.9rem;
  }
  
  .user-id {
    padding: 8px;
    font-size: 0.7rem;
  }
  
  .header {
    padding: 10px;
    flex-direction: column;
    gap: 5px;
    text-align: center;
  }
  
  .header h2 {
    font-size: 0.9rem;
  }
  
  .timer {
    font-size: 0.9rem;
  }
  
  .no-room-message {
    padding: 1rem;
    margin: 0 10px;
  }
  
  .no-room-message h2 {
    font-size: 1rem;
  }
  
  .messages {
    padding: 10px;
  }
  
  .message-bubble {
    max-width: 85%;
    padding: 10px 12px;
    font-size: 0.8rem;
  }
  
  .message-content {
    font-size: 0.8rem;
  }
  
  .input-area {
    padding: 10px;
    flex-direction: column;
    gap: 8px;
  }
  
  .input-area textarea {
    font-size: 0.8rem;
    padding: 10px;
  }
  
  .input-area button {
    padding: 10px 20px;
    font-size: 0.8rem;
    align-self: flex-end;
    width: auto;
  }
}

@media (max-width: 480px) {
  .login-screen h1 {
    font-size: 1.2rem;
  }
  
  .typewriter {
    animation: typing 3s steps(11, end), blink-caret 0.75s step-end infinite;
  }
  
  .message-bubble {
    max-width: 90%;
    padding: 8px 10px;
  }
  
  .no-room-message {
    padding: 0.8rem;
  }
  
  .no-room-message h2 {
    font-size: 0.9rem;
  }
}
</style>