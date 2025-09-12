import { Router } from 'express';
import { createMatter, syncContact, createTimeEntry, logActivity } from '../services/clioService.js';

const router = Router();

router.post('/create-matter', async (req, res, next) => {
  try {
    const matter = await createMatter(req.body);
    res.json(matter);
  } catch (error) {
    next(error);
  }
});

router.post('/sync-contact', async (req, res, next) => {
  try {
    const contact = await syncContact(req.body);
    res.json(contact);
  } catch (error) {
    next(error);
  }
});

router.post('/time-entry', async (req, res, next) => {
  try {
    const entry = await createTimeEntry(req.body);
    res.json(entry);
  } catch (error) {
    next(error);
  }
});

router.post('/log-activity', async (req, res, next) => {
  try {
    const activity = await logActivity(req.body);
    res.json(activity);
  } catch (error) {
    next(error);
  }
});

export default router;
