const ws = new WebSocket('ws://localhost:8000/ws');

const indicator = document.getElementById('language-indicator');
const select = document.getElementById('language-select');
const overrideBtn = document.getElementById('manual-override');

let autoDetect = false;

ws.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'language_changed') {
    indicator.textContent = data.language;
    autoDetect = data.auto_detect === true;
    select.disabled = autoDetect;
    overrideBtn.style.display = autoDetect ? 'inline-block' : 'none';
  }
});

select.addEventListener('change', () => {
  ws.send(JSON.stringify({ type: 'set_language', language: select.value }));
});

overrideBtn.addEventListener('click', () => {
  autoDetect = false;
  select.disabled = false;
  overrideBtn.style.display = 'none';
  ws.send(JSON.stringify({ type: 'set_language', language: select.value }));
});
