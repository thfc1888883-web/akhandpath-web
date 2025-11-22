import React, { useEffect, useRef, useState } from 'react';


export default function LiveListener() {
const [wsReady, setWsReady] = useState(false);
const wsRef = useRef(null);
const mediaRef = useRef(null);
const recorderRef = useRef(null);
const [lastMatch, setLastMatch] = useState(null);
const [status, setStatus] = useState('idle');


const BACKEND_URL = 'YOUR_RENDER_BACKEND_URL'; // e.g., https://my-akhandpath-backend.onrender.com


useEffect(() => {
const ws = new WebSocket(`${BACKEND_URL.replace(/^http/, 'ws')}/ws/akhand`);
ws.binaryType = 'arraybuffer';
ws.onopen = () => setWsReady(true);
ws.onclose = () => setWsReady(false);
ws.onmessage = (evt) => {
try {
const obj = JSON.parse(evt.data);
if (obj.match) setLastMatch(obj.match);
} catch (err) {
console.error('WS message parse error', err);
}
};
wsRef.current = ws;


return () => {
ws.close();
};
}, []);


async function startMic() {
try {
setStatus('requesting');
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
mediaRef.current = stream;


const mediaRecorder = new MediaRecorder(stream);
recorderRef.current = mediaRecorder;


mediaRecorder.ondataavailable = (e) => {
e.data.arrayBuffer().then((buf) => {
if (wsRef.current && wsRef.current.readyState === 1) {
wsRef.current.send(buf);
}
});
};


mediaRecorder.start(2500); // send every 2.5s
setStatus('listening');
} catch (err) {
console.error('Error starting mic', err);
setStatus('idle');
}
}


function stopMic() {
if (recorderRef.current && recorderRef.current.state !== 'inactive') recorderRef.current.stop();
if (mediaRef.current) {
mediaRef.current.getTracks().forEach((t) => t.stop());
mediaRef.current = null;
}
setStatus('idle');
}


async function uploadFile(e) {
const f = e.target.files[0];
if (!f) return;


const fd = new FormData();
fd.append('file', f);
}