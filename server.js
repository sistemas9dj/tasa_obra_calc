const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const app = express();

app.use(express.json());
app.use(express.static('public')); // Servirá el index.html automáticamente

const db = new sqlite3.Database('./obras.db');

// Crea la tabla si no existe
db.serialize(() => {
    db.run("CREATE TABLE IF NOT EXISTS configuracion (id INTEGER PRIMARY KEY, arancel REAL, modulo REAL)");
});

// Ruta para obtener valores
app.get('/config', (req, res) => {
    db.get("SELECT arancel, modulo FROM configuracion WHERE id = 1", (err, row) => {
        res.json(row || { arancel: 1320000, modulo: 1000 });
    });
});

// Ruta para guardar valores (Admin)
app.post('/config', (req, res) => {
    const { arancel, modulo } = req.body;
    db.run("INSERT OR REPLACE INTO configuracion (id, arancel, modulo) VALUES (1, ?, ?)", [arancel, modulo], (err) => {
        if (err) res.status(500).send(err);
        else res.json({ status: "Valores actualizados" });
    });
});

const PORT = 3000;
app.listen(PORT, () => {
    console.log(`Servidor de Intranet corriendo en http://localhost:${PORT}`);
});