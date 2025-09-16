import { initializeApp } from 'firebase/app'
import { getAuth, signInAnonymously, type Auth, type UserCredential } from 'firebase/auth'

const firebaseConfig = {
  apiKey: "AIzaSyC-RjBhRs4Knbgr6gDhL0c9R84_EhgYv98",
  authDomain: "ikuchio-cup-2025.firebaseapp.com",
  projectId: "ikuchio-cup-2025",
  storageBucket: "ikuchio-cup-2025.firebasestorage.app",
  messagingSenderId: "88236233617",
  appId: "1:88236233617:web:c7cd68186816bd20530030",
  measurementId: "G-7K9CEJ4YDR"
};

const app = initializeApp(firebaseConfig)
export const auth: Auth = getAuth(app)

export interface FirebaseAuthResult {
  uid: string
  token: string
}

export const signInAnonymous = async (): Promise<FirebaseAuthResult> => {
  try {
    const result: UserCredential = await signInAnonymously(auth)
    const token = await result.user.getIdToken()
    return {
      uid: result.user.uid,
      token: token
    }
  } catch (error) {
    console.error('Firebase anonymous sign-in failed:', error)
    throw error
  }
}