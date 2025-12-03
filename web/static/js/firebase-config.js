// Import Firebase App (wajib pakai CDN versi 10.7.1)
import { initializeApp } 
    from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";

// Jika ingin analytics, boleh tapi hanya jalan di HTTPS + real domain
import { getAnalytics } 
    from "https://www.gstatic.com/firebasejs/10.7.1/firebase-analytics.js";

// Firebase configuration
export const firebaseConfig = {
  apiKey: "AIzaSyCl-N1WrpxkypbmjKuOpMzjHnPO14XcnL4",
  authDomain: "sortir-buah-naga.firebaseapp.com",
  databaseURL: "https://sortir-buah-naga-default-rtdb.firebaseio.com",
  projectId: "sortir-buah-naga",
  storageBucket: "sortir-buah-naga.firebasestorage.app",
  messagingSenderId: "90569366366",
  appId: "1:90569366366:web:9bb7a9823b1de84c1acdcf",
  measurementId: "G-LT4ZHZBDZS"
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);

// Analytics (Opsional → Tidak jalan di localhost)
let analytics = null;
try {
    analytics = getAnalytics(app);
} catch (e) {
    console.warn("Analytics tidak aktif (localhost / http).");
}
