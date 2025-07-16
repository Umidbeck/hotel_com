type Lang = 'uz' | 'en' | 'ru';

export const translations: Record<Lang, {
  hotel: string;
  connecting: string;
  online: string;
  placeholder: string;
}> = {
  uz: {
    hotel: "Mehmonxona",
    connecting: "🕗 Ulanmoqda...",
    online: "🟢 Onlayn",
    placeholder: "Xabar yozing...",
  },
  en: {
    hotel: "Hotel",
    connecting: "🕗 Connecting...",
    online: "🟢 Online",
    placeholder: "Type a message...",
  },
  ru: {
    hotel: "Гостиница",
    connecting: "🕗 Подключение...",
    online: "🟢 Онлайн",
    placeholder: "Напишите сообщение...",
  },
};

export function getTranslation(): {
  hotel: string;
  connecting: string;
  online: string;
  placeholder: string;
} {
  const lang = localStorage.getItem("chat_language");

  // ✅ Faqat ruxsat etilgan tillarni tekshiramiz
  if (lang === 'uz' || lang === 'en' || lang === 'ru') {
    return translations[lang];
  }

  // ❗️ Noto‘g‘ri yoki yo‘q qiymat bo‘lsa, `uz` qaytadi
  return translations["uz"];
}
