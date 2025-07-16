import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND || 'http://localhost:8000';

const QRRedirect: React.FC = () => {
  const { qr_code } = useParams<{ qr_code: string }>();
  const navigate = useNavigate();

  useEffect(() => {
    const redirect = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/qr/${qr_code}/`);
        if (!res.ok) throw new Error("QR topilmadi");

        const data = await res.json();
        if (data.url) {
          // Agar url local bo‘lsa → navigate
          const url = new URL(data.url, BACKEND_URL);
          navigate(url.pathname + url.search); // React router orqali navigatsiya
        } else {
          alert("❌ QR uchun URL topilmadi");
        }
      } catch (err) {
        alert("❌ Xatolik yuz berdi: " + err);
        console.error(err);
      }
    };
    redirect();
  }, [qr_code, navigate]);

  return <p>🔄 QR dan chat sahifasiga yo‘naltirilmoqda...</p>;
};

export default QRRedirect;

