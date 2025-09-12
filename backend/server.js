import express from 'express';
import http from 'http';
import { Server } from 'socket.io';
import twilioRoutes from './routes/twilio.js';
import clioRoutes from './routes/clio.js';

const app = express();
app.use(express.json());
app.use('/api/twilio', twilioRoutes);
app.use('/api/clio', clioRoutes);

const server = http.createServer(app);
const io = new Server(server);

io.on('connection', socket => {
  console.log('socket connected');
});

export { io };

const port = process.env.PORT || 3001;
server.listen(port, () => console.log(`Backend listening on ${port}`));
