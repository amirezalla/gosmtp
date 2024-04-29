const { SMTPServer } = require('smtp-server');
const { simpleParser } = require('mailparser');
const axios = require('axios');
const mysql = require('mysql');
const os = require('os');
const tls = require('tls');
const fs = require('fs');


// Create database connection
const db = mysql.createConnection({
    host: '34.77.161.76',
    user: 'root',
    password: 'Amir208079@',
    database: 'sendgrid'
});

db.connect(err => {
    if (err) throw err;
    console.log('Connected to database.');
});

// SMTP server options
const serverOptions = {
    key: fs.readFileSync('sendgrid.icoa.it-key.pem'),  // Path to your private key
    cert: fs.readFileSync('sendgrid.icoa.it.pem'),  // Path to your certificate
    // Not using secure (TLS) communication
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


            callback(null, 'Message processed')
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
    }
};


function getServerIPAddress() {
    const interfaces = os.networkInterfaces();
    for (let iface of Object.values(interfaces)) {
        for (let alias of iface) {
            if (alias.family === 'IPv4' && !alias.internal) {
                return alias.address;
            }
        }
    }
    return 'localhost'; // Return localhost if no external IP is found
}

const server = new SMTPServer(serverOptions);

server.listen(1025, () => {  // Standard port for SMTPS
    console.log('Secure SMTP server running on port 465');
});



function authenticateUser(username, password, callback) {
    // Simulate database check or real check
    console.log(username, password)
    db.query('SELECT * FROM `smtp` WHERE `username` = ? and `password`= ?', [username, password], (err, results) => {
        if (err) {
            return callback(err, false);
        }
        if (results.length > 0) {
            // increment
            db.query('UPDATE `smtp` SET `usage` = `usage` + 1 WHERE `username` = ?', [username])
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
