const localtunnel = require('C:/Users/mksin/AppData/Roaming/npm/node_modules/localtunnel');

(async () => {
  const tunnel = await localtunnel({ port: 8000, subdomain: 'campusmate-ai' });
  console.log('Tunnel URL:', tunnel.url);

  tunnel.on('close', () => {
    console.log('Tunnel closed');
    process.exit(0);
  });

  tunnel.on('error', (err) => {
    console.error('Tunnel error:', err);
  });

  // Keep alive
  setInterval(() => {}, 60000);
})();
