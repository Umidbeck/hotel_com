// chat/static/chat/room.js
const roomNumber = document.getElementById('room-data').dataset.roomNumber;
const chatSocket = new WebSocket(
    `wss://${window.location.host}/ws/chat/${roomNumber}/`
);

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    const chat = document.getElementById('chat');

    const messageDiv = document.createElement('div');
    messageDiv.classList.add(data.sender === 'client' ? 'client-msg' : 'staff-msg');
    messageDiv.innerText = data.message;

    chat.appendChild(messageDiv);
    chat.scrollTop = chat.scrollHeight;
};

document.getElementById('message-input').onkeyup = function(e) {
    if (e.keyCode === 13) {  // Enter tugmasi
        const messageInput = e.target;
        chatSocket.send(JSON.stringify({
            'message': messageInput.value
        }));
        messageInput.value = '';
    }
};

chatSocket.onerror = function(e) {
    console.error('WebSocket error:', e);
    document.getElementById('chat').innerHTML += '<p style="color:red">Ulanishda xato!</p>';
};