const tls = require('tls');
const fs = require('fs');
const { SMTPServer } = require('smtp-server');
const { simpleParser } = require('mailparser');
const axios = require('axios');
const mysql = require('mysql');
const os = require('os');



// Create database connection
const db = mysql.createConnection({
    host: '35.198.135.195',
    user: 'amir',
    password: 'Amir208079@',
    database: 'sendgrid'
});

db.connect(err => {
    if (err) throw err;
    console.log('Connected to database.');
});

// SSL/TLS Options
const secureContext = tls.createSecureContext({
    key: fs.readFileSync('sendgrid.icoa.it-key.pem'),
    cert: fs.readFileSync('sendgrid.icoa.it.crt'),
    minVersion: 'TLSv1.2',  // Enforce TLS v1.2 or higher
});

// SMTP server options
const serverOptions = {
    secure: true,  // Use STARTTLS instead of immediate TLS
    authOptional: false,  // Require authentication
    onData(stream, session, callback) {
        simpleParser(stream, async (err, parsed) => {
            if (err) {
                console.error(err);
                return callback(err);
            }

            console.log(`Received email from: ${parsed.from.text}`);
            const { from, to, subject, text: body } = parsed;

            forwardEmail(from.value[0].address, to.value[0].address, subject, body);

            callback(null, 'Message processed');
        });
    },
    onAuth(auth, session, callback) {
        let username = auth.username;
        let password = auth.password;

        authenticateUser(username, password, (err, success) => {
            if (err) {
                console.error('Authentication server error:', err.message);
                return callback(new Error('Internal server error'), false);
            }
            if (success) {
                console.log(`Authenticated and incremented ${username} successfully.`);
                return callback(null, { user: username }); // Authentication success
            } else {
                return callback(new Error('Invalid credentials'), false); // Failed authentication
            }
        });
    },
    onConnect(session, callback) {
        session.servername = 'sendgrid.icoa.it'; // Ensure the servername is set for SNI
        callback();
    },
    secureContext: secureContext
};

const server = new SMTPServer(serverOptions);

server.listen(1025, () => {  // Use a higher port like 1025
    console.log('SMTP server running on port 1025 with SSL');
});

function authenticateUser(username, password, callback) {
    db.query('SELECT * FROM `smtp` WHERE `username` = ? and `password`= ?', [username, password], (err, results) => {
        if (err) {
            return callback(err, false);
        }
        if (results.length > 0) {
            db.query('UPDATE `smtp` SET `usage` = `usage` + 1 WHERE `username` = ?', [username]);
            return callback(null, true);
        } else {
            return callback(null, false);
        }
    });
}

function forwardEmail(from, recipients, subject, body) {
    axios.post('https://sendgrid-hlixxcbawa-uc.a.run.app/api/sendEmail', {
        from: from,
        recipients: recipients,
        subject: subject,
        message: body
    })
        .then(response => console.log('Email forwarded:', response.status, response.data))
        .catch(error => console.error('Failed to forward email:', error));
}

function getServerIPAddress() {
    const interfaces = os.networkInterfaces();
    for (let iface of Object.values(interfaces)) {
        for (let alias of iface) {
            if (alias.family === 'IPv4' && !alias.internal) {
                return alias.address;
            }
        }
    }
    return 'localhost';
}
