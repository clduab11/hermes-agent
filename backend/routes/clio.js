import { Router } from 'express';
import { createMatter, syncContact, createTimeEntry, logActivity } from '../services/clioService.js';

const router = Router();

router.post('/create-matter', async (req, res) => {
  const matter = await createMatter(req.body);
  res.json(matter);
});

router.post('/sync-contact', async (req, res) => {
  const contact = await syncContact(req.body);
  res.json(contact);
});

router.post('/time-entry', async (req, res) => {
  const entry = await createTimeEntry(req.body);
  res.json(entry);
});

router.post('/log-activity', async (req, res) => {
  const activity = await logActivity(req.body);
  res.json(activity);
});

export default router;
