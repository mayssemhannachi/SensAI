const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;
const DATA_DIR = path.join(__dirname, 'data');
const DATA_FILE = path.join(DATA_DIR, 'players.json');

// ---------- Stockage fichier (à remplacer par la base de données plus tard) ----------
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR);
if (!fs.existsSync(DATA_FILE)) fs.writeFileSync(DATA_FILE, JSON.stringify({ players: [] }, null, 2));

const readDB = () => {
  try { return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8')); }
  catch { return { players: [] }; }
};
const writeDB = db => {
  const tmp = DATA_FILE + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(db, null, 2));
  fs.renameSync(tmp, DATA_FILE); // écriture atomique : pas de fichier corrompu
};

// Ajoute ou met à jour une séance pour un joueur
function upsertSession(playerName, session) {
  const db = readDB();
  const name = String(playerName || 'Anonyme').trim().slice(0, 60);
  let player = db.players.find(p => p.name.toLowerCase() === name.toLowerCase());
  if (!player) {
    player = { id: 'p_' + Date.now().toString(36), name, createdAt: new Date().toISOString(), sessions: [] };
    db.players.push(player);
  }
  const i = player.sessions.findIndex(s => s.sessionId === session.sessionId);
  if (i >= 0) player.sessions[i] = session; else player.sessions.push(session);
  writeDB(db);
  return player;
}

// ---------- Serveur HTTP ----------
const send = (res, code, body, type = 'application/json') => {
  res.writeHead(code, { 'Content-Type': type + '; charset=utf-8' });
  res.end(typeof body === 'string' ? body : JSON.stringify(body));
};

http.createServer((req, res) => {
  const url = req.url.split('?')[0];

  if (req.method === 'GET' && (url === '/' || url === '/index.html')) {
    return send(res, 200, fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8'), 'text/html');
  }
  if (req.method === 'GET' && url === '/api/players') {
    return send(res, 200, readDB());
  }
  if (req.method === 'POST' && url === '/api/session') {
    let raw = '';
    req.on('data', c => { raw += c; if (raw.length > 5e6) req.destroy(); });
    req.on('end', () => {
      try {
        const { playerName, session } = JSON.parse(raw);
        if (!session || !session.sessionId) return send(res, 400, { error: 'session invalide' });
        const p = upsertSession(playerName, session);
        console.log(`[${new Date().toLocaleTimeString()}] ${p.name} : séance ${session.sessionId} (${session.summary.repsValidated} reps)`);
        send(res, 200, { ok: true, playerId: p.id });
      } catch (e) { send(res, 400, { error: e.message }); }
    });
    return;
  }
  send(res, 404, { error: 'introuvable' });
}).listen(PORT, () => console.log(`Jeu : http://localhost:${PORT}\nDonnées : ${DATA_FILE}`));