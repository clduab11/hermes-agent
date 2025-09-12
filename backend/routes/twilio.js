import { Router } from 'express';
import Twilio from 'twilio';

export default function getTwilioRouter(io) {
  const router = Router();

  router.post('/inbound', (req, res) => {
    const twiml = new Twilio.twiml.VoiceResponse();
    twiml.say('Smith and Associates Law Firm demo. Press 1 for intake.');
    res.type('text/xml');
    res.send(twiml.toString());
  });

  router.post('/voice-stream', (req, res) => {
    // placeholder for media stream handling
    res.sendStatus(200);
  });

  router.post('/call-log', (req, res) => {
    const log = req.body;
    io.emit('crm-event', `Call logged: ${JSON.stringify(log)}`);
    res.sendStatus(200);
  });

  return router;
}
