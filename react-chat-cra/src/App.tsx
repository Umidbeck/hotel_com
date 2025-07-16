import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import WebChatInterface from './WebChatInterface';
import QRRedirect from './QRRedirect'; // 👈 bu faylni import qiling

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/chat/:roomNumber" element={<WebChatInterface />} />
        <Route path="/qr/:qr_code" element={<QRRedirect />} /> {/* 👈 YANGI */}
        {/* boshqa routelar */}
      </Routes>
    </Router>
  );
}

export default App;