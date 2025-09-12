export async function createMatter(data) {
  return { id: 'matter-1', ...data };
}

export async function syncContact(data) {
  return { id: 'contact-1', ...data };
}

export async function createTimeEntry(data) {
  return { id: 'time-1', ...data };
}

export async function logActivity(data) {
  return { id: 'activity-1', ...data };
}
